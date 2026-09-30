from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import (
    ArabicSense,
    DictionaryEntry,
    ParallelSegment,
    SenseMapping,
    TranslationCandidate,
    TranslationRequest,
)
from app.models.enums import InputType, PartOfSpeech, RecordStatus, TranslationStatus
from app.schemas.public import TranslateResponse
from app.services.embedding import embed_text
from app.services.retrieval import RetrievalService
from app.services.syntax import (
    _PREPOSITIONS_BY_DIALECT,
    compose_coptic_sentence,
    compose_coptic_sentence_with_notes,
)
from app.services.text import (
    arabic_lookup_variants,
    is_single_word,
    normalize_arabic,
    normalize_coptic,
    tokenize_arabic,
)


class TranslationService:
    LOW_CONFIDENCE_THRESHOLD = 0.6

    def __init__(self, db: Session) -> None:
        self.db = db

    normalize_arabic = staticmethod(normalize_arabic)
    embed_text = staticmethod(embed_text)

    def translate(
        self, text: str, user_id: int | None, target_dialect_id: int | None = None, context: str | None = None
    ) -> TranslateResponse:
        if is_single_word(text):
            result = self.translate_word(text, target_dialect_id)
            entries = result["entries"]
            unique_translations = list(dict.fromkeys(e["coptic_word"] for e in entries if e.get("coptic_word")))
            return TranslateResponse(
                input_type=InputType.word,
                status=RecordStatus.approved if entries else RecordStatus.draft,
                translation=entries[0]["coptic_word"] if entries else None,
                translations=unique_translations,
                confidence=entries[0]["confidence"] if entries else 0.0,
                dictionary_entry_ids=[entry["dictionary_entry_id"] for entry in entries],
                word_results=entries,
                needs_human_review=not entries,
                human_review_reason=None if entries else "unknown_word",
                references=[entry["reference"] for entry in entries],
                evidence={"word_results": entries},
            )
        result = self.translate_sentence(text, user_id, target_dialect_id, context)
        candidate = result["candidate_translation"]
        return TranslateResponse(
            input_type=InputType.sentence,
            status=RecordStatus(result["review_status"]),
            translation=candidate,
            translations=[candidate] if candidate else [],
            confidence=result["confidence_score"],
            dictionary_entry_ids=result["used_dictionary_entries"],
            translation_request_id=result.get("translation_request_id"),
            translation_candidate_id=result.get("translation_candidate_id"),
            candidate_translation=result["candidate_translation"],
            literal_breakdown=result["literal_breakdown"],
            used_dictionary_entries=result["used_dictionary_entries"],
            similar_examples=result["similar_examples"],
            meaning_examples=result["meaning_examples"],
            grammar_notes=result["grammar_notes"],
            unknown_words=result["unknown_words"],
            needs_human_review=result["needs_human_review"],
            human_review_reason=result["human_review_reason"],
            references=result["references"],
            evidence={
                "literal_breakdown": result["literal_breakdown"],
                "similar_examples": result["similar_examples"],
                "meaning_examples": result["meaning_examples"],
                "grammar_notes": result["grammar_notes"],
                "references": result["references"],
                "unknown_words": result["unknown_words"],
                "needs_human_review": result["needs_human_review"],
                "human_review_reason": result["human_review_reason"],
            },
        )

    def translate_word(self, text: str, dialect_id: int | None = None) -> dict:
        normalized = normalize_arabic(text)
        entries = [
            self._word_entry_payload(entry, sense, mapping)
            for entry, sense, mapping in self._lookup_word(normalized, dialect_id)
        ]
        return {
            "input_type": "word",
            "normalized_text": normalized,
            "entries": entries,
            "review_status": "approved" if entries else "draft",
            "needs_human_review": not entries,
        }

    def translate_sentence(
        self,
        text: str,
        user_id: int | None,
        target_dialect_id: int | None = None,
        context: str | None = None,
    ) -> dict:
        normalized = normalize_arabic(text)
        approved = self._find_approved_parallel_sentence(normalized, target_dialect_id)
        if approved is not None:
            reference = {"table": "parallel_segments", "id": approved.id}
            return {
                "input_type": "sentence",
                "normalized_text": normalized,
                "candidate_translation": approved.coptic_text,
                "literal_breakdown": [],
                "used_dictionary_entries": [],
                "similar_examples": [
                    {
                        "id": approved.id,
                        "arabic_text": approved.arabic_text,
                        "coptic_text": approved.coptic_text,
                        "source_id": approved.source_id,
                        "dialect_id": approved.dialect_id,
                        "similarity_score": 1.0,
                        "match_type": "approved",
                        "reference": reference,
                    }
                ],
                "meaning_examples": [],
                "grammar_notes": [],
                "references": [reference],
                "confidence_score": 1.0,
                "review_status": "approved",
                "needs_human_review": False,
                "human_review_reason": None,
                "unknown_words": [],
                "translation_request_id": None,
                "translation_candidate_id": None,
            }

        tokens = tokenize_arabic(text)
        breakdown = []
        used_entries: list[DictionaryEntry] = []
        mapping_confidences: list[float] = []
        unknown_words: list[str] = []

        for token in tokens:
            lookup = self._lookup_word(token, target_dialect_id)
            if not lookup:
                breakdown.append(
                    {
                        "arabic": token,
                        "coptic": None,
                        "status": "unknown",
                        "dictionary_entry_id": None,
                    }
                )
                unknown_words.append(token)
                continue
            entry, _sense, mapping = lookup[0]
            used_entries.append(entry)
            mapping_confidences.append(mapping.confidence)
            breakdown.append(
                {
                    "arabic": token,
                    "coptic": entry.coptic_text,
                    "status": "known",
                    "dictionary_entry_id": entry.id,
                }
            )

        retrieval = RetrievalService(self.db)
        rag = retrieval.references_for_sentence(normalized, dialect_id=target_dialect_id)
        similar_examples = rag["similar_examples"]
        meaning_examples = rag["meaning_examples"]
        grammar_notes = rag["grammar_notes"]
        references = rag["references"]

        syntax_res = compose_coptic_sentence_with_notes(breakdown, dialect_id=target_dialect_id or 1)
        all_grammar_notes = grammar_notes + syntax_res.grammar_notes

        confidence = self._pipeline_confidence(
            tokens=tokens,
            mapping_confidences=mapping_confidences,
            examples=similar_examples,
            grammar_notes=all_grammar_notes,
            meaning_examples=meaning_examples,
            unknown_words=unknown_words,
        )
        needs_review = bool(unknown_words) or confidence < self.LOW_CONFIDENCE_THRESHOLD
        review_reason = (
            "unknown_words"
            if unknown_words
            else "low_confidence"
            if confidence < self.LOW_CONFIDENCE_THRESHOLD
            else None
        )
        candidate_text = self._compose_candidate(breakdown, confidence, unknown_words, target_dialect_id)
        if unknown_words or (candidate_text is not None and not candidate_text.strip()):
            candidate_text = None

        request = TranslationRequest(
            user_id=user_id,
            target_dialect_id=target_dialect_id,
            input_text=text,
            normalized_input_text=normalized,
            context=context,
            status=TranslationStatus.completed,
        )
        self.db.add(request)
        self.db.flush()
        candidate = TranslationCandidate(
            translation_request_id=request.id,
            candidate_text=candidate_text if candidate_text else None,
            normalized_candidate_text=normalize_coptic(candidate_text) if candidate_text else None,
            dialect_id=target_dialect_id,
            generated_by="rule_based",
            rank=1,
            confidence=confidence,
            evidence={
                "literal_breakdown": breakdown,
                "dictionary_entry_ids": [entry.id for entry in used_entries],
                "parallel_segment_ids": [item["id"] for item in similar_examples],
                "arabic_sense_ids": [item["id"] for item in meaning_examples],
                "grammar_rule_ids": [item["id"] for item in grammar_notes if "id" in item],
                "syntax_grammar_notes": syntax_res.grammar_notes,
                "unknown_words": unknown_words,
                "human_review_reason": review_reason,
                "references": references,
            },
            review_status=RecordStatus.draft,
        )
        self.db.add(candidate)
        self.db.commit()
        self.db.refresh(candidate)

        return {
            "input_type": "sentence",
            "normalized_text": normalized,
            "candidate_translation": candidate_text,
            "literal_breakdown": breakdown,
            "used_dictionary_entries": [entry.id for entry in used_entries],
            "similar_examples": similar_examples,
            "meaning_examples": meaning_examples,
            "grammar_notes": all_grammar_notes,
            "references": references,
            "confidence_score": confidence,
            "review_status": "draft",
            "needs_human_review": needs_review,
            "human_review_reason": review_reason,
            "unknown_words": unknown_words,
            "translation_request_id": request.id,
            "translation_candidate_id": candidate.id,
        }

    def _lookup_word(
        self, normalized: str, dialect_id: int | None
    ) -> list[tuple[DictionaryEntry, ArabicSense, SenseMapping]]:
        for lookup_variant in arabic_lookup_variants(normalized):
            results = self._lookup_word_exact(lookup_variant, dialect_id)
            if results:
                return results

        # Fallback for recognized grammatical prepositions
        d_key = "bohairic" if dialect_id in (None, 1) else ("sahidic" if dialect_id == 2 else "fayyumic")
        prep_table = _PREPOSITIONS_BY_DIALECT.get(d_key, _PREPOSITIONS_BY_DIALECT["bohairic"])
        clean_norm = normalized.strip()
        base_prep = clean_norm[1:] if (clean_norm.startswith("و") and len(clean_norm) > 2 and clean_norm[1:] in prep_table) else clean_norm
        if base_prep in prep_table:
            c_text = prep_table[base_prep]
            dummy_entry = DictionaryEntry(
                coptic_text=c_text,
                normalized_coptic_text=c_text.lower(),
                dialect_id=dialect_id or 1,
                part_of_speech=PartOfSpeech.preposition,
                review_status=RecordStatus.approved,
            )
            dummy_sense = ArabicSense(
                arabic_lemma=base_prep,
                normalized_arabic_lemma=base_prep,
                definition_ar=f"حرف جر قبطي: {c_text}",
                part_of_speech=PartOfSpeech.preposition,
                review_status=RecordStatus.approved,
            )
            dummy_mapping = SenseMapping(confidence=1.0, is_primary=True, review_status=RecordStatus.approved)
            return [(dummy_entry, dummy_sense, dummy_mapping)]

        return []

    def _lookup_word_exact(
        self, normalized: str, dialect_id: int | None
    ) -> list[tuple[DictionaryEntry, ArabicSense, SenseMapping]]:
        statement = (
            self.db.query(DictionaryEntry, ArabicSense, SenseMapping)
            .join(SenseMapping, SenseMapping.dictionary_entry_id == DictionaryEntry.id)
            .join(ArabicSense, ArabicSense.id == SenseMapping.arabic_sense_id)
            .filter(
                ArabicSense.normalized_arabic_lemma == normalized,
                ArabicSense.review_status == RecordStatus.approved,
                DictionaryEntry.review_status == RecordStatus.approved,
                SenseMapping.review_status == RecordStatus.approved,
            )
        )
        if dialect_id is not None:
            statement = statement.order_by(
                (DictionaryEntry.dialect_id == dialect_id).desc(),
                SenseMapping.confidence.desc(),
                SenseMapping.is_primary.desc(),
                DictionaryEntry.id.desc(),
            )
        else:
            statement = statement.order_by(
                SenseMapping.confidence.desc(),
                SenseMapping.is_primary.desc(),
                DictionaryEntry.id.desc(),
            )
        return statement.all()

    def _word_entry_payload(
        self, entry: DictionaryEntry, sense: ArabicSense, mapping: SenseMapping
    ) -> dict:
        return {
            "dictionary_entry_id": entry.id,
            "coptic_word": entry.coptic_text,
            "dialect": entry.dialect.name if entry.dialect else None,
            "dialect_id": entry.dialect_id,
            "part_of_speech": entry.part_of_speech.value,
            "meaning": sense.definition_ar,
            "source": entry.source.title if entry.source else None,
            "source_id": entry.source_id,
            "confidence": round(float(mapping.confidence), 4),
            "reference": {"table": "dictionary_entries", "id": entry.id},
            "examples": [
                value
                for value in [
                    entry.example_sentence,
                    sense.example_ar,
                ]
                if value
            ],
        }

    def _find_approved_parallel_sentence(
        self, normalized: str, dialect_id: int | None
    ) -> ParallelSegment | None:
        statement = self.db.query(ParallelSegment).filter(
            ParallelSegment.normalized_arabic_text == normalized,
            ParallelSegment.review_status == RecordStatus.approved,
        )
        if dialect_id is not None:
            statement = statement.order_by((ParallelSegment.dialect_id == dialect_id).desc(), ParallelSegment.id.asc())
        return statement.first()

    def _compose_candidate(
        self, breakdown: list[dict], confidence: float, unknown_words: list[str], target_dialect_id: int | None = 1
    ) -> str | None:
        if unknown_words or confidence < self.LOW_CONFIDENCE_THRESHOLD:
            return None
        composed = compose_coptic_sentence(breakdown, dialect_id=target_dialect_id or 1)
        if not composed or not composed.strip():
            return None
        return composed.strip()

    def _pipeline_confidence(
        self,
        tokens: list[str],
        mapping_confidences: list[float],
        examples: list[dict],
        grammar_notes: list[dict],
        meaning_examples: list[dict],
        unknown_words: list[str],
    ) -> float:
        if not tokens:
            return 0.0
        coverage = (len(tokens) - len(unknown_words)) / len(tokens)
        lexical = (
            sum(mapping_confidences) / len(mapping_confidences)
            if mapping_confidences
            else 0.0
        )
        example_score = max([item["similarity_score"] for item in examples], default=0.0)
        meaning_score = max([item["similarity_score"] for item in meaning_examples], default=0.0)
        rule_bonus = 0.05 if any("id" in item for item in grammar_notes) else 0.0
        evidence_penalty = 0.10 if not examples else 0.0
        unknown_penalty = 0.30 if unknown_words else 0.0
        confidence = (
            coverage * 0.5
            + lexical * 0.35
            + example_score * 0.10
            + meaning_score * 0.05
            + rule_bonus
        )
        return round(max(0.0, min(0.95, confidence - unknown_penalty - evidence_penalty)), 4)
