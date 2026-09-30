from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import inspect
from sqlalchemy.orm import Session

from app.models import (
    ArabicSense,
    AuditLog,
    CorpusText,
    GrammarRule,
    ParallelSegment,
    SenseMapping,
    Source,
    User,
)
from app.models.enums import RecordStatus
from app.schemas.admin import (
    ArabicSenseCreate,
    CorpusTextCreate,
    GrammarRuleCreate,
    ParallelSegmentCreate,
    SenseMappingCreate,
    SourceCreate,
    UserCreate,
)
from app.security import get_password_hash
from app.services.embedding import embed_text
from app.services.text import normalize_arabic, normalize_coptic


def _snapshot(record: object) -> dict:
    values: dict = {}
    for attr in inspect(record).mapper.column_attrs:
        value = getattr(record, attr.key)
        if hasattr(value, "value"):
            value = value.value
        if isinstance(value, datetime | date):
            value = value.isoformat()
        values[attr.columns[0].name] = value
    return values


def log_audit(
    db: Session,
    *,
    user_id: int | None,
    action: str,
    record: object,
    old_data: dict | None = None,
    new_data: dict | None = None,
) -> None:
    db.add(
        AuditLog(
            user_id=user_id,
            action=action,
            table_name=getattr(record, "__tablename__"),
            record_id=getattr(record, "id"),
            old_data=old_data,
            new_data=new_data,
        )
    )


def update_record(db: Session, model: type, record_id: int, payload, user_id: int | None):
    from fastapi import HTTPException

    record = db.get(model, record_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"{model.__tablename__} record not found")
    old = _snapshot(record)
    values = payload.model_dump(exclude_unset=True)
    if "metadata" in values:
        values["extra_metadata"] = values.pop("metadata")
    if isinstance(record, User) and "password" in values:
        password = values.pop("password")
        if password:
            values["password_hash"] = get_password_hash(password)
    for field, value in values.items():
        setattr(record, field, value)
    _refresh_computed_fields(record)
    db.flush()
    log_audit(db, user_id=user_id, action="update", record=record, old_data=old, new_data=_snapshot(record))
    db.commit()
    db.refresh(record)
    return record


def delete_record(db: Session, model: type, record_id: int, user_id: int | None) -> None:
    from fastapi import HTTPException

    record = db.get(model, record_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"{model.__tablename__} record not found")
    old = _snapshot(record)
    log_audit(db, user_id=user_id, action="delete", record=record, old_data=old, new_data=None)
    db.delete(record)
    db.commit()


def _refresh_computed_fields(record: object) -> None:
    if isinstance(record, ArabicSense):
        record.normalized_arabic_lemma = record.normalized_arabic_lemma or normalize_arabic(record.arabic_lemma)
        record.meaning_embedding = embed_text(record.definition_ar)
    if isinstance(record, ParallelSegment):
        record.normalized_arabic_text = record.normalized_arabic_text or normalize_arabic(record.arabic_text)
        record.normalized_coptic_text = record.normalized_coptic_text or (normalize_coptic(record.coptic_text) if record.coptic_text else None)
        record.arabic_embedding = embed_text(record.arabic_text)
        record.coptic_embedding = embed_text(record.coptic_text or "")
        record.sentence_embedding = embed_text(record.arabic_text)
    if isinstance(record, GrammarRule):
        record.description_embedding = embed_text(record.description)


def create_source(db: Session, payload: SourceCreate, user_id: int | None) -> Source:
    source = Source(**payload.model_dump(), created_by=user_id)
    db.add(source)
    db.flush()
    log_audit(db, user_id=user_id, action="create", record=source, new_data=_snapshot(source))
    db.commit()
    db.refresh(source)
    return source


def create_user(db: Session, payload: UserCreate) -> User:
    user = User(
        email=payload.email,
        display_name=payload.display_name,
        password_hash=get_password_hash(payload.password),
        role=payload.role,
        preferred_dialect_id=payload.preferred_dialect_id,
        is_active=payload.is_active,
    )
    db.add(user)
    db.flush()
    log_audit(db, user_id=None, action="create", record=user, new_data=_snapshot(user))
    db.commit()
    db.refresh(user)
    return user


def create_arabic_sense(db: Session, payload: ArabicSenseCreate, user_id: int | None) -> ArabicSense:
    sense = ArabicSense(
        arabic_lemma=payload.arabic_lemma,
        normalized_arabic_lemma=payload.normalized_arabic_lemma or normalize_arabic(payload.arabic_lemma),
        sense_key=payload.sense_key,
        definition_ar=payload.definition_ar,
        part_of_speech=payload.part_of_speech,
        example_ar=payload.example_ar,
        meaning_embedding=embed_text(payload.definition_ar),
        source_id=payload.source_id,
        review_status=payload.review_status,
        created_by=user_id,
    )
    db.add(sense)
    db.flush()
    log_audit(db, user_id=user_id, action="create", record=sense, new_data=_snapshot(sense))
    db.commit()
    db.refresh(sense)
    return sense


def create_mapping(db: Session, payload: SenseMappingCreate, user_id: int | None) -> SenseMapping:
    mapping = SenseMapping(**payload.model_dump(), created_by=user_id)
    db.add(mapping)
    db.flush()
    log_audit(db, user_id=user_id, action="create", record=mapping, new_data=_snapshot(mapping))
    db.commit()
    db.refresh(mapping)
    return mapping


def create_corpus_text(db: Session, payload: CorpusTextCreate, user_id: int | None) -> CorpusText:
    corpus = CorpusText(
        title=payload.title,
        source_id=payload.source_id,
        dialect_id=payload.dialect_id,
        language=payload.language,
        content=payload.content,
        review_status=payload.review_status,
        extra_metadata=payload.metadata,
        created_by=user_id,
    )
    db.add(corpus)
    db.flush()
    log_audit(db, user_id=user_id, action="create", record=corpus, new_data=_snapshot(corpus))
    db.commit()
    db.refresh(corpus)
    return corpus


def create_parallel_segment(
    db: Session, payload: ParallelSegmentCreate, user_id: int | None
) -> ParallelSegment:
    segment = ParallelSegment(
            **{
                **payload.model_dump(exclude={"normalized_arabic_text", "normalized_coptic_text"}),
                "normalized_arabic_text": payload.normalized_arabic_text or normalize_arabic(payload.arabic_text),
                "normalized_coptic_text": payload.normalized_coptic_text or payload.coptic_text,
                "arabic_embedding": embed_text(payload.arabic_text),
                "coptic_embedding": embed_text(payload.coptic_text or ""),
                "sentence_embedding": embed_text(payload.arabic_text),
            },
        created_by=user_id,
    )
    db.add(segment)
    db.flush()
    log_audit(db, user_id=user_id, action="create", record=segment, new_data=_snapshot(segment))
    db.commit()
    db.refresh(segment)
    return segment


def create_grammar_rule(db: Session, payload: GrammarRuleCreate, user_id: int | None) -> GrammarRule:
    rule = GrammarRule(
        **payload.model_dump(),
        description_embedding=embed_text(payload.description),
        created_by=user_id,
    )
    db.add(rule)
    db.flush()
    log_audit(db, user_id=user_id, action="create", record=rule, new_data=_snapshot(rule))
    db.commit()
    db.refresh(rule)
    return rule


def create_reviewed_parallel_segment(
    db: Session,
    *,
    arabic_text: str,
    coptic_text: str,
    source_id: int,
    dialect_id: int | None,
    reviewer_id: int | None,
) -> ParallelSegment:
    normalized = normalize_arabic(arabic_text)
    existing = (
        db.query(ParallelSegment)
        .filter(
            ParallelSegment.normalized_arabic_text == normalized,
            ParallelSegment.coptic_text == coptic_text,
            ParallelSegment.review_status == RecordStatus.approved,
        )
        .first()
    )
    if existing:
        return existing
    segment = ParallelSegment(
        source_id=source_id,
        dialect_id=dialect_id,
        arabic_text=arabic_text,
        coptic_text=coptic_text,
        normalized_arabic_text=normalized,
        normalized_coptic_text=normalize_coptic(coptic_text) if coptic_text else None,
        alignment_score=1.0,
        arabic_embedding=embed_text(arabic_text),
        coptic_embedding=embed_text(coptic_text),
        sentence_embedding=embed_text(arabic_text),
        review_status=RecordStatus.approved,
        created_by=reviewer_id,
        reviewed_by=reviewer_id,
    )
    db.add(segment)
    db.flush()
    log_audit(db, user_id=reviewer_id, action="create", record=segment, new_data=_snapshot(segment))
    return segment
