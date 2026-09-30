from __future__ import annotations

from dataclasses import dataclass
from sqlalchemy.orm import Session

from app.models import Source, User
from app.models.enums import Role, SourceType


@dataclass(frozen=True)
class StandardSourceSpec:
    title: str
    author: str
    type: SourceType
    year: int | None
    url: str | None
    isbn: str | None
    notes: str


STANDARD_SOURCES: list[StandardSourceSpec] = [
    StandardSourceSpec(
        title="A Coptic Dictionary (Crum)",
        author="Walter Ewing Crum",
        type=SourceType.lexicon,
        year=1939,
        url="https://coptot.manuscriptroom.com/crum-coptic-dictionary",
        isbn="978-1592443017",
        notes="The standard historical Coptic lexicon covering Sahidic, Bohairic, Fayyumic, and Akhmimic dialects.",
    ),
    StandardSourceSpec(
        title="Comprehensive Coptic Lexicon (CCL)",
        author="Berlin-Brandenburg Academy (BBAW) & DDGLC Project",
        type=SourceType.lexicon,
        year=2020,
        url="https://doi.org/10.17169/refubium-27566",
        isbn=None,
        notes="TEI-XML open-access standard Coptic lexicon integrating Egyptian roots and Greek loanwords in Coptic.",
    ),
    StandardSourceSpec(
        title="قاموس اللغة القبطية المصرية (الدرة النفيسة)",
        author="إقلاديوس بك لبيب (Claudius Labib)",
        type=SourceType.lexicon,
        year=1905,
        url="https://archive.org/details/coptic-arabic-dictionary-claudius-labib",
        isbn=None,
        notes="المعجم القبطي العربي التاريخي المعتمد في مصر والمنشور بمطبعة عين شمس بالقاهرة.",
    ),
    StandardSourceSpec(
        title="A Greek-English Lexicon (LSJ)",
        author="Henry George Liddell & Robert Scott",
        type=SourceType.dictionary,
        year=1940,
        url="https://stephanus.tlg.uci.edu/lsj/",
        isbn="978-0198642268",
        notes="Standard reference for Greek loanwords occurring in Coptic literature and liturgical texts.",
    ),
    StandardSourceSpec(
        title="Dictionnaire Grec-Français (Bailly)",
        author="Anatole Bailly",
        type=SourceType.dictionary,
        year=1895,
        url="https://bailly.app/",
        isbn=None,
        notes="Standard dictionary of ancient Greek used in comparative scholarly lexical analyses.",
    ),
    StandardSourceSpec(
        title="معجم الكلمات القبطية ذات الأصل اليوناني",
        author="د. عادل معوض (Adel Moawad)",
        type=SourceType.lexicon,
        year=2003,
        url=None,
        isbn=None,
        notes="معجم متخصص في الألفاظ اليونانية الدخيلة على اللسان القبطي البحيري والصعيدي.",
    ),
    StandardSourceSpec(
        title="Open Biblical Coptic Corpus (Coptic Scriptorium)",
        author="Coptic SCRIPTORIUM Project",
        type=SourceType.bible,
        year=2020,
        url="https://copticscriptorium.org/",
        isbn=None,
        notes="Annotated and normalized parallel biblical and monastic corpus in Sahidic and Bohairic.",
    ),
]


def ensure_standard_sources(db: Session, admin_id: int | None = None) -> dict[str, Source]:
    """
    Ensure all scholarly standard references exist in the database with rich metadata.
    Returns a dictionary mapping source title to Source instance.
    """
    if admin_id is None:
        admin = db.query(User).filter(User.role == Role.admin).order_by(User.id).first()
        admin_id = admin.id if admin else None

    result: dict[str, Source] = {}
    for spec in STANDARD_SOURCES:
        source = (
            db.query(Source)
            .filter((Source.title == spec.title) | (Source.url == spec.url if spec.url else False))
            .first()
        )
        if source:
            source.title = spec.title
            source.author = spec.author
            source.type = spec.type
            source.year = spec.year
            source.url = spec.url
            source.isbn = spec.isbn
            source.notes = spec.notes
            if not source.created_by and admin_id:
                source.created_by = admin_id
        else:
            source = Source(
                title=spec.title,
                author=spec.author,
                type=spec.type,
                year=spec.year,
                url=spec.url,
                isbn=spec.isbn,
                notes=spec.notes,
                created_by=admin_id,
            )
            db.add(source)
            db.flush()
        result[spec.title] = source

    db.commit()
    return result
