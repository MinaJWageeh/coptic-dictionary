from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import ArabicSense, DictionaryEntry, SenseMapping, Source
from app.models.enums import PartOfSpeech, RecordStatus
from app.seed.run import seed
from app.services.deduplication import DeduplicationService
from app.services.import_pipeline import DictionaryImportPipeline
from app.services.sources import ensure_standard_sources, STANDARD_SOURCES
from app.services.translation import TranslationService
from tests.conftest import auth_header


def test_standard_reference_sources_metadata(db_session: Session) -> None:
    sources_map = ensure_standard_sources(db_session)

    assert len(sources_map) == len(STANDARD_SOURCES)
    assert "A Coptic Dictionary (Crum)" in sources_map
    crum = sources_map["A Coptic Dictionary (Crum)"]
    assert crum.author == "Walter Ewing Crum"
    assert crum.year == 1939
    assert crum.isbn == "978-1592443017"

    assert "Comprehensive Coptic Lexicon (CCL)" in sources_map
    ccl = sources_map["Comprehensive Coptic Lexicon (CCL)"]
    assert "refubium" in (ccl.url or "")

    assert "قاموس اللغة القبطية المصرية (الدرة النفيسة)" in sources_map
    labib = sources_map["قاموس اللغة القبطية المصرية (الدرة النفيسة)"]
    assert "إقلاديوس" in (labib.author or "")

    assert "A Greek-English Lexicon (LSJ)" in sources_map
    assert "Dictionnaire Grec-Français (Bailly)" in sources_map
    assert "معجم الكلمات القبطية ذات الأصل اليوناني" in sources_map


def test_csv_import_pipeline_with_deduplication(db_session: Session) -> None:
    sources = ensure_standard_sources(db_session)
    source = sources["A Coptic Dictionary (Crum)"]

    csv_data = """coptic,arabic,pos,dialect,definition,confidence,citation
ⲁⲅⲅⲉⲗⲟⲥ,ملاك,noun,bohairic,كائن نوراني مرسل من الله,0.95,Crum p. 2a
ⲁⲅⲅⲉⲗⲟⲥ,ملاك,noun,sahidic,ملاك ورسول سماوي,0.95,Crum p. 2a
ⲁⲅⲅⲉⲗⲟⲥ,ملاك,noun,bohairic,كائن نوراني,0.99,Second import citation
"""
    pipeline = DictionaryImportPipeline(db_session)
    stats = pipeline.import_csv(csv_data, default_source_id=source.id)

    assert stats.total_processed == 3
    # First bohairic created, second sahidic created, third bohairic reused!
    assert stats.entries_created == 2
    assert stats.entries_reused == 1
    # Arabic sense "ملاك" created once and reused for the other two!
    assert stats.senses_created == 1
    assert stats.senses_reused == 2
    assert stats.mappings_created == 2
    assert stats.mappings_updated == 1

    # Verify database state
    bohairic_entry = (
        db_session.query(DictionaryEntry)
        .filter(DictionaryEntry.coptic_text == "ⲁⲅⲅⲉⲗⲟⲥ", DictionaryEntry.notes.like("%Second import%"))
        .first()
    )
    assert bohairic_entry is not None
    assert "Crum p. 2a" in bohairic_entry.notes


def test_json_import_pipeline(db_session: Session) -> None:
    sources = ensure_standard_sources(db_session)
    source = sources["A Coptic Dictionary (Crum)"]

    json_data = """[
        {
            "coptic_text": "ⲥⲟⲛ",
            "arabic_lemma": "أخ",
            "part_of_speech": "noun",
            "dialect": "bohairic",
            "definition": "الأخ في النسب أو الروح",
            "confidence": 0.95,
            "transliteration": "son"
        },
        {
            "coptic_text": "ⲥⲱⲛⲓ",
            "arabic_lemma": "أخت",
            "part_of_speech": "noun",
            "dialect": "bohairic",
            "definition": "الأخت في النسب أو الروح",
            "confidence": 0.95,
            "transliteration": "soni"
        }
    ]"""
    pipeline = DictionaryImportPipeline(db_session)
    stats = pipeline.import_json(json_data, default_source_id=source.id)

    assert stats.total_processed == 2
    assert stats.entries_created == 2
    assert stats.senses_created == 2
    assert stats.mappings_created == 2

    # Query via translation service
    res = TranslationService(db_session).translate_word("أخ")
    assert res["input_type"] == "word"
    assert len(res["entries"]) > 0
    assert res["entries"][0]["coptic_word"] == "ⲥⲟⲛ"


def test_tei_xml_import_pipeline(db_session: Session) -> None:
    sources = ensure_standard_sources(db_session)
    source = sources["Comprehensive Coptic Lexicon (CCL)"]

    tei_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <TEI xmlns="http://www.tei-c.org/ns/1.0">
      <text>
        <body>
          <entry xml:id="ccl_entry_1">
            <form type="lemma">
              <orth xml:lang="cop">ⲣⲁϣⲓ</orth>
            </form>
            <gramGrp>
              <pos>verb</pos>
            </gramGrp>
            <usg type="dialect">bohairic</usg>
            <sense>
              <cit type="translation" xml:lang="ar">
                <quote>فرح</quote>
              </cit>
              <def xml:lang="ar">الفرح والابتهاج والسرور</def>
            </sense>
          </entry>
        </body>
      </text>
    </TEI>"""

    pipeline = DictionaryImportPipeline(db_session)
    stats = pipeline.import_tei_xml(tei_xml, default_source_id=source.id)

    assert stats.total_processed == 1
    assert stats.entries_created == 1
    assert stats.senses_created == 1
    assert stats.mappings_created == 1

    entry = db_session.query(DictionaryEntry).filter(DictionaryEntry.coptic_text == "ⲣⲁϣⲓ").one()
    assert entry.part_of_speech == PartOfSpeech.verb
    assert "ccl_entry_1" in entry.notes


def test_curated_lexicon_includes_essential_words(db_session: Session) -> None:
    seed(db_session)

    service = TranslationService(db_session)

    # 1. جندي (Soldier)
    soldier_res = service.translate_word("جندي")
    assert len(soldier_res["entries"]) > 0
    assert any(e["coptic_word"] == "ⲙⲁⲧⲟⲓ" for e in soldier_res["entries"])

    # 2. حارس (Guard)
    guard_res = service.translate_word("حارس")
    assert len(guard_res["entries"]) > 0
    assert any(e["coptic_word"] == "ⲣⲉϥϩⲁⲣⲉϩ" for e in guard_res["entries"])

    # 3. ملك (King)
    king_res = service.translate_word("ملك")
    assert len(king_res["entries"]) > 0
    coptic_words = {e["coptic_word"] for e in king_res["entries"]}
    assert "ⲟⲩⲣⲟ" in coptic_words or "ⲣⲣⲟ" in coptic_words

    # 4. كتاب (Book)
    book_res = service.translate_word("كتاب")
    assert len(book_res["entries"]) > 0
    assert any(e["coptic_word"] in {"ϫⲱⲙ", "ϫⲱⲱⲙⲉ"} for e in book_res["entries"])

    # 5. صلاة (Prayer)
    prayer_res = service.translate_word("صلاة")
    assert len(prayer_res["entries"]) > 0
    assert any(e["coptic_word"] in {"ⲉⲩⲭⲏ", "ϣⲗⲏⲗ"} for e in prayer_res["entries"])


def test_deduplication_audit_and_merge(db_session: Session) -> None:
    dedup = DeduplicationService(db_session)

    # Artificially insert duplicate Arabic senses with identical normalized lemma and pos
    source = Source(title="Temp Source")
    db_session.add(source)
    db_session.flush()

    s1 = ArabicSense(
        arabic_lemma="نور",
        normalized_arabic_lemma="نور",
        definition_ar="الضياء الأول",
        part_of_speech=PartOfSpeech.noun,
        source_id=source.id,
    )
    s2 = ArabicSense(
        arabic_lemma="نور",
        normalized_arabic_lemma="نور",
        definition_ar="الضياء الثاني المكرر",
        part_of_speech=PartOfSpeech.noun,
        source_id=source.id,
    )
    db_session.add_all([s1, s2])
    db_session.commit()

    audit = dedup.audit_duplicates()
    assert audit["duplicate_arabic_senses_count"] >= 1

    merged_count = dedup.merge_duplicate_arabic_senses()
    assert merged_count >= 1

    # After merge, no duplicates for 'نور' with noun POS
    post_count = (
        db_session.query(ArabicSense)
        .filter(ArabicSense.normalized_arabic_lemma == "نور", ArabicSense.part_of_speech == PartOfSpeech.noun)
        .count()
    )
    assert post_count == 1


def test_admin_api_import_and_deduplication_routes(client: TestClient) -> None:
    token_headers = auth_header(client, "admin@example.com")

    # 1. Test POST /admin/sources/ensure-standard
    res_sources = client.post("/admin/sources/ensure-standard", headers=token_headers)
    assert res_sources.status_code == 200
    assert len(res_sources.json()) >= len(STANDARD_SOURCES)

    # 2. Test POST /admin/import/dictionary (CSV)
    csv_payload = {
        "format": "csv",
        "content": "coptic,arabic,pos,definition\nⲡⲓⲥⲧⲓⲥ,إيمان,noun,الإيمان واليقين بالله\n",
        "default_dialect_code": "bohairic",
    }
    res_import = client.post("/admin/import/dictionary", json=csv_payload, headers=token_headers)
    assert res_import.status_code == 200
    data = res_import.json()
    assert data["total_processed"] == 1
    assert data["entries_created"] == 1
    assert data["senses_created"] == 1

    # 3. Test GET /admin/deduplication/audit
    res_audit = client.get("/admin/deduplication/audit", headers=token_headers)
    assert res_audit.status_code == 200
    assert "duplicate_coptic_entries_count" in res_audit.json()

    # 4. Test POST /admin/deduplication/merge
    res_merge = client.post("/admin/deduplication/merge", headers=token_headers)
    assert res_merge.status_code == 200
    assert "removed_redundant_senses" in res_merge.json()
