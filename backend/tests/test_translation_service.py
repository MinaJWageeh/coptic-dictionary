from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import (
    ArabicSense,
    Dialect,
    DictionaryEntry,
    GrammarRule,
    ParallelSegment,
    SenseMapping,
    Source,
    TranslationCandidate,
    TranslationRequest,
)
from app.models.enums import PartOfSpeech, RecordStatus
from app.seed.run import seed
from app.services.translation import TranslationService


def _get_dialect_and_source(db: Session) -> tuple[int, int]:
    dialect = db.query(Dialect).first()
    source = db.query(Source).first()
    dialect_id = dialect.id if dialect else 1
    source_id = source.id if source else 1
    return dialect_id, source_id


def _entry(
    db: Session,
    arabic: str,
    coptic: str,
    pos: PartOfSpeech,
    meaning: str,
    confidence: float = 0.9,
) -> DictionaryEntry:
    dialect_id, source_id = _get_dialect_and_source(db)
    entry = DictionaryEntry(
        coptic_text=coptic,
        normalized_coptic_text=coptic,
        transliteration=coptic,
        dialect_id=dialect_id,
        source_id=source_id,
        part_of_speech=pos,
        example_sentence=f"{coptic} example",
        review_status=RecordStatus.approved,
    )
    db.add(entry)
    db.flush()
    sense = ArabicSense(
        arabic_lemma=arabic,
        normalized_arabic_lemma=TranslationService.normalize_arabic(arabic),
        definition_ar=meaning,
        part_of_speech=pos,
        example_ar=f"مثال {arabic}",
        source_id=source_id,
        review_status=RecordStatus.approved,
    )
    db.add(sense)
    db.flush()
    db.add(
        SenseMapping(
            arabic_sense_id=sense.id,
            dictionary_entry_id=entry.id,
            confidence=confidence,
            is_primary=True,
            review_status=RecordStatus.approved,
        )
    )
    db.commit()
    db.refresh(entry)
    return entry


def _approved_segment(db: Session, arabic: str, coptic: str) -> ParallelSegment:
    dialect_id, source_id = _get_dialect_and_source(db)
    segment = ParallelSegment(
        source_id=source_id,
        dialect_id=dialect_id,
        arabic_text=arabic,
        normalized_arabic_text=TranslationService.normalize_arabic(arabic),
        coptic_text=coptic,
        normalized_coptic_text=coptic,
        sentence_embedding=TranslationService.embed_text(arabic),
        review_status=RecordStatus.approved,
    )
    db.add(segment)
    db.commit()
    db.refresh(segment)
    return segment


def _grammar_rule(db: Session) -> GrammarRule:
    dialect_id, source_id = _get_dialect_and_source(db)
    rule = GrammarRule(
        dialect_id=dialect_id,
        source_id=source_id,
        title="Simple noun adjective order",
        rule_code="SAH_NOUN_ADJ",
        description="Keep noun before adjective for this simple pattern.",
        pattern="noun adjective",
        replacement="{noun} {adjective}",
        examples=[],
        priority=10,
        review_status=RecordStatus.approved,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


def test_single_word_translation_returns_mapped_coptic_entries(db_session: Session) -> None:
    entry = _entry(db_session, "إله", "ⲛⲟⲩϯ", PartOfSpeech.noun, "كائن إلهي")

    result = TranslationService(db_session).translate_word("إِلَه")

    assert result["input_type"] == "word"
    assert result["normalized_text"] == "اله"
    assert result["entries"][0]["dictionary_entry_id"] == entry.id
    assert result["entries"][0]["coptic_word"] == "ⲛⲟⲩϯ"
    assert result["entries"][0]["dialect"] == "Sahidic"
    assert result["entries"][0]["part_of_speech"] == "noun"
    assert result["entries"][0]["meaning"] == "كائن إلهي"
    assert result["entries"][0]["source"] == "Seed Lexicon"
    assert result["entries"][0]["confidence"] == 0.9
    assert result["entries"][0]["examples"]


def test_single_word_translation_uses_arabic_prefix_fallback(db_session: Session) -> None:
    entry = _entry(db_session, "سلام", "ⲉⲓⲣⲏⲛⲏ", PartOfSpeech.noun, "تحية وسلام")

    result = TranslationService(db_session).translate_word("السلام")

    assert result["review_status"] == "approved"
    assert result["entries"][0]["dictionary_entry_id"] == entry.id
    assert result["entries"][0]["coptic_word"] == "ⲉⲓⲣⲏⲛⲏ"


def test_sentence_with_all_known_words_returns_draft_candidate_breakdown(db_session: Session) -> None:
    god = _entry(db_session, "إله", "ⲛⲟⲩϯ", PartOfSpeech.noun, "كائن إلهي")
    good = _entry(db_session, "صالح", "ⲁⲅⲁⲑⲟⲥ", PartOfSpeech.adjective, "طيب")
    example = _approved_segment(db_session, "إله صالح جدا", "ⲛⲟⲩϯ ⲁⲅⲁⲑⲟⲥ ⲉⲙⲁⲧⲉ")
    rule = _grammar_rule(db_session)

    result = TranslationService(db_session).translate_sentence("إله صالح", user_id=1, target_dialect_id=1)

    assert result["review_status"] == "draft"
    assert result["candidate_translation"] == "ⲛⲟⲩϯ ⲁⲅⲁⲑⲟⲥ"
    assert result["literal_breakdown"] == [
        {"arabic": "اله", "coptic": "ⲛⲟⲩϯ", "status": "known", "dictionary_entry_id": god.id},
        {"arabic": "صالح", "coptic": "ⲁⲅⲁⲑⲟⲥ", "status": "known", "dictionary_entry_id": good.id},
    ]
    assert result["used_dictionary_entries"] == [god.id, good.id]
    assert result["similar_examples"][0]["id"] == example.id
    assert result["grammar_notes"][0]["id"] == rule.id
    assert result["confidence_score"] >= 0.85
    assert result["needs_human_review"] is False
    assert db_session.query(TranslationRequest).count() == 1
    assert db_session.query(TranslationCandidate).one().review_status == RecordStatus.draft


def test_sentence_translation_uses_arabic_prefix_fallback_in_breakdown(
    db_session: Session,
) -> None:
    god = _entry(db_session, "الله", "Ⲫⲛⲟⲩϯ", PartOfSpeech.noun, "الإله الواحد")
    love = _entry(db_session, "محبة", "ⲁⲅⲁⲡⲏ", PartOfSpeech.noun, "المحبة")
    _approved_segment(db_session, "الله محبة جدا", "Ⲫⲛⲟⲩϯ ⲁⲅⲁⲡⲏ ⲉⲙⲁⲧⲉ")

    result = TranslationService(db_session).translate_sentence("الله المحبة", user_id=1, target_dialect_id=1)

    assert result["literal_breakdown"] == [
        {"arabic": "الله", "coptic": "Ⲫⲛⲟⲩϯ", "status": "known", "dictionary_entry_id": god.id},
        {"arabic": "المحبه", "coptic": "ⲁⲅⲁⲡⲏ", "status": "known", "dictionary_entry_id": love.id},
    ]
    assert result["unknown_words"] == []
    assert result["candidate_translation"] == "Ⲫⲛⲟⲩϯ ⲁⲅⲁⲡⲏ"


def test_sentence_with_unknown_words_marks_unknown_and_does_not_hallucinate(db_session: Session) -> None:
    _entry(db_session, "إله", "ⲛⲟⲩϯ", PartOfSpeech.noun, "كائن إلهي")

    result = TranslationService(db_session).translate_sentence("إله غامض", user_id=1, target_dialect_id=1)

    assert result["literal_breakdown"][0]["status"] == "known"
    assert result["literal_breakdown"][1] == {
        "arabic": "غامض",
        "coptic": None,
        "status": "unknown",
        "dictionary_entry_id": None,
    }
    assert result["unknown_words"] == ["غامض"]
    assert result["candidate_translation"] is None
    assert result["needs_human_review"] is True


def test_low_confidence_translation_requires_human_review(db_session: Session) -> None:
    _entry(db_session, "إله", "ⲛⲟⲩϯ", PartOfSpeech.noun, "كائن إلهي", confidence=0.35)
    _entry(db_session, "صالح", "ⲁⲅⲁⲑⲟⲥ", PartOfSpeech.adjective, "طيب", confidence=0.35)

    result = TranslationService(db_session).translate_sentence("إله صالح", user_id=1, target_dialect_id=1)

    assert result["confidence_score"] < TranslationService.LOW_CONFIDENCE_THRESHOLD
    assert result["needs_human_review"] is True
    assert result["human_review_reason"] == "low_confidence"
    assert result["candidate_translation"] is None


def test_approved_existing_translation_returns_approved_without_new_candidate(db_session: Session) -> None:
    _approved_segment(db_session, "إله صالح", "ⲛⲟⲩϯ ⲁⲅⲁⲑⲟⲥ")

    result = TranslationService(db_session).translate_sentence("إله صالح", user_id=1, target_dialect_id=1)

    assert result["review_status"] == "approved"
    assert result["candidate_translation"] == "ⲛⲟⲩϯ ⲁⲅⲁⲑⲟⲥ"
    assert result["confidence_score"] == 1.0
    assert result["needs_human_review"] is False
    assert db_session.query(TranslationRequest).count() == 0
    assert db_session.query(TranslationCandidate).count() == 0


def test_seeded_allah_love_phrase_returns_approved_translation(db_session: Session) -> None:
    seed(db_session)
    bohairic_id = db_session.query(Dialect).filter(Dialect.code == "bohairic").one().id
    sahidic_id = db_session.query(Dialect).filter(Dialect.code == "sahidic").one().id

    bohairic = TranslationService(db_session).translate(
        "الله محبة", user_id=None, target_dialect_id=bohairic_id
    )
    sahidic_love = TranslationService(db_session).translate(
        "محبة", user_id=None, target_dialect_id=sahidic_id
    )
    sahidic = TranslationService(db_session).translate(
        "الله محبة", user_id=None, target_dialect_id=sahidic_id
    )

    assert bohairic.status == RecordStatus.approved
    assert bohairic.translation == "Ⲫⲛⲟⲩϯ ⲟⲩⲁⲅⲁⲡⲏ ⲡⲉ"
    assert sahidic_love.status == RecordStatus.approved
    assert sahidic_love.translation == "ⲁⲅⲁⲑⲟⲥ" or sahidic_love.translation == "ⲁⲅⲁⲡⲏ"
    assert sahidic.status == RecordStatus.approved
    assert sahidic.translation == "ⲡⲛⲟⲩⲧⲉ ⲟⲩⲁⲅⲁⲡⲏ ⲡⲉ"
