from __future__ import annotations

from sqlalchemy.orm import Session

from app.database import SessionLocal, init_extensions
from app.models import (
    ArabicSense,
    CorpusText,
    Dialect,
    DictionaryEntry,
    GrammarRule,
    ParallelSegment,
    RoleRecord,
    SenseMapping,
    Source,
    User,
)
from app.models.enums import PartOfSpeech, RecordStatus, Role, SourceType
from app.security import get_password_hash
from app.seed.data.curated_lexicon import CURATED_LEXICON
from app.services.deduplication import DeduplicationService
from app.services.embedding import embed_text
from app.services.sources import ensure_standard_sources
from app.services.text import normalize_arabic

SAMPLE_NOTE = (
    "Sample data for development and UI testing only. This is not a final scholarly "
    "Coptic source and must be verified by a human reviewer before production use."
)
NEEDS_VERIFICATION_NOTE = f"{SAMPLE_NOTE} Needs verification."


def _role_records(db: Session) -> None:
    descriptions = {
        Role.user: "Can translate and inspect public dictionary/examples.",
        Role.reviewer: "Can approve, reject, and correct draft translation candidates.",
        Role.admin: "Can manage users, sources, dictionary, corpus, grammar, and review data.",
    }
    for role, description in descriptions.items():
        if not db.query(RoleRecord).filter(RoleRecord.name == role.value).first():
            db.add(RoleRecord(name=role.value, description=description))


def _dialect(db: Session, code: str, name: str, native_name: str | None = None) -> Dialect:
    dialect = db.query(Dialect).filter(Dialect.code == code).first()
    if dialect:
        dialect.name = name
        dialect.native_name = native_name
        dialect.description = f"{name} Coptic dialect seed record. {SAMPLE_NOTE}"
        dialect.is_active = True
        return dialect
    dialect = Dialect(
        code=code,
        name=name,
        native_name=native_name,
        description=f"{name} Coptic dialect seed record. {SAMPLE_NOTE}",
        is_active=True,
    )
    db.add(dialect)
    db.flush()
    return dialect


def _user(db: Session, email: str, display_name: str, role: Role, dialect_id: int | None) -> User:
    user = db.query(User).filter(User.email == email).first()
    if user:
        return user
    user = User(
        email=email,
        display_name=display_name,
        password_hash=get_password_hash("ChangeMe123!"),
        role=role,
        preferred_dialect_id=dialect_id,
    )
    db.add(user)
    db.flush()
    return user


def _source(
    db: Session,
    *,
    title: str,
    source_type: SourceType,
    notes: str,
    admin_id: int,
    author: str = "Coptic Translator Project",
) -> Source:
    source = db.query(Source).filter(Source.title == title).first()
    if source:
        source.type = source_type
        source.author = author
        source.notes = notes
        return source
    source = Source(
        title=title,
        author=author,
        type=source_type,
        notes=notes,
        created_by=admin_id,
    )
    db.add(source)
    db.flush()
    return source


def _entry(
    db: Session,
    *,
    coptic_text: str,
    transliteration: str,
    dialect_id: int,
    source_id: int,
    part_of_speech: PartOfSpeech,
    created_by: int,
    notes: str = NEEDS_VERIFICATION_NOTE,
    review_status: RecordStatus = RecordStatus.approved,
) -> DictionaryEntry:
    entry = (
        db.query(DictionaryEntry)
        .filter(
            DictionaryEntry.normalized_coptic_text == coptic_text,
            DictionaryEntry.dialect_id == dialect_id,
            DictionaryEntry.part_of_speech == part_of_speech,
            DictionaryEntry.source_id == source_id,
        )
        .first()
    )
    if entry:
        entry.coptic_text = coptic_text
        entry.transliteration = transliteration
        entry.notes = notes
        entry.review_status = review_status
        return entry
    entry = DictionaryEntry(
        coptic_text=coptic_text,
        normalized_coptic_text=coptic_text,
        transliteration=transliteration,
        dialect_id=dialect_id,
        source_id=source_id,
        part_of_speech=part_of_speech,
        review_status=review_status,
        created_by=created_by,
        reviewed_by=created_by if review_status == RecordStatus.approved else None,
        notes=notes,
    )
    db.add(entry)
    db.flush()
    return entry


def _sense(
    db: Session,
    *,
    arabic_lemma: str,
    definition_ar: str,
    part_of_speech: PartOfSpeech,
    source_id: int,
    created_by: int,
    example_ar: str | None = None,
    review_status: RecordStatus = RecordStatus.approved,
) -> ArabicSense:
    normalized = normalize_arabic(arabic_lemma)
    sense = (
        db.query(ArabicSense)
        .filter(
            ArabicSense.normalized_arabic_lemma == normalized,
            ArabicSense.definition_ar == definition_ar,
        )
        .first()
    )
    if sense:
        sense.part_of_speech = part_of_speech
        sense.source_id = source_id
        sense.example_ar = example_ar
        sense.review_status = review_status
        sense.meaning_embedding = embed_text(definition_ar)
        return sense
    sense = ArabicSense(
        arabic_lemma=arabic_lemma,
        normalized_arabic_lemma=normalized,
        sense_key=f"sample:{normalized}:{part_of_speech.value}",
        definition_ar=definition_ar,
        part_of_speech=part_of_speech,
        example_ar=example_ar,
        source_id=source_id,
        review_status=review_status,
        example_embedding=embed_text(example_ar) if example_ar else None,
        meaning_embedding=embed_text(definition_ar),
        created_by=created_by,
        reviewed_by=created_by if review_status == RecordStatus.approved else None,
    )
    db.add(sense)
    db.flush()
    return sense


def _mapping(
    db: Session,
    *,
    sense_id: int,
    entry_id: int,
    created_by: int,
    confidence: float,
    usage_note: str = NEEDS_VERIFICATION_NOTE,
    review_status: RecordStatus = RecordStatus.approved,
    is_primary: bool = True,
) -> None:
    mapping = (
        db.query(SenseMapping)
        .filter(
            SenseMapping.arabic_sense_id == sense_id,
            SenseMapping.dictionary_entry_id == entry_id,
        )
        .first()
    )
    if mapping:
        mapping.confidence = confidence
        mapping.usage_note = usage_note
        mapping.review_status = review_status
        mapping.is_primary = is_primary
        return
    db.add(
        SenseMapping(
            arabic_sense_id=sense_id,
            dictionary_entry_id=entry_id,
            confidence=confidence,
            usage_note=usage_note,
            is_primary=is_primary,
            review_status=review_status,
            created_by=created_by,
            reviewed_by=created_by if review_status == RecordStatus.approved else None,
        )
    )


def _corpus(db: Session, source_id: int, dialect_id: int, admin_id: int) -> CorpusText:
    corpus = db.query(CorpusText).filter(CorpusText.title == "Sample Parallel Sentences for Review").first()
    if corpus:
        corpus.source_id = source_id
        corpus.dialect_id = dialect_id
        corpus.review_status = RecordStatus.draft
        corpus.content = NEEDS_VERIFICATION_NOTE
        corpus.extra_metadata = {"purpose": "sample_seed", "verification_status": "needs_verification"}
        return corpus
    corpus = CorpusText(
        title="Sample Parallel Sentences for Review",
        source_id=source_id,
        dialect_id=dialect_id,
        language="parallel",
        content=NEEDS_VERIFICATION_NOTE,
        review_status=RecordStatus.draft,
        extra_metadata={"purpose": "sample_seed", "verification_status": "needs_verification"},
        created_by=admin_id,
    )
    db.add(corpus)
    db.flush()
    return corpus


def _parallel_segment(
    db: Session,
    *,
    corpus_id: int | None,
    source_id: int,
    dialect_id: int,
    order: int,
    arabic_text: str,
    coptic_text: str,
    admin_id: int,
) -> None:
    segment = (
        db.query(ParallelSegment)
        .filter(
            ParallelSegment.arabic_text == arabic_text,
            ParallelSegment.dialect_id == dialect_id,
            ParallelSegment.source_id == source_id,
        )
        .first()
    )
    values = {
        "corpus_text_id": corpus_id,
        "segment_order": order,
        "coptic_text": coptic_text,
        "normalized_arabic_text": normalize_arabic(arabic_text),
        "normalized_coptic_text": coptic_text,
        "alignment_score": 0.95,
        "arabic_embedding": embed_text(arabic_text),
        "coptic_embedding": embed_text(coptic_text),
        "sentence_embedding": embed_text(arabic_text),
        "review_status": RecordStatus.approved,
    }
    if segment:
        for field, value in values.items():
            setattr(segment, field, value)
        return
    db.add(
        ParallelSegment(
            corpus_text_id=corpus_id,
            source_id=source_id,
            dialect_id=dialect_id,
            segment_order=order,
            arabic_text=arabic_text,
            coptic_text=coptic_text,
            normalized_arabic_text=values["normalized_arabic_text"],
            normalized_coptic_text=coptic_text,
            alignment_score=values["alignment_score"],
            arabic_embedding=values["arabic_embedding"],
            coptic_embedding=values["coptic_embedding"],
            sentence_embedding=values["sentence_embedding"],
            review_status=RecordStatus.approved,
            created_by=admin_id,
        )
    )


def _grammar_rule(
    db: Session,
    *,
    dialect_id: int,
    source_id: int,
    title: str,
    rule_code: str,
    description: str,
    pattern: str,
    replacement: str,
    examples: list[dict],
    priority: int,
    admin_id: int,
) -> None:
    description_with_note = f"{description} {NEEDS_VERIFICATION_NOTE}"
    rule = db.query(GrammarRule).filter(GrammarRule.rule_code == rule_code).first()
    values = {
        "dialect_id": dialect_id,
        "source_id": source_id,
        "title": title,
        "description": description_with_note,
        "description_embedding": embed_text(description_with_note),
        "pattern": pattern,
        "replacement": replacement,
        "examples": examples,
        "priority": priority,
        "is_active": True,
        "review_status": RecordStatus.draft,
    }
    if rule:
        for field, value in values.items():
            setattr(rule, field, value)
        return
    db.add(
        GrammarRule(
            rule_code=rule_code,
            created_by=admin_id,
            **values,
        )
    )


def _seed_dictionary(
    db: Session,
    *,
    bohairic_id: int,
    sahidic_id: int,
    source_id: int,
    admin_id: int,
) -> None:
    rows = [
        {
            "arabic": "الله",
            "definition": "اسم يشير إلى الله في سياق ديني. Sample sense only; needs verification.",
            "pos": PartOfSpeech.noun,
            "example": "الله محبة",
            "entries": [
                (bohairic_id, "Ⲫⲛⲟⲩϯ", "Pnouti", 0.95),
                (sahidic_id, "ⲡⲛⲟⲩⲧⲉ", "pnoute", 0.95),
            ],
        },
        {
            "arabic": "محبة",
            "definition": "معنى عربي شائع للمحبة أو الحب. Sample sense only; needs verification.",
            "pos": PartOfSpeech.noun,
            "example": "الله محبة",
            "entries": [
                (bohairic_id, "ⲁⲅⲁⲡⲏ", "agape", 0.95),
                (sahidic_id, "ⲁⲅⲁⲡⲏ", "agape", 0.95),
            ],
        },
        {
            "arabic": "سلام",
            "definition": "السلام أو السكينة. Sample sense only; needs verification.",
            "pos": PartOfSpeech.noun,
            "example": "السلام لكم",
            "entries": [(bohairic_id, "ⲉⲓⲣⲏⲛⲏ", "eirene", 0.95)],
        },
        {
            "arabic": "نور",
            "definition": "النور أو الضوء. Sample sense only; needs verification.",
            "pos": PartOfSpeech.noun,
            "example": "أنا أحب النور",
            "entries": [(bohairic_id, "ⲟⲩⲟⲓⲛⲓ", "ouoini", 0.95)],
        },
        {
            "arabic": "حياة",
            "definition": "الحياة أو العيش. Sample sense only; needs verification.",
            "pos": PartOfSpeech.noun,
            "example": "الحياة نور",
            "entries": [(bohairic_id, "ⲱⲛϧ", "onkh", 0.95)],
        },
        {
            "arabic": "أنا",
            "definition": "ضمير المتكلم المفرد. Sample sense only; needs verification.",
            "pos": PartOfSpeech.pronoun,
            "example": "أنا أحب النور",
            "entries": [(bohairic_id, "ⲁⲛⲟⲕ", "anok", 0.95)],
        },
        {
            "arabic": "أنت",
            "definition": "ضمير المخاطب المفرد. Sample sense only; needs verification.",
            "pos": PartOfSpeech.pronoun,
            "example": "أنت عظيم",
            "entries": [(bohairic_id, "ⲛⲑⲟⲕ", "nthok", 0.95)],
        },
        {
            "arabic": "هو",
            "definition": "ضمير الغائب المفرد. Sample sense only; needs verification.",
            "pos": PartOfSpeech.pronoun,
            "example": "هو عظيم",
            "entries": [(bohairic_id, "ⲛⲑⲟϥ", "nthof", 0.95)],
        },
        {
            "arabic": "أحب",
            "definition": "فعل يدل على المحبة. Sample sense only; needs verification.",
            "pos": PartOfSpeech.verb,
            "example": "أنا أحب النور",
            "entries": [(bohairic_id, "ⲙⲉⲓ", "mei", 0.90)],
        },
        {
            "arabic": "عظيم",
            "definition": "صفة بمعنى كبير أو جليل. Sample sense only; needs verification.",
            "pos": PartOfSpeech.adjective,
            "example": "هو عظيم",
            "entries": [(bohairic_id, "ⲛⲓϣϯ", "nishti", 0.90)],
        },
    ]

    for row in rows:
        sense = _sense(
            db,
            arabic_lemma=row["arabic"],
            definition_ar=row["definition"],
            part_of_speech=row["pos"],
            source_id=source_id,
            created_by=admin_id,
            example_ar=row["example"],
            review_status=RecordStatus.approved,
        )
        for dialect_id, coptic_text, transliteration, confidence in row["entries"]:
            entry = _entry(
                db,
                coptic_text=coptic_text,
                transliteration=transliteration,
                dialect_id=dialect_id,
                source_id=source_id,
                part_of_speech=row["pos"],
                created_by=admin_id,
                notes=NEEDS_VERIFICATION_NOTE,
                review_status=RecordStatus.approved,
            )
            _mapping(
                db,
                sense_id=sense.id,
                entry_id=entry.id,
                created_by=admin_id,
                confidence=confidence,
                usage_note=NEEDS_VERIFICATION_NOTE,
                review_status=RecordStatus.approved,
                is_primary=dialect_id == bohairic_id,
            )


def _seed_parallel_segments(db: Session, *, source_id: int, dialect_id: int, admin_id: int) -> None:
    corpus = _corpus(db, source_id, dialect_id, admin_id)
    rows = [
        ("الله محبة", "Ⲫⲛⲟⲩϯ ⲟⲩⲁⲅⲁⲡⲏ ⲡⲉ"),
        ("أنا أحب النور", "ⲁⲛⲟⲕ ϯⲙⲉⲓ ⲙ̀ⲡⲓⲟⲩⲟⲓⲛⲓ"),
        ("السلام لكم", "ⲡⲓⲉⲓⲣⲏⲛⲏ ⲛⲱⲧⲉⲛ"),
        ("هو عظيم", "ⲛⲑⲟϥ ⲟⲩⲛⲓϣϯ"),
        ("الحياة نور", "ⲡⲓⲱⲛϧ ⲟⲩⲟⲩⲟⲓⲛⲓ"),
    ]
    for index, (arabic_text, coptic_text) in enumerate(rows, start=1):
        _parallel_segment(
            db,
            corpus_id=corpus.id,
            source_id=source_id,
            dialect_id=dialect_id,
            order=index,
            arabic_text=arabic_text,
            coptic_text=coptic_text,
            admin_id=admin_id,
        )


def _seed_grammar_rules(db: Session, *, source_id: int, dialect_id: int, admin_id: int) -> None:
    rows = [
        {
            "title": "جملة اسمية",
            "rule_code": "sample-nominal-sentence",
            "description": "Sample nominal sentence pattern for Arabic-to-Coptic testing.",
            "pattern": "NOUN/PRONOUN + NOUN/ADJECTIVE",
            "replacement": "{subject} {predicate}",
            "examples": [{"arabic": "الله محبة", "coptic": "Ⲫⲛⲟⲩϯ ⲟⲩⲁⲅⲁⲡⲏ ⲡⲉ"}],
            "priority": 20,
        },
        {
            "title": "جملة فعلية",
            "rule_code": "sample-verbal-sentence",
            "description": "Sample verbal sentence pattern for simple subject verb ordering.",
            "pattern": "SUBJECT + VERB",
            "replacement": "{subject} {verb}",
            "examples": [{"arabic": "أنا أحب", "coptic": "ⲁⲛⲟⲕ ϯⲙⲉⲓ"}],
            "priority": 30,
        },
        {
            "title": "نفي",
            "rule_code": "sample-negation",
            "description": "Sample negation placeholder rule; not validated for dialectal correctness.",
            "pattern": "NEGATION + VERB",
            "replacement": "{negation} {verb}",
            "examples": [{"arabic": "لا أحب", "coptic": "sample only"}],
            "priority": 40,
        },
        {
            "title": "إضافة",
            "rule_code": "sample-genitive",
            "description": "Sample possession/genitive relationship pattern.",
            "pattern": "NOUN + OF + NOUN",
            "replacement": "{head} {linker} {dependent}",
            "examples": [{"arabic": "نور الحياة", "coptic": "sample only"}],
            "priority": 50,
        },
        {
            "title": "ضمير + فعل + مفعول",
            "rule_code": "sample-pronoun-verb-object",
            "description": "Sample pronoun verb object pattern for low-confidence composition tests.",
            "pattern": "PRONOUN + VERB + OBJECT",
            "replacement": "{pronoun} {verb} {object}",
            "examples": [{"arabic": "أنا أحب النور", "coptic": "ⲁⲛⲟⲕ ϯⲙⲉⲓ ⲙ̀ⲡⲓⲟⲩⲟⲓⲛⲓ"}],
            "priority": 10,
        },
    ]
    for row in rows:
        _grammar_rule(db, dialect_id=dialect_id, source_id=source_id, admin_id=admin_id, **row)


def _seed_curated_lexicon(
    db: Session,
    *,
    standard_sources: dict[str, Source],
    bohairic_id: int,
    sahidic_id: int,
    admin_id: int,
) -> None:
    dedup = DeduplicationService(db)
    dialect_map = {"bohairic": bohairic_id, "sahidic": sahidic_id}
    default_source = standard_sources.get("A Coptic Dictionary (Crum)") or next(iter(standard_sources.values()))

    for item in CURATED_LEXICON:
        source = standard_sources.get(item.source_title, default_source)
        dialect_id = dialect_map.get(item.dialect, bohairic_id)

        entry_res = dedup.find_or_create_coptic_entry(
            coptic_text=item.coptic,
            dialect_id=dialect_id,
            part_of_speech=item.pos,
            source_id=source.id,
            transliteration=item.transliteration,
            notes=f"Scholarly citation: {item.citation}",
            example_sentence=item.example_coptic,
            review_status=RecordStatus.approved,
            admin_id=admin_id,
        )
        sense_res = dedup.find_or_create_arabic_sense(
            arabic_lemma=item.arabic,
            definition_ar=item.definition,
            part_of_speech=item.pos,
            source_id=source.id,
            example_ar=item.example_arabic,
            review_status=RecordStatus.approved,
            admin_id=admin_id,
        )
        dedup.find_or_create_sense_mapping(
            arabic_sense_id=sense_res.sense.id,
            dictionary_entry_id=entry_res.entry.id,
            confidence=item.confidence,
            usage_note=item.citation,
            is_primary=True,
            review_status=RecordStatus.approved,
            admin_id=admin_id,
        )


def seed(db: Session) -> None:
    try:
        init_extensions(db)
    except Exception:
        db.rollback()

    _role_records(db)
    bohairic = _dialect(db, "bohairic", "Bohairic", "Ⲙⲉⲧⲣⲉⲙⲛⲭⲏⲙⲓ")
    sahidic = _dialect(db, "sahidic", "Sahidic", "Ⲙⲉⲧⲣⲉⲙⲛⲕⲏⲙⲉ")
    admin = _user(db, "admin@example.com", "Admin", Role.admin, bohairic.id)
    _user(db, "reviewer@example.com", "Reviewer", Role.reviewer, bohairic.id)
    _user(db, "user@example.com", "User", Role.user, bohairic.id)

    # 1. Standard Reference Sources (Crum, CCL, Labib, LSJ, Bailly, Moawad, Scriptorium)
    standard_sources = ensure_standard_sources(db, admin.id)

    # 2. Curated Scholarly Lexicon entries
    _seed_curated_lexicon(
        db,
        standard_sources=standard_sources,
        bohairic_id=bohairic.id,
        sahidic_id=sahidic.id,
        admin_id=admin.id,
    )

    manual_source = _source(
        db,
        title="Manual Test Source",
        source_type=SourceType.user_submission,
        notes=f"{SAMPLE_NOTE} Manual test source for local QA only.",
        admin_id=admin.id,
    )
    liturgical_source = _source(
        db,
        title="Sample Liturgical Source",
        source_type=SourceType.corpus,
        notes=f"{SAMPLE_NOTE} Sample liturgical-style examples for review only.",
        admin_id=admin.id,
    )
    dictionary_source = _source(
        db,
        title="Sample Dictionary Source",
        source_type=SourceType.dictionary,
        notes=f"{SAMPLE_NOTE} Sample dictionary entries; not a final lexical authority.",
        admin_id=admin.id,
    )

    _seed_dictionary(
        db,
        bohairic_id=bohairic.id,
        sahidic_id=sahidic.id,
        source_id=dictionary_source.id,
        admin_id=admin.id,
    )
    _seed_parallel_segments(db, source_id=liturgical_source.id, dialect_id=bohairic.id, admin_id=admin.id)
    _parallel_segment(
        db,
        corpus_id=None,
        source_id=liturgical_source.id,
        dialect_id=sahidic.id,
        order=1,
        arabic_text="الله محبة",
        coptic_text="ⲡⲛⲟⲩⲧⲉ ⲟⲩⲁⲅⲁⲡⲏ ⲡⲉ",
        admin_id=admin.id,
    )
    _seed_grammar_rules(db, source_id=manual_source.id, dialect_id=bohairic.id, admin_id=admin.id)
    db.commit()


def main() -> None:
    with SessionLocal() as db:
        seed(db)
    print("Seed data is ready.")


if __name__ == "__main__":
    main()
