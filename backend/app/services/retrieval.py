from __future__ import annotations

from difflib import SequenceMatcher
from typing import Any

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models import ArabicSense, GrammarRule, ParallelSegment, Source
from app.models.enums import RecordStatus, SourceType
from app.services.embedding import cosine_similarity, embed_text
from app.services.text import normalize_arabic, tokenize_arabic


_SCHOLARLY_KEYWORDS = (
    "crum",
    "ccl",
    "labib",
    "scriptorium",
    "liddell",
    "scott",
    "bailly",
    "moawad",
    "معجم",
    "قاموس",
    "مخطوط",
)


def compute_trigram_overlap(s1: str, s2: str) -> float:
    """Character trigram Dice similarity coefficient for Arabic morphology capture."""
    if not s1 or not s2:
        return 0.0
    if len(s1) < 3 or len(s2) < 3:
        return SequenceMatcher(None, s1, s2).ratio()
    tri1 = {s1[i : i + 3] for i in range(len(s1) - 2)}
    tri2 = {s2[i : i + 3] for i in range(len(s2) - 2)}
    if not tri1 or not tri2:
        return 0.0
    return round(2.0 * len(tri1 & tri2) / (len(tri1) + len(tri2)), 4)


def get_source_quality_score(source: Source | None) -> float:
    """Calculates authority weighting based on scholarly standard and source type."""
    if source is None:
        return 0.50
    title_lower = (source.title or "").lower()
    notes_lower = (source.notes or "").lower()
    if any(k in title_lower or k in notes_lower for k in _SCHOLARLY_KEYWORDS):
        return 1.0
    stype = getattr(source, "type", None)
    if stype in {SourceType.lexicon, SourceType.manuscript}:
        return 0.95
    if stype == SourceType.dictionary:
        return 0.90
    if stype == SourceType.book:
        return 0.80
    if stype == SourceType.website:
        return 0.70
    return 0.60


def get_review_status_score(status: RecordStatus | None) -> float:
    """Weights verified peer-reviewed content over drafts or unreviewed records."""
    if status == RecordStatus.approved:
        return 1.0
    if status == RecordStatus.draft:
        return 0.60
    return 0.0


def compute_hybrid_ranking(
    text_ratio: float,
    token_overlap: float,
    trigram_overlap: float,
    vector_score: float,
    source_quality: float,
    review_status: float,
) -> tuple[float, dict[str, float]]:
    """Hybrid ranking: trigram + vector + source quality + review status.

    Weights:
    - 0.35 Text/Trigram Overlap
    - 0.35 Multilingual Vector Semantic Similarity
    - 0.15 Source Authority & Scholarly Quality
    - 0.15 Peer Review & Curation Status
    """
    text_combined = max(text_ratio, token_overlap, trigram_overlap)

    # Exact match preserves perfect score
    if text_ratio >= 0.999 and vector_score >= 0.999:
        final_score = 1.0
    else:
        raw = (
            (0.35 * text_combined)
            + (0.35 * vector_score)
            + (0.15 * source_quality)
            + (0.15 * review_status)
        )
        final_score = round(min(max(raw, 0.0), 1.0), 4)

    breakdown = {
        "text_overlap": round(text_combined, 4),
        "trigram_overlap": round(trigram_overlap, 4),
        "vector_similarity": round(vector_score, 4),
        "source_quality": round(source_quality, 4),
        "review_status": round(review_status, 4),
    }
    return final_score, breakdown


class RetrievalService:
    normalize_arabic = staticmethod(normalize_arabic)
    embed_text = staticmethod(embed_text)

    def __init__(self, db: Session) -> None:
        self.db = db

    def similar_segments(
        self, q: str, dialect_id: int | None = None, limit: int = 5
    ) -> list[dict]:
        normalized = normalize_arabic(q)
        query_vector = embed_text(normalized)
        statement = self.db.query(ParallelSegment).filter(
            ParallelSegment.review_status == RecordStatus.approved,
            ParallelSegment.coptic_text.isnot(None),
        )
        if dialect_id is not None:
            statement = statement.filter(ParallelSegment.dialect_id == dialect_id)

        if self._is_postgres():
            distance = ParallelSegment.arabic_embedding.cosine_distance(query_vector)
            vector_rows = (
                statement.filter(ParallelSegment.arabic_embedding.isnot(None))
                .order_by(distance)
                .limit(limit * 2)
                .all()
            )
            full_text_rows = self._postgres_full_text_segments(
                statement, normalized, limit * 2
            )
            rows = self._merge_rows(vector_rows, full_text_rows)
        else:
            tokens = [t for t in tokenize_arabic(normalized) if len(t) > 1]
            if tokens:
                token_filters = [
                    ParallelSegment.normalized_arabic_text.like(f"%{t}%")
                    for t in tokens
                ]
                matched_rows = statement.filter(or_(*token_filters)).limit(120).all()
                if len(matched_rows) < 20:
                    fallback_rows = statement.limit(100).all()
                    rows = self._merge_rows(matched_rows, fallback_rows)
                else:
                    rows = matched_rows
            else:
                rows = statement.limit(100).all()

        ranked = [
            self._segment_result(segment, normalized, query_vector)
            for segment in rows
        ]
        ranked.sort(key=lambda item: item["similarity_score"], reverse=True)
        return ranked[:limit]

    def examples_for_sentence(
        self, q: str, dialect_id: int | None = None, limit: int = 5
    ) -> dict:
        segments = self.similar_segments(q, dialect_id=dialect_id, limit=limit)
        senses = self._matching_senses(q, limit=limit)
        return {"segments": segments, "senses": senses}

    def grammar_rules_for_sentence(
        self, q: str, dialect_id: int | None = None, limit: int = 5
    ) -> list[dict]:
        normalized = normalize_arabic(q)
        query_vector = embed_text(normalized)
        statement = self.db.query(GrammarRule).filter(
            GrammarRule.is_active.is_(True),
            GrammarRule.review_status == RecordStatus.approved,
        )
        if dialect_id is not None:
            statement = statement.filter(GrammarRule.dialect_id == dialect_id)
        rules = statement.all()
        ranked = [
            self._grammar_result(rule, normalized, query_vector) for rule in rules
        ]
        ranked.sort(key=lambda item: item["similarity_score"], reverse=True)
        return ranked[:limit]

    def references_for_sentence(
        self, q: str, dialect_id: int | None = None
    ) -> dict:
        examples = self.examples_for_sentence(q, dialect_id=dialect_id, limit=5)
        grammar_rules = self.grammar_rules_for_sentence(
            q, dialect_id=dialect_id, limit=5
        )
        references = [
            item["reference"]
            for item in [*examples["segments"], *examples["senses"], *grammar_rules]
        ]
        return {
            "similar_examples": examples["segments"],
            "meaning_examples": examples["senses"],
            "grammar_notes": grammar_rules,
            "references": references,
        }

    def _matching_senses(self, q: str, limit: int) -> list[dict]:
        normalized = normalize_arabic(q)
        tokens = tokenize_arabic(q)
        query_vector = embed_text(normalized)
        statement = self.db.query(ArabicSense).filter(
            ArabicSense.review_status == RecordStatus.approved
        )
        conditions = [
            ArabicSense.normalized_arabic_lemma == token for token in tokens
        ]
        if conditions:
            statement = statement.filter(
                or_(*conditions) | ArabicSense.definition_ar.contains(normalized)
            )
        senses = statement.all()
        ranked = [
            self._sense_result(sense, normalized, query_vector) for sense in senses
        ]
        ranked.sort(key=lambda item: item["similarity_score"], reverse=True)
        return ranked[:limit]

    def _postgres_full_text_segments(self, statement, normalized: str, limit: int):  # noqa: ANN001
        tokens = tokenize_arabic(normalized)
        if not tokens:
            return []
        query_text = " & ".join(tokens)
        return (
            statement.filter(
                func.to_tsvector(
                    "simple", ParallelSegment.normalized_arabic_text
                ).op("@@")(func.to_tsquery("simple", query_text))
            )
            .limit(limit)
            .all()
        )

    @staticmethod
    def _merge_rows(*groups: list[ParallelSegment]) -> list[ParallelSegment]:
        merged: dict[int, ParallelSegment] = {}
        for group in groups:
            for row in group:
                merged[row.id] = row
        return list(merged.values())

    def _segment_result(
        self, segment: ParallelSegment, normalized: str, query_vector: list[float]
    ) -> dict[str, Any]:
        segment_text = segment.normalized_arabic_text or normalize_arabic(
            segment.arabic_text
        )
        text_score = SequenceMatcher(None, normalized, segment_text).ratio()
        token_score = self._token_overlap(normalized, segment_text)
        tri_score = compute_trigram_overlap(normalized, segment_text)
        vector_score = cosine_similarity(
            query_vector,
            segment.arabic_embedding or segment.sentence_embedding,
        )

        source = getattr(segment, "source", None)
        if source is None and segment.source_id and self.db:
            source = self.db.get(Source, segment.source_id)

        source_qual = get_source_quality_score(source)
        rev_score = get_review_status_score(segment.review_status)

        hybrid_score, breakdown = compute_hybrid_ranking(
            text_ratio=text_score,
            token_overlap=token_score,
            trigram_overlap=tri_score,
            vector_score=vector_score,
            source_quality=source_qual,
            review_status=rev_score,
        )

        return {
            "id": segment.id,
            "arabic_text": segment.arabic_text,
            "coptic_text": segment.coptic_text,
            "source_id": segment.source_id,
            "source_title": source.title if source else None,
            "dialect_id": segment.dialect_id,
            "similarity_score": hybrid_score,
            "score_breakdown": breakdown,
            "match_type": self._match_type(text_score, token_score, vector_score),
            "reference": {"table": "parallel_segments", "id": segment.id},
        }

    def _sense_result(
        self, sense: ArabicSense, normalized: str, query_vector: list[float]
    ) -> dict[str, Any]:
        lemma_score = SequenceMatcher(
            None, normalized, sense.normalized_arabic_lemma
        ).ratio()
        tri_score = compute_trigram_overlap(normalized, sense.normalized_arabic_lemma)
        meaning_vector = sense.meaning_embedding or embed_text(sense.definition_ar)
        vector_score = cosine_similarity(query_vector, meaning_vector)
        rev_score = get_review_status_score(sense.review_status)

        hybrid_score, breakdown = compute_hybrid_ranking(
            text_ratio=lemma_score,
            token_overlap=lemma_score,
            trigram_overlap=tri_score,
            vector_score=vector_score,
            source_quality=0.85,
            review_status=rev_score,
        )

        return {
            "id": sense.id,
            "arabic_lemma": sense.arabic_lemma,
            "meaning_ar": sense.definition_ar,
            "similarity_score": hybrid_score,
            "score_breakdown": breakdown,
            "reference": {"table": "arabic_senses", "id": sense.id},
        }

    def _grammar_result(
        self, rule: GrammarRule, normalized: str, query_vector: list[float]
    ) -> dict[str, Any]:
        text_score = SequenceMatcher(
            None, normalized, normalize_arabic(rule.description)
        ).ratio()
        vector_score = cosine_similarity(
            query_vector,
            rule.description_embedding or embed_text(rule.description),
        )
        pattern_score = (
            0.6 if len(tokenize_arabic(normalized)) > 1 and rule.pattern else 0.0
        )
        tri_score = compute_trigram_overlap(
            normalized, normalize_arabic(rule.description)
        )
        rev_score = get_review_status_score(rule.review_status)

        hybrid_score, breakdown = compute_hybrid_ranking(
            text_ratio=text_score,
            token_overlap=pattern_score,
            trigram_overlap=tri_score,
            vector_score=vector_score,
            source_quality=0.90,
            review_status=rev_score,
        )

        return {
            "id": rule.id,
            "title": rule.title,
            "description": rule.description,
            "pattern": rule.pattern,
            "replacement": rule.replacement,
            "similarity_score": hybrid_score,
            "score_breakdown": breakdown,
            "reference": {"table": "grammar_rules", "id": rule.id},
        }

    @staticmethod
    def _token_overlap(left: str, right: str) -> float:
        left_tokens = set(tokenize_arabic(left))
        right_tokens = set(tokenize_arabic(right))
        if not left_tokens or not right_tokens:
            return 0.0
        return round(
            len(left_tokens & right_tokens) / len(left_tokens | right_tokens), 4
        )

    @staticmethod
    def _match_type(text_score: float, token_score: float, vector_score: float) -> str:
        best = max(text_score, token_score, vector_score)
        if best == vector_score:
            return "vector"
        if best == token_score:
            return "full_text"
        return "text"

    def _is_postgres(self) -> bool:
        bind = (
            self.db.get_bind()
            if hasattr(self.db, "get_bind")
            else getattr(self.db, "bind", None)
        )
        return bind is not None and bind.dialect.name == "postgresql"
