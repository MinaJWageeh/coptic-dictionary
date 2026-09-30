from __future__ import annotations

import csv
import io
import json
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Any
from sqlalchemy.orm import Session

from app.models import Dialect, Source, User
from app.models.enums import PartOfSpeech, RecordStatus, Role, SourceType
from app.services.coptic_nmt_import import POS_ALIASES, romanize_coptic
from app.services.deduplication import DeduplicationService
from app.services.sources import ensure_standard_sources


@dataclass
class ImportStats:
    total_processed: int = 0
    entries_created: int = 0
    entries_reused: int = 0
    senses_created: int = 0
    senses_reused: int = 0
    mappings_created: int = 0
    mappings_updated: int = 0
    errors: list[str] = field(default_factory=list)


class DictionaryImportPipeline:
    def __init__(self, db: Session, admin_id: int | None = None):
        self.db = db
        if admin_id is None:
            admin = db.query(User).filter(User.role == Role.admin).order_by(User.id).first()
            admin_id = admin.id if admin else None
        self.admin_id = admin_id
        self.dedup = DeduplicationService(db)
        self._dialects_by_code: dict[str, Dialect] = {
            d.code.lower(): d for d in db.query(Dialect).all()
        }

    def _resolve_dialect(self, dialect_val: Any, default_code: str = "bohairic") -> int:
        if isinstance(dialect_val, int):
            return dialect_val
        code = str(dialect_val or default_code).strip().lower()
        if code in self._dialects_by_code:
            return self._dialects_by_code[code].id
        # Fallback or create if unknown
        dialect = Dialect(code=code, name=code.capitalize())
        self.db.add(dialect)
        self.db.flush()
        self._dialects_by_code[code] = dialect
        return dialect.id

    def _parse_pos(self, pos_val: Any) -> PartOfSpeech:
        raw = str(pos_val or "other").strip().lower()
        return POS_ALIASES.get(raw, PartOfSpeech.other)

    def import_record(
        self,
        *,
        coptic_text: str,
        arabic_lemma: str,
        part_of_speech: PartOfSpeech | str = PartOfSpeech.noun,
        definition_ar: str | None = None,
        dialect_code: str = "bohairic",
        source_id: int,
        transliteration: str | None = None,
        confidence: float = 0.95,
        example_coptic: str | None = None,
        example_arabic: str | None = None,
        notes: str | None = None,
        is_primary: bool = True,
        review_status: RecordStatus = RecordStatus.approved,
        stats: ImportStats,
    ) -> None:
        coptic_clean = coptic_text.strip()
        arabic_clean = arabic_lemma.strip()
        if not coptic_clean or not arabic_clean:
            stats.errors.append(f"Skipping empty entry: coptic='{coptic_clean}', arabic='{arabic_clean}'")
            return

        pos = part_of_speech if isinstance(part_of_speech, PartOfSpeech) else self._parse_pos(part_of_speech)
        dialect_id = self._resolve_dialect(dialect_code)
        if not transliteration:
            transliteration = romanize_coptic(coptic_clean)

        stats.total_processed += 1

        # 1. Coptic Dictionary Entry with Deduplication
        entry_res = self.dedup.find_or_create_coptic_entry(
            coptic_text=coptic_clean,
            dialect_id=dialect_id,
            part_of_speech=pos,
            source_id=source_id,
            transliteration=transliteration,
            notes=notes,
            example_sentence=example_coptic,
            review_status=review_status,
            admin_id=self.admin_id,
        )
        if entry_res.is_created:
            stats.entries_created += 1
        else:
            stats.entries_reused += 1

        # 2. Arabic Sense with Deduplication
        def_ar = definition_ar.strip() if definition_ar else arabic_clean
        sense_res = self.dedup.find_or_create_arabic_sense(
            arabic_lemma=arabic_clean,
            definition_ar=def_ar,
            part_of_speech=pos,
            source_id=source_id,
            example_ar=example_arabic,
            review_status=review_status,
            admin_id=self.admin_id,
        )
        if sense_res.is_created:
            stats.senses_created += 1
        else:
            stats.senses_reused += 1

        # 3. Sense Mapping with Deduplication
        mapping_res = self.dedup.find_or_create_sense_mapping(
            arabic_sense_id=sense_res.sense.id,
            dictionary_entry_id=entry_res.entry.id,
            confidence=confidence,
            usage_note=notes,
            is_primary=is_primary,
            review_status=review_status,
            admin_id=self.admin_id,
        )
        if mapping_res.is_created:
            stats.mappings_created += 1
        elif mapping_res.is_updated:
            stats.mappings_updated += 1

    def import_csv(
        self,
        content: str | io.StringIO,
        *,
        default_dialect: str = "bohairic",
        default_source_id: int,
        review_status: RecordStatus = RecordStatus.approved,
    ) -> ImportStats:
        """Import dictionary entries from CSV / TSV text."""
        stats = ImportStats()
        if isinstance(content, str):
            stream = io.StringIO(content.strip())
        else:
            stream = content

        # Detect dialect / delimiter
        sample = stream.read(2048)
        stream.seek(0)
        delimiter = "\t" if "\t" in sample and sample.count("\t") > sample.count(",") else ","

        reader = csv.DictReader(stream, delimiter=delimiter)
        for row in reader:
            # Map column names flexibly
            coptic = row.get("coptic") or row.get("coptic_text") or row.get("coptic_word") or ""
            arabic = row.get("arabic") or row.get("arabic_lemma") or row.get("meaning") or ""
            pos = row.get("pos") or row.get("part_of_speech") or "noun"
            definition = row.get("definition") or row.get("definition_ar") or arabic
            dialect = row.get("dialect") or row.get("dialect_code") or default_dialect
            translit = row.get("transliteration") or row.get("translit") or None
            notes = row.get("notes") or row.get("citation") or None
            example_cop = row.get("example_coptic") or row.get("example") or None
            example_ar = row.get("example_arabic") or row.get("example_ar") or None

            try:
                confidence = float(row.get("confidence", 0.95))
            except ValueError:
                confidence = 0.95

            self.import_record(
                coptic_text=coptic,
                arabic_lemma=arabic,
                part_of_speech=pos,
                definition_ar=definition,
                dialect_code=dialect,
                source_id=default_source_id,
                transliteration=translit,
                confidence=confidence,
                example_coptic=example_cop,
                example_arabic=example_ar,
                notes=notes,
                review_status=review_status,
                stats=stats,
            )

        self.db.commit()
        return stats

    def import_json(
        self,
        content: str,
        *,
        default_dialect: str = "bohairic",
        default_source_id: int,
        review_status: RecordStatus = RecordStatus.approved,
    ) -> ImportStats:
        """Import dictionary entries from JSON array or JSONL lines."""
        stats = ImportStats()
        content = content.strip()
        items: list[dict[str, Any]] = []

        if content.startswith("["):
            items = json.loads(content)
        else:
            # Try JSONL
            for line in content.splitlines():
                line = line.strip()
                if line:
                    items.append(json.loads(line))

        for item in items:
            coptic = item.get("coptic_text") or item.get("coptic") or ""
            arabic = item.get("arabic_lemma") or item.get("arabic") or ""
            pos = item.get("part_of_speech") or item.get("pos") or "noun"
            definition = item.get("definition_ar") or item.get("definition") or arabic
            dialect = item.get("dialect_code") or item.get("dialect") or default_dialect
            translit = item.get("transliteration") or item.get("translit") or None
            notes = item.get("notes") or item.get("citation") or None
            confidence = float(item.get("confidence", 0.95))
            example_cop = item.get("example_coptic") or item.get("example_sentence") or None
            example_ar = item.get("example_arabic") or item.get("example_ar") or None

            self.import_record(
                coptic_text=coptic,
                arabic_lemma=arabic,
                part_of_speech=pos,
                definition_ar=definition,
                dialect_code=dialect,
                source_id=default_source_id,
                transliteration=translit,
                confidence=confidence,
                example_coptic=example_cop,
                example_arabic=example_ar,
                notes=notes,
                review_status=review_status,
                stats=stats,
            )

        self.db.commit()
        return stats

    def import_tei_xml(
        self,
        xml_content: str,
        *,
        default_dialect: str = "sahidic",
        default_source_id: int,
        review_status: RecordStatus = RecordStatus.approved,
    ) -> ImportStats:
        """
        Import dictionary entries from TEI-XML (TEI-P5 standard lexicon format used by Kellia / CCL).
        Parses <entry>, <form><orth>, <gramGrp><pos>, <sense><cit><quote>, <def>.
        """
        stats = ImportStats()
        root = ET.fromstring(xml_content)

        entries = root.findall(".//{*}entry")
        if not entries:
            entries = root.findall(".//entry")
        if not entries:
            entries = root.findall(".//{*}entryFree")
        if not entries:
            entries = root.findall(".//entryFree")
        if not entries and (root.tag.endswith("entry") or root.tag == "entry"):
            entries = [root]

        for entry_el in entries:
            # Find Coptic orthography
            coptic_el = entry_el.find(".//{*}orth")
            if coptic_el is None:
                coptic_el = entry_el.find(".//orth")
            coptic_text = coptic_el.text.strip() if coptic_el is not None and coptic_el.text else ""

            # Find POS
            pos_el = entry_el.find(".//{*}pos")
            if pos_el is None:
                pos_el = entry_el.find(".//pos")
            pos_text = pos_el.text.strip() if pos_el is not None and pos_el.text else "noun"

            # Find dialect (e.g. <usg type="dialect">)
            dialect_el = entry_el.find(".//{*}usg")
            if dialect_el is None:
                dialect_el = entry_el.find(".//usg")
            dialect_code = dialect_el.text.strip() if dialect_el is not None and dialect_el.text else default_dialect

            # Find Arabic senses
            arabic_texts: list[tuple[str, str]] = []
            senses = entry_el.findall(".//{*}sense")
            if not senses:
                senses = entry_el.findall(".//sense")
            if not senses:
                senses = [entry_el]
            for sense_el in senses:
                lemma = ""
                meaning = ""

                for el in sense_el.iter():
                    tag = el.tag.split("}")[-1] if "}" in el.tag else el.tag
                    if tag == "cit":
                        for q in el.iter():
                            q_tag = q.tag.split("}")[-1] if "}" in q.tag else q.tag
                            if q_tag == "quote" and q.text and q.text.strip():
                                lemma = q.text.strip()
                                break
                    elif tag == "def" and el.text and el.text.strip():
                        meaning = el.text.strip()
                        if not lemma:
                            lemma = meaning

                if lemma:
                    arabic_texts.append((lemma, meaning or lemma))

            # Citations / reference id
            ref_id = entry_el.get("{http://www.w3.org/XML/1998/namespace}id") or entry_el.get("id") or ""
            notes = f"TEI Entry ID: {ref_id}" if ref_id else "Imported from TEI-XML Lexicon"

            if coptic_text and arabic_texts:
                for lemma, definition in arabic_texts:
                    self.import_record(
                        coptic_text=coptic_text,
                        arabic_lemma=lemma,
                        part_of_speech=pos_text,
                        definition_ar=definition,
                        dialect_code=dialect_code,
                        source_id=default_source_id,
                        notes=notes,
                        review_status=review_status,
                        stats=stats,
                    )
            elif coptic_text:
                stats.errors.append(f"Entry {coptic_text} (ID: {ref_id}) lacked Arabic definition in TEI.")

        self.db.commit()
        return stats
