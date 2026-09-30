from __future__ import annotations

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_roles
from app.models import (
    ArabicSense,
    AuditLog,
    CorpusText,
    DictionaryEntry,
    GrammarRule,
    ParallelSegment,
    SenseMapping,
    Source,
    TranslationCandidate,
    TranslationRequest,
)
from app.models.enums import RecordStatus, Role
from app.models.identity import User
from app.schemas.admin import (
    ArabicSenseCreate,
    ArabicSenseRead,
    ArabicSenseUpdate,
    AuditLogRead,
    CorpusTextCreate,
    CorpusTextRead,
    CorpusTextUpdate,
    DeduplicationAuditResponse,
    DeduplicationMergeResponse,
    DictionaryImportPayload,
    DictionaryImportStats,
    DictionaryEntryCreate,
    DictionaryEntryUpdate,
    EvaluationDatasetItem,
    EvaluationMetricsResponse,
    WorkloadDashboardResponse,
    GrammarRuleCreate,
    GrammarRuleRead,
    GrammarRuleUpdate,
    ParallelSegmentCreate,
    ParallelSegmentUpdate,
    SenseMappingCreate,
    SenseMappingRead,
    SenseMappingUpdate,
    SourceCreate,
    SourceRead,
    SourceUpdate,
    TranslationCandidateRead,
    TranslationRequestRead,
    UserCreate,
    UserRead,
    UserUpdate,
)
from app.schemas.public import DictionaryEntryRead, ParallelSegmentRead
from app.services import admin as admin_service
from app.services.dictionary import DictionaryService

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(require_roles(Role.admin))],
)


@router.post("/dictionary", response_model=DictionaryEntryRead, status_code=status.HTTP_201_CREATED)
def create_dictionary_entry(
    payload: DictionaryEntryCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.admin)),
):
    return DictionaryService(db).create_entry(payload, user.id)


@router.get("/dictionary", response_model=list[DictionaryEntryRead])
def list_dictionary_entries(
    review_status: RecordStatus | None = RecordStatus.approved,
    db: Session = Depends(get_db),
):
    query = db.query(DictionaryEntry)
    if review_status:
        query = query.filter(DictionaryEntry.review_status == review_status)
    return query.order_by(DictionaryEntry.created_at.desc()).all()


@router.put("/dictionary/{entry_id}", response_model=DictionaryEntryRead)
def update_dictionary_entry(
    entry_id: int,
    payload: DictionaryEntryUpdate,
    db: Session = Depends(get_db),
):
    return DictionaryService(db).update_entry(entry_id, payload)


@router.delete("/dictionary/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_dictionary_entry(entry_id: int, db: Session = Depends(get_db)) -> Response:
    DictionaryService(db).delete_entry(entry_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/senses", status_code=status.HTTP_201_CREATED)
def create_sense(
    payload: ArabicSenseCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.admin)),
):
    return admin_service.create_arabic_sense(db, payload, user.id)


@router.get("/senses", response_model=list[ArabicSenseRead])
def list_senses(
    review_status: RecordStatus | None = RecordStatus.approved,
    db: Session = Depends(get_db),
):
    query = db.query(ArabicSense)
    if review_status:
        query = query.filter(ArabicSense.review_status == review_status)
    return query.order_by(ArabicSense.created_at.desc()).all()


@router.put("/senses/{sense_id}", response_model=ArabicSenseRead)
def update_sense(
    sense_id: int,
    payload: ArabicSenseUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.admin)),
):
    return admin_service.update_record(db, ArabicSense, sense_id, payload, user.id)


@router.delete("/senses/{sense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sense(
    sense_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.admin)),
) -> Response:
    admin_service.delete_record(db, ArabicSense, sense_id, user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/mappings", status_code=status.HTTP_201_CREATED)
def create_mapping(
    payload: SenseMappingCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.admin)),
):
    return admin_service.create_mapping(db, payload, user.id)


@router.get("/mappings", response_model=list[SenseMappingRead])
def list_mappings(
    review_status: RecordStatus | None = RecordStatus.approved,
    db: Session = Depends(get_db),
):
    query = db.query(SenseMapping)
    if review_status:
        query = query.filter(SenseMapping.review_status == review_status)
    return query.order_by(SenseMapping.created_at.desc()).all()


@router.put("/mappings/{mapping_id}", response_model=SenseMappingRead)
def update_mapping(
    mapping_id: int,
    payload: SenseMappingUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.admin)),
):
    return admin_service.update_record(db, SenseMapping, mapping_id, payload, user.id)


@router.delete("/mappings/{mapping_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_mapping(
    mapping_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.admin)),
) -> Response:
    admin_service.delete_record(db, SenseMapping, mapping_id, user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/corpus-texts", status_code=status.HTTP_201_CREATED)
def create_corpus_text(
    payload: CorpusTextCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.admin)),
):
    return admin_service.create_corpus_text(db, payload, user.id)


@router.get("/corpus-texts", response_model=list[CorpusTextRead])
def list_corpus_texts(
    review_status: RecordStatus | None = RecordStatus.approved,
    db: Session = Depends(get_db),
):
    query = db.query(CorpusText)
    if review_status:
        query = query.filter(CorpusText.review_status == review_status)
    return query.order_by(CorpusText.created_at.desc()).all()


@router.put("/corpus-texts/{corpus_id}", response_model=CorpusTextRead)
def update_corpus_text(
    corpus_id: int,
    payload: CorpusTextUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.admin)),
):
    return admin_service.update_record(db, CorpusText, corpus_id, payload, user.id)


@router.delete("/corpus-texts/{corpus_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_corpus_text(
    corpus_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.admin)),
) -> Response:
    admin_service.delete_record(db, CorpusText, corpus_id, user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/parallel-segments", response_model=ParallelSegmentRead, status_code=status.HTTP_201_CREATED)
def create_parallel_segment(
    payload: ParallelSegmentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.admin)),
):
    return admin_service.create_parallel_segment(db, payload, user.id)


@router.get("/parallel-segments", response_model=list[ParallelSegmentRead])
def list_parallel_segments(
    review_status: RecordStatus | None = RecordStatus.approved,
    db: Session = Depends(get_db),
):
    query = db.query(ParallelSegment)
    if review_status:
        query = query.filter(ParallelSegment.review_status == review_status)
    return query.order_by(ParallelSegment.created_at.desc()).all()


@router.put("/parallel-segments/{segment_id}", response_model=ParallelSegmentRead)
def update_parallel_segment(
    segment_id: int,
    payload: ParallelSegmentUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.admin)),
):
    return admin_service.update_record(db, ParallelSegment, segment_id, payload, user.id)


@router.delete("/parallel-segments/{segment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_parallel_segment(
    segment_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.admin)),
) -> Response:
    admin_service.delete_record(db, ParallelSegment, segment_id, user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/grammar-rules", status_code=status.HTTP_201_CREATED)
def create_grammar_rule(
    payload: GrammarRuleCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.admin)),
):
    return admin_service.create_grammar_rule(db, payload, user.id)


@router.get("/grammar-rules", response_model=list[GrammarRuleRead])
def list_grammar_rules(
    review_status: RecordStatus | None = RecordStatus.approved,
    db: Session = Depends(get_db),
):
    query = db.query(GrammarRule)
    if review_status:
        query = query.filter(GrammarRule.review_status == review_status)
    return query.order_by(GrammarRule.created_at.desc()).all()


@router.put("/grammar-rules/{rule_id}", response_model=GrammarRuleRead)
def update_grammar_rule(
    rule_id: int,
    payload: GrammarRuleUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.admin)),
):
    return admin_service.update_record(db, GrammarRule, rule_id, payload, user.id)


@router.delete("/grammar-rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_grammar_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.admin)),
) -> Response:
    admin_service.delete_record(db, GrammarRule, rule_id, user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/sources", response_model=SourceRead, status_code=status.HTTP_201_CREATED)
def create_source(
    payload: SourceCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.admin)),
):
    return admin_service.create_source(db, payload, user.id)


@router.get("/sources", response_model=list[SourceRead])
def list_sources(db: Session = Depends(get_db)):
    return db.query(Source).order_by(Source.created_at.desc()).all()


@router.put("/sources/{source_id}", response_model=SourceRead)
def update_source(
    source_id: int,
    payload: SourceUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.admin)),
):
    return admin_service.update_record(db, Source, source_id, payload, user.id)


@router.delete("/sources/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_source(
    source_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.admin)),
) -> Response:
    admin_service.delete_record(db, Source, source_id, user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    return admin_service.create_user(db, payload)


@router.get("/users", response_model=list[UserRead])
def list_users(db: Session = Depends(get_db)):
    return db.query(User).order_by(User.created_at.desc()).all()


@router.put("/users/{user_id}", response_model=UserRead)
def update_user(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.admin)),
):
    return admin_service.update_record(db, User, user_id, payload, user.id)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.admin)),
) -> Response:
    admin_service.delete_record(db, User, user_id, user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/audit-logs", response_model=list[AuditLogRead])
def list_audit_logs(db: Session = Depends(get_db)):
    return db.query(AuditLog).order_by(AuditLog.id.desc()).all()


@router.get("/translation-requests", response_model=list[TranslationRequestRead])
def list_translation_requests(db: Session = Depends(get_db)):
    return db.query(TranslationRequest).order_by(TranslationRequest.created_at.desc()).all()


@router.get("/translation-candidates", response_model=list[TranslationCandidateRead])
def list_translation_candidates(
    review_status: RecordStatus | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(TranslationCandidate)
    if review_status:
        query = query.filter(TranslationCandidate.review_status == review_status)
    return query.order_by(TranslationCandidate.created_at.desc()).all()


@router.post("/import/dictionary", response_model=DictionaryImportStats, status_code=status.HTTP_200_OK)
def import_dictionary_data(
    payload: DictionaryImportPayload,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.admin)),
):
    from app.services.import_pipeline import DictionaryImportPipeline

    # Ensure a default source exists if not specified
    source_id = payload.default_source_id
    if not source_id:
        src = db.query(Source).first()
        source_id = src.id if src else 1

    pipeline = DictionaryImportPipeline(db, admin_id=user.id)
    fmt = payload.format.lower().strip()
    if fmt in {"csv", "tsv"}:
        stats = pipeline.import_csv(
            payload.content,
            default_dialect=payload.default_dialect_code,
            default_source_id=source_id,
            review_status=payload.default_review_status,
        )
    elif fmt in {"json", "jsonl"}:
        stats = pipeline.import_json(
            payload.content,
            default_dialect=payload.default_dialect_code,
            default_source_id=source_id,
            review_status=payload.default_review_status,
        )
    elif fmt in {"tei", "xml", "tei_xml"}:
        stats = pipeline.import_tei_xml(
            payload.content,
            default_dialect=payload.default_dialect_code,
            default_source_id=source_id,
            review_status=payload.default_review_status,
        )
    else:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported format '{payload.format}'. Supported: csv, json, tei_xml",
        )

    return stats


@router.get("/deduplication/audit", response_model=DeduplicationAuditResponse)
def audit_database_duplicates(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.admin)),
):
    from app.services.deduplication import DeduplicationService
    dedup = DeduplicationService(db)
    return dedup.audit_duplicates()


@router.post("/deduplication/merge", response_model=DeduplicationMergeResponse)
def merge_database_duplicates(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.admin)),
):
    from app.services.deduplication import DeduplicationService
    dedup = DeduplicationService(db)
    count = dedup.merge_duplicate_arabic_senses()
    return {
        "removed_redundant_senses": count,
        "message": f"Successfully merged {count} redundant Arabic senses.",
    }


@router.post("/sources/ensure-standard", response_model=list[SourceRead])
def ensure_standard_reference_sources(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.admin)),
):
    from app.services.sources import ensure_standard_sources
    source_map = ensure_standard_sources(db, admin_id=user.id)
    return list(source_map.values())


@router.get("/evaluation/metrics", response_model=EvaluationMetricsResponse)
def get_evaluation_metrics(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.admin)),
):
    from app.services.evaluation import EvaluationDatasetService
    service = EvaluationDatasetService(db)
    return service.compute_metrics()


@router.get("/evaluation/dataset")
def export_evaluation_dataset(
    format: str = "json",
    status_filter: str | None = None,
    limit: int = 1000,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.admin)),
):
    from app.services.evaluation import EvaluationDatasetService
    service = EvaluationDatasetService(db)

    stat = None
    if status_filter:
        try:
            stat = RecordStatus(status_filter)
        except ValueError:
            pass

    if format == "jsonl":
        ndjson_content = service.export_jsonl(status=stat, limit=limit)
        return Response(
            content=ndjson_content,
            media_type="application/x-ndjson",
            headers={"Content-Disposition": "attachment; filename=coptic_eval_dataset.jsonl"},
        )
    elif format == "csv":
        csv_content = service.export_csv(status=stat, limit=limit)
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=coptic_eval_dataset.csv"},
        )
    else:
        return service.get_evaluation_items(status=stat, limit=limit)


@router.get("/workload", response_model=WorkloadDashboardResponse)
def get_reviewer_workload_dashboard(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.admin, Role.reviewer)),
):
    from sqlalchemy import func
    from app.models import TranslationCandidate, TranslationRequest, TranslationReview

    pending_drafts = db.query(func.count(TranslationCandidate.id)).filter(
        TranslationCandidate.review_status == RecordStatus.draft
    ).scalar() or 0
    approved_cands = db.query(func.count(TranslationCandidate.id)).filter(
        TranslationCandidate.review_status == RecordStatus.approved
    ).scalar() or 0
    rejected_cands = db.query(func.count(TranslationCandidate.id)).filter(
        TranslationCandidate.review_status == RecordStatus.rejected
    ).scalar() or 0
    total_requests = db.query(func.count(TranslationRequest.id)).scalar() or 0

    avg_conf = db.query(func.avg(TranslationCandidate.confidence)).scalar() or 0.0

    # Reviewer workload statistics
    reviewers = db.query(User).filter(User.role.in_([Role.reviewer, Role.admin])).all()
    reviewer_stats = []
    for r in reviewers:
        reviews = db.query(TranslationReview).filter(TranslationReview.reviewer_id == r.id).all()
        appr = sum(1 for x in reviews if x.review_status == RecordStatus.approved and not x.corrected_text)
        corr = sum(1 for x in reviews if x.review_status == RecordStatus.approved and x.corrected_text)
        rej = sum(1 for x in reviews if x.review_status == RecordStatus.rejected)
        last_rev = max([x.created_at for x in reviews], default=None) if reviews else None

        reviewer_stats.append({
            "user_id": r.id,
            "display_name": r.display_name,
            "email": r.email,
            "approved_count": appr,
            "corrected_count": corr,
            "rejected_count": rej,
            "total_reviewed": len(reviews),
            "last_review_at": last_rev.isoformat() if last_rev else None,
        })

    return {
        "total_pending_drafts": pending_drafts,
        "total_approved_candidates": approved_cands,
        "total_rejected_candidates": rejected_cands,
        "total_translation_requests": total_requests,
        "reviewers": reviewer_stats,
        "average_confidence": round(float(avg_conf), 4),
    }


@router.get("/export/dictionary")
def export_dictionary_bulk(
    format: str = "json",
    dialect_id: int | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.admin)),
):
    import csv
    import io
    import json
    query = db.query(DictionaryEntry)
    if dialect_id:
        query = query.filter(DictionaryEntry.dialect_id == dialect_id)
    entries = query.all()

    if format == "csv":
        output = io.StringIO()
        fieldnames = ["id", "coptic_text", "transliteration", "part_of_speech", "dialect_id", "source_id", "review_status", "notes"]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        for e in entries:
            writer.writerow({
                "id": e.id,
                "coptic_text": e.coptic_text,
                "transliteration": e.transliteration or "",
                "part_of_speech": e.part_of_speech.value if hasattr(e.part_of_speech, "value") else str(e.part_of_speech),
                "dialect_id": e.dialect_id,
                "source_id": e.source_id,
                "review_status": e.review_status.value if hasattr(e.review_status, "value") else str(e.review_status),
                "notes": e.notes or "",
            })
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=dictionary_export.csv"},
        )
    else:
        results = [
            {
                "id": e.id,
                "coptic_text": e.coptic_text,
                "normalized_coptic_text": e.normalized_coptic_text,
                "transliteration": e.transliteration,
                "part_of_speech": e.part_of_speech.value if hasattr(e.part_of_speech, "value") else str(e.part_of_speech),
                "dialect_id": e.dialect_id,
                "source_id": e.source_id,
                "review_status": e.review_status.value if hasattr(e.review_status, "value") else str(e.review_status),
                "notes": e.notes,
            }
            for e in entries
        ]
        return Response(
            content=json.dumps(results, ensure_ascii=False, indent=2),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=dictionary_export.json"},
        )


@router.get("/export/segments")
def export_parallel_segments_bulk(
    format: str = "json",
    dialect_id: int | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.admin)),
):
    import csv
    import io
    import json
    query = db.query(ParallelSegment)
    if dialect_id:
        query = query.filter(ParallelSegment.dialect_id == dialect_id)
    segments = query.all()

    if format == "csv":
        output = io.StringIO()
        fieldnames = ["id", "arabic_text", "coptic_text", "dialect_id", "source_id", "review_status"]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        for s in segments:
            writer.writerow({
                "id": s.id,
                "arabic_text": s.arabic_text,
                "coptic_text": s.coptic_text or "",
                "dialect_id": s.dialect_id or "",
                "source_id": s.source_id,
                "review_status": s.review_status.value if hasattr(s.review_status, "value") else str(s.review_status),
            })
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=parallel_segments_export.csv"},
        )
    else:
        results = [
            {
                "id": s.id,
                "arabic_text": s.arabic_text,
                "normalized_arabic_text": s.normalized_arabic_text,
                "coptic_text": s.coptic_text,
                "normalized_coptic_text": s.normalized_coptic_text,
                "dialect_id": s.dialect_id,
                "source_id": s.source_id,
                "review_status": s.review_status.value if hasattr(s.review_status, "value") else str(s.review_status),
            }
            for s in segments
        ]
        return Response(
            content=json.dumps(results, ensure_ascii=False, indent=2),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=parallel_segments_export.json"},
        )

