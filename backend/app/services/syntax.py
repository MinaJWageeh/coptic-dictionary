"""
Coptic Syntax & Linguistic Grammar Engine (Phase 2 - Linguistic Depth).
Handles:
1. Sentence-Type Detection (Nominal, Verbal, Negative).
2. Verb Conjugation across tenses and persons (Present I, Perfect I, Future I).
3. Gender and Number Agreement for articles, copulas, and adjectives.
4. Dialect-specific priorities (Bohairic, Sahidic, Fayyumic).
5. Genitive, Object, Relative, and Conjunction linkers.
"""
from dataclasses import dataclass, field
from app.services.morphology import (
    CopticNumerals,
    GenitiveLinker,
    GrammaticalGender,
    GrammaticalNumber,
    GrammaticalPerson,
    GrammaticalTense,
    NounDeclension,
    ObjectMarker,
    VerbConjugator,
)
from app.services.sentence_analysis import NegationKind, SentenceType, SentenceTypeDetector
from app.services.text import normalize_arabic

# Labial consonants in Bohairic that turn ⲛ̀- into ⲙ̀-
_LABIALS_BOHAIRIC = ("ⲃ", "ⲙ", "ⲡ", "ⲫ", "ⲯ", "Ⲃ", "Ⲙ", "Ⲡ", "Ⲫ", "Ⲯ")

# Transitive verbs in Arabic that require an object linker (ⲙ̀- / ⲛ̀-) before a definite object
_TRANSITIVE_VERBS = {
    "احب", "يحب", "نحب", "يعبد", "نعبد", "سجد", "يسجد", "نسجد", "سبح", "يسبح",
    "نسبح", "بارك", "يبارك", "نبارك", "صنع", "يصنع", "خلق", "يخلق", "اعطى",
    "يعطي", "اخذ", "ياخذ", "عرف", "يعرف", "خلص", "يخلص", "طلب", "يطلب",
    "راى", "يرى", "سمع", "يسمع", "حفظ", "يحفظ", "غفر", "يغفر", "قبل", "يقبل"
}

_COPULA_WORDS_AR: set[str] = {
    "اكون", "أكون", "تكون", "يكون", "نكون", "تكونوا", "يكونوا", "تكونون", "يكونون"
}

_ALL_VERBS = (_TRANSITIVE_VERBS | {
    "كان", "صار", "يصير", "قال", "يقول", "ارحم", "يرحم",
    "صلى", "يصلي", "نصلي", "اصلي", "تصلي",
    "شكر", "يشكر", "نشكر", "اشكر",
    "قام", "يقوم", "مات", "يموت", "اتى", "ياتي", "ولد", "يولد"
}) - _COPULA_WORDS_AR

_GENITIVE_HEAD_WORDS = {
    "ابن", "خبز", "ملك", "رب", "نور", "كنيسة", "صلاة", "كلمة", "روح", "دم",
    "جسد", "بيت", "باب", "طريق", "حق", "حياة", "ارض", "أرض", "مجد", "اسم",
    "شعب", "سر", "تاج", "سيد", "شمس", "ينبوع", "عهد", "ذبيحة", "قربان", "راعي",
    "قوة", "سلطان", "ملكوت", "عرش", "كرسي", "شريعة", "وصية", "سلام", "بركة", "نعمة",
    "حارس", "جندي", "مدينة", "قرية"
}

# Gendered Adjectives with agreement across dialects
_GENDERED_ADJECTIVE_MAP = {
    "صالح": {
        "bohairic": {"m": "ⲉⲑⲛⲁⲛⲉϥ", "f": "ⲉⲑⲛⲁⲛⲉⲥ", "pl": "ⲉⲑⲛⲁⲛⲱⲟⲩ"},
        "sahidic": {"m": "ⲉⲧⲛⲁⲛⲟⲩϥ", "f": "ⲉⲧⲛⲁⲛⲟⲩⲥ", "pl": "ⲉⲧⲛⲁⲛⲟⲩⲟⲩ"},
        "fayyumic": {"m": "ⲉⲧⲛⲁⲛⲟⲩϥ", "f": "ⲉⲧⲛⲁⲛⲟⲩⲥ", "pl": "ⲉⲧⲛⲁⲛⲟⲩⲟⲩ"},
    },
    "القدوس": {
        "bohairic": {"m": "ⲉⲑⲟⲩⲁⲃ", "f": "ⲉⲑⲟⲩⲁⲃ", "pl": "ⲉⲑⲟⲩⲁⲃ"},
        "sahidic": {"m": "ⲉⲧⲟⲩⲁⲁⲃ", "f": "ⲉⲧⲟⲩⲁⲁⲃ", "pl": "ⲉⲧⲟⲩⲁⲁⲃ"},
        "fayyumic": {"m": "ⲉⲧⲟⲩⲁⲃ", "f": "ⲉⲧⲟⲩⲁⲃ", "pl": "ⲉⲧⲟⲩⲁⲃ"},
    },
    "قدوس": {
        "bohairic": {"m": "ⲉⲑⲟⲩⲁⲃ", "f": "ⲉⲑⲟⲩⲁⲃ", "pl": "ⲉⲑⲟⲩⲁⲃ"},
        "sahidic": {"m": "ⲉⲧⲟⲩⲁⲁⲃ", "f": "ⲉⲧⲟⲩⲁⲁⲃ", "pl": "ⲉⲧⲟⲩⲁⲁⲃ"},
        "fayyumic": {"m": "ⲉⲧⲟⲩⲁⲃ", "f": "ⲉⲧⲟⲩⲁⲃ", "pl": "ⲉⲧⲟⲩⲁⲃ"},
    },
    "القدس": {
        "bohairic": {"m": "ⲉⲑⲟⲩⲁⲃ", "f": "ⲉⲑⲟⲩⲁⲃ", "pl": "ⲉⲑⲟⲩⲁⲃ"},
        "sahidic": {"m": "ⲉⲧⲟⲩⲁⲁⲃ", "f": "ⲉⲧⲟⲩⲁⲁⲃ", "pl": "ⲉⲧⲟⲩⲁⲁⲃ"},
        "fayyumic": {"m": "ⲉⲧⲟⲩⲁⲃ", "f": "ⲉⲧⲟⲩⲁⲃ", "pl": "ⲉⲧⲟⲩⲁⲃ"},
    },
    "قدس": {
        "bohairic": {"m": "ⲉⲑⲟⲩⲁⲃ", "f": "ⲉⲑⲟⲩⲁⲃ", "pl": "ⲉⲑⲟⲩⲁⲃ"},
        "sahidic": {"m": "ⲉⲧⲟⲩⲁⲁⲃ", "f": "ⲉⲧⲟⲩⲁⲁⲃ", "pl": "ⲉⲧⲟⲩⲁⲁⲃ"},
        "fayyumic": {"m": "ⲉⲧⲟⲩⲁⲃ", "f": "ⲉⲧⲟⲩⲁⲃ", "pl": "ⲉⲧⲟⲩⲁⲃ"},
    },
    "عظيم": {
        "bohairic": {"m": "ⲛ̀ⲛⲓϣϯ", "f": "ⲛ̀ⲛⲓϣϯ", "pl": "ⲛ̀ⲛⲓϣϯ"},
        "sahidic": {"m": "ⲛ̄ⲛⲟϭ", "f": "ⲛ̄ⲛⲟϭ", "pl": "ⲛ̄ⲛⲟϭ"},
        "fayyumic": {"m": "ⲛ̄ⲛⲟϭ", "f": "ⲛ̄ⲛⲟϭ", "pl": "ⲛ̄ⲛⲟϭ"},
    },
    "مبارك": {
        "bohairic": {"m": "ⲉⲧⲥⲙⲁⲣⲱⲟⲩⲧ", "f": "ⲉⲧⲥⲙⲁⲣⲱⲟⲩⲧ", "pl": "ⲉⲧⲥⲙⲁⲣⲱⲟⲩⲧ"},
        "sahidic": {"m": "ⲉⲧⲥⲙⲁⲙⲁⲁⲧ", "f": "ⲉⲧⲥⲙⲁⲙⲁⲁⲧ", "pl": "ⲉⲧⲥⲙⲁⲙⲁⲁⲧ"},
        "fayyumic": {"m": "ⲉⲧⲥⲙⲁⲙⲁⲧ", "f": "ⲉⲧⲥⲙⲁⲙⲁⲧ", "pl": "ⲉⲧⲥⲙⲁⲙⲁⲧ"},
    },
    "حي": {
        "bohairic": {"m": "ⲉⲧⲟⲛϧ", "f": "ⲉⲧⲟⲛϧ", "pl": "ⲉⲧⲟⲛϧ"},
        "sahidic": {"m": "ⲉⲧⲟⲛϩ", "f": "ⲉⲧⲟⲛϩ", "pl": "ⲉⲧⲟⲛϩ"},
        "fayyumic": {"m": "ⲉⲧⲟⲛϩ", "f": "ⲉⲧⲟⲛϩ", "pl": "ⲉⲧⲟⲛϩ"},
    },
    "حقيقي": {
        "bohairic": {"m": "ⲛ̀ⲧⲁⲫⲙⲏⲓ", "f": "ⲛ̀ⲧⲁⲫⲙⲏⲓ", "pl": "ⲛ̀ⲧⲁⲫⲙⲏⲓ"},
        "sahidic": {"m": "ⲙ̄ⲙⲉ", "f": "ⲙ̄ⲙⲉ", "pl": "ⲙ̄ⲙⲉ"},
        "fayyumic": {"m": "ⲙ̄ⲙⲉ", "f": "ⲙ̄ⲙⲉ", "pl": "ⲙ̄ⲙⲉ"},
    },
    "قوي": {
        "bohairic": {"m": "ⲉⲧϫⲟⲣ", "f": "ⲉⲧϫⲟⲣ", "pl": "ⲉⲧϫⲟⲣ"},
        "sahidic": {"m": "ⲉⲧϫⲟⲟⲣ", "f": "ⲉⲧϫⲟⲟⲣ", "pl": "ⲉⲧϫⲟⲟⲣ"},
        "fayyumic": {"m": "ⲉⲧϫⲟⲗ", "f": "ⲉⲧϫⲟⲗ", "pl": "ⲉⲧϫⲟⲗ"},
    },
}

# Root-word guards to avoid falsely stripping attached prepositions
_ROOT_B_WORDS = {
    "باب", "بيت", "بركة", "بركه", "بحر", "بستان", "بريء", "برئ", "بلد",
    "بخور", "بشارة", "بشاره", "بطرس", "بولس", "بشر", "بين", "بدء", "بداءة",
    "بداءه", "بكر", "بطل", "بناء", "بعيد", "بصير", "باكر", "بر", "بصيرة",
    "بصره", "بعثة", "بعثه", "برج", "بنيان", "بائس", "بستاني", "بذار", "بذرة",
    "بذره", "بئر", "بروق", "برد"
}

_ROOT_L_WORDS = {
    "لحم", "لبن", "لسان", "ليل", "ليلة", "ليله", "لص", "لوح", "لهب", "لؤلؤ",
    "لؤلؤة", "لؤلؤه", "لقمة", "لقمه", "لجام", "لحية", "لحيه"
}

# Prepositions by dialect
_PREPOSITIONS_BY_DIALECT = {
    "bohairic": {
        "في": "ϧⲉⲛ", "ب": "ϧⲉⲛ", "بـ": "ϧⲉⲛ",
        "على": "ϩⲓϫⲉⲛ", "علي": "ϩⲓϫⲉⲛ",
        "من": "ⲉ̀ⲃⲟⲗ ϧⲉⲛ",
        "الي": "ⲉ̀", "إلى": "ⲉ̀", "الى": "ⲉ̀", "ل": "ⲉ̀", "لـ": "ⲉ̀", "نحو": "ⲉ̀", "صوب": "ⲉ̀",
        "مع": "ⲛⲉⲙ",
        "عند": "ϧⲁⲧⲉⲛ", "لدى": "ϧⲁⲧⲉⲛ", "لدي": "ϧⲁⲧⲉⲛ",
        "تحت": "ϧⲁ",
        "فوق": "ⲉ̀ϩⲣⲏⲓ ⲉ̀ϫⲉⲛ",
        "امام": "ⲙ̀ⲡⲉⲙ̀ⲑⲟ ⲛ̀", "أمام": "ⲙ̀ⲡⲉⲙ̀ⲑⲟ ⲛ̀", "قدام": "ⲙ̀ⲡⲉⲙ̀ⲑⲟ ⲛ̀",
        "وراء": "ⲥⲁⲙⲉⲛϩⲏⲧ", "خلف": "ⲥⲁⲙⲉⲛϩⲏⲧ",
        "قبل": "ϧⲁϫⲱ",
        "بعد": "ⲙⲉⲛⲉⲛⲥⲁ",
        "بين": "ⲟⲩⲧⲉ",
        "لاجل": "ⲉⲑⲃⲉ", "لأجل": "ⲉⲑⲃⲉ", "بسبب": "ⲉⲑⲃⲉ", "عن": "ⲉⲑⲃⲉ",
        "حتى": "ϣⲁ", "حتي": "ϣⲁ",
        "بدون": "ⲁϭⲛⲉ", "بغير": "ⲁϭⲛⲉ", "دون": "ⲁϭⲛⲉ",
        "مثل": "ⲙ̀ⲫⲣⲏϯ ⲛ̀", "ك": "ⲙ̀ⲫⲣⲏϯ ⲛ̀", "كـ": "ⲙ̀ⲫⲣⲏϯ ⲛ̀",
        "حسب": "ⲕⲁⲧⲁ", "وفق": "ⲕⲁⲧⲁ",
        "بواسطة": "ⲉ̀ⲃⲟⲗ ϩⲓⲧⲉⲛ", "خلال": "ⲉ̀ⲃⲟⲗ ϩⲓⲧⲉⲛ",
        "حول": "ⲕⲱϯ ⲉ̀",
    },
    "sahidic": {
        "في": "ϩⲛ̄", "ب": "ϩⲛ̄", "بـ": "ϩⲛ̄",
        "على": "ⲉϫⲛ̄", "علي": "ⲉϫⲛ̄",
        "من": "ⲉⲃⲟⲗ ϩⲛ̄",
        "الي": "ⲉ-", "إلى": "ⲉ-", "الى": "ⲉ-", "ل": "ⲉ-", "لـ": "ⲉ-", "نحو": "ⲉ-", "صوب": "ⲉ-",
        "مع": "ⲙⲛ̄",
        "عند": "ϩⲁⲧⲛ̄", "لدى": "ϩⲁⲧⲛ̄", "لدي": "ϩⲁⲧⲛ̄",
        "تحت": "ϩⲁ",
        "فوق": "ⲉϩⲣⲁⲓ ⲉϫⲛ̄",
        "امام": "ⲙ̄ⲡⲉⲙ̄ⲧⲟ ⲛ̄", "أمام": "ⲙ̄ⲡⲉⲙ̄ⲧⲟ ⲛ̄", "قدام": "ⲙ̄ⲡⲉⲙ̄ⲧⲟ ⲛ̄",
        "وراء": "ϩⲓⲡⲁϩⲟⲩ", "خلف": "ϩⲓⲡⲁϩⲟⲩ",
        "قبل": "ϩⲁⲧⲏⲩ",
        "بعد": "ⲙⲛ̄ⲛ̄ⲥⲁ",
        "بين": "ⲟⲩⲧⲉ",
        "لاجل": "ⲉⲧⲃⲉ", "لأجل": "ⲉⲧⲃⲉ", "بسبب": "ⲉⲧⲃⲉ", "عن": "ⲉⲧⲃⲉ",
        "حتى": "ϣⲁ", "حتي": "ϣⲁ",
        "بدون": "ⲁϫⲛ̄", "بغير": "ⲁϫⲛ̄", "دون": "ⲁϫⲛ̄",
        "مثل": "ⲛ̄ⲑⲉ ⲛ̄", "ك": "ⲛ̄ⲑⲉ ⲛ̄", "كـ": "ⲛ̄ⲑⲉ ⲛ̄",
        "حسب": "ⲕⲁⲧⲁ", "وفق": "ⲕⲁⲧⲁ",
        "بواسطة": "ⲉⲃⲟⲗ ϩⲓⲧⲛ̄", "خلال": "ⲉⲃⲟⲗ ϩⲓⲧⲛ̄",
        "حول": "ⲕⲱⲧⲉ ⲉ-",
    },
    "fayyumic": {
        "في": "ϧⲉⲛ", "ب": "ϧⲉⲛ", "بـ": "ϧⲉⲛ",
        "على": "ϩⲓϫⲉⲛ", "علي": "ϩⲓϫⲉⲛ",
        "من": "ⲉⲃⲟⲗ ϧⲉⲛ",
        "الي": "ⲉ-", "إلى": "ⲉ-", "الى": "ⲉ-", "ل": "ⲉ-", "لـ": "ⲉ-", "نحو": "ⲉ-", "صوب": "ⲉ-",
        "مع": "ⲛⲉⲙ",
        "عند": "ϧⲁⲧⲉⲛ", "لدى": "ϧⲁⲧⲉⲛ", "لدي": "ϧⲁⲧⲉⲛ",
        "تحت": "ϧⲁ",
        "فوق": "ⲉϩⲣⲏⲓ ⲉϫⲉⲛ",
        "امام": "ⲙ̀ⲡⲉⲙ̀ⲑⲟ ⲛ̀", "أمام": "ⲙ̀ⲡⲉⲙ̀ⲑⲟ ⲛ̀", "قدام": "ⲙ̀ⲡⲉⲙ̀ⲑⲟ ⲛ̀",
        "وراء": "ⲥⲁⲫⲁϩⲟⲩ", "خلف": "ⲥⲁⲫⲁϩⲟⲩ",
        "قبل": "ϧⲁϫⲱ",
        "بعد": "ⲙⲉⲛⲉⲛⲥⲁ",
        "بين": "ⲟⲩⲧⲉ",
        "لاجل": "ⲉⲑⲃⲉ", "لأجل": "ⲉⲑⲃⲉ", "بسبب": "ⲉⲑⲃⲉ", "عن": "ⲉⲑⲃⲉ",
        "حتى": "ϣⲁ", "حتي": "ϣⲁ",
        "بدون": "ⲁϫⲛⲉ", "بغير": "ⲁϫⲛⲉ", "دون": "ⲁϫⲛⲉ",
        "مثل": "ⲙ̀ⲫⲣⲏϯ ⲛ̀", "ك": "ⲙ̀ⲫⲣⲏϯ ⲛ̀", "كـ": "ⲙ̀ⲫⲣⲏϯ ⲛ̀",
        "حسب": "ⲕⲁⲧⲁ", "وفق": "ⲕⲁⲧⲁ",
        "بواسطة": "ⲉⲃⲟⲗ ϩⲓⲧⲉⲛ", "خلال": "ⲉⲃⲟⲗ ϩⲓⲧⲉⲛ",
        "حول": "ⲕⲱϯ ⲉ̀",
    },
}


@dataclass
class SyntaxComposition:
    coptic_text: str | None
    grammar_notes: list[dict] = field(default_factory=list)


def _resolve_dialect_key(dialect_id: int | str) -> str:
    val = str(dialect_id).lower().strip()
    if val in {"2", "sahidic"}:
        return "sahidic"
    if val in {"3", "fayyumic"}:
        return "fayyumic"
    return "bohairic"


def compose_coptic_sentence_with_notes(
    breakdown: list[dict], dialect_id: int = 1
) -> SyntaxComposition:
    """
    Intelligently compose a grammatically sound Coptic sentence from token breakdown,
    applying morphological conjugations, agreement checks, negation, and dialect priority.
    """
    dialect_key = _resolve_dialect_key(dialect_id)
    is_bohairic = (dialect_key == "bohairic")
    is_sahidic = (dialect_key == "sahidic")
    is_fayyumic = (dialect_key == "fayyumic")

    valid_items = [
        item for item in breakdown
        if (item.get("status") in {"known", None} and item.get("coptic"))
        or normalize_arabic(item.get("arabic", "")) in {"لم", "لا", "ما", "لن", "ليس", "ليست"}
        or normalize_arabic(item.get("arabic", "")) in _PREPOSITIONS_BY_DIALECT.get(dialect_key, {})
        or (normalize_arabic(item.get("arabic", "")).startswith("و") and normalize_arabic(item.get("arabic", ""))[1:] in _PREPOSITIONS_BY_DIALECT.get(dialect_key, {}))
    ]
    if len(valid_items) != len(breakdown) or not valid_items:
        return SyntaxComposition(coptic_text=None, grammar_notes=[])

    # Reconstruct raw Arabic sentence to run sentence-type analysis
    raw_sentence = " ".join(item.get("arabic", "").strip() for item in breakdown)
    analysis = SentenceTypeDetector.analyze(raw_sentence, breakdown)

    tokens_count = len(breakdown)
    output_tokens: list[str] = []
    notes: list[dict] = []

    def _add_note(title: str, description: str):
        if not any(n["title"] == title and n["description"] == description for n in notes):
            notes.append({"title": title, "description": description})

    # Add explanations from sentence analysis
    for expl in analysis.explanations:
        _add_note("تحليل بنية الجملة (Sentence-Type Analysis)", expl)

    prep_map = _PREPOSITIONS_BY_DIALECT.get(dialect_key, _PREPOSITIONS_BY_DIALECT["bohairic"])
    copula_inserted = False

    i = 0
    while i < tokens_count:
        item = breakdown[i]
        raw_ar = item.get("arabic", "").strip()
        norm_ar = normalize_arabic(raw_ar)
        coptic_word = item.get("coptic", "").strip()

        # Handle Explicit Copula Verbs (أكون / يكون / تكون / نكون / ...)
        if norm_ar in _COPULA_WORDS_AR:
            output_tokens.append(analysis.copula_coptic)
            _add_note(
                "رابط الكينونة القبطي (Nominal Copula)",
                f"تُرجم فعل الكينونة «{raw_ar}» إلى رابط الكينونة القبطي «{analysis.copula_coptic}» المتطابق مع الفاعل ({analysis.subject_gender.value})."
            )
            copula_inserted = True
            i += 1
            continue

        # Handle Separating Pronoun as Copula (أنا هو ... / أنت هو ...)
        if norm_ar in {"هو", "هي", "هم"} and i > 0 and analysis.sentence_type == SentenceType.NOMINAL and not copula_inserted:
            prev_norm = normalize_arabic(breakdown[i - 1].get("arabic", ""))
            if prev_norm in {"انا", "أنا", "انت", "أنت", "انتي", "نحن", "انتم"}:
                output_tokens.append(analysis.copula_coptic)
                _add_note(
                    "ضمير الفصل ورابط الكينونة (Nominal Copula)",
                    f"تُرجم ضمير الفصل «{raw_ar}» إلى رابط الكينونة القبطي «{analysis.copula_coptic}» المتوافق مع الفاعل."
                )
                copula_inserted = True
                i += 1
                continue

        # Handle attached Arabic conjunction 'و'
        has_leading_waw = (
            raw_ar.startswith("و") and
            len(raw_ar) > 1 and
            norm_ar not in {"واحد", "وحيد", "ورقة", "ورد", "وزن", "وقت", "ولد", "وفاق", "وجه"}
        )

        if has_leading_waw and i > 0:
            is_prep = norm_ar in prep_map or raw_ar[1:] in prep_map
            if is_prep:
                conj = "ⲟⲩⲟϩ" if is_bohairic else "ⲁⲩⲱ"
                _add_note("أداة عطف الجمل والعبارات (Clause Conjunction)", f"استُخدمت الأداة «{conj}» بحسب قواعد اللهجة {dialect_key.capitalize()}.")
            else:
                conj = "ⲛⲉⲙ" if (is_bohairic or dialect_key == "fayyumic") else "ⲙⲛ̄"
                _add_note("أداة عطف واشتراك الأسماء (Noun Conjunction)", f"استُخدمت الأداة «{conj}» لعطف الأسماء المشتركة.")
            output_tokens.append(conj)

        # 1. Handle Negation Particles (لم، لن، لا، ليس)
        if norm_ar in {"لم", "لن", "لا", "ما", "ليس", "ليست"}:
            if norm_ar == "لم" and i + 1 < tokens_count:
                # Past negative prefix: ⲙ̀ⲡⲉ- (Bohairic) / ⲙ̄ⲡⲉ- (Sahidic)
                next_item = breakdown[i + 1]
                next_coptic = next_item.get("coptic", "").strip()
                person_prefix = VerbConjugator.conjugate(next_coptic, tense=GrammaticalTense.PERFECT_1, person=analysis.detected_person, dialect=dialect_key).prefix
                # In Coptic negative past: ⲙ̀ⲡⲓ- (1s), ⲙ̀ⲡⲉⲕ- (2sm), ⲙ̀ⲡⲉϥ- (3sm), ⲙ̀ⲡⲉⲥ- (3sf), ⲙ̀ⲡⲉⲛ- (1p)
                neg_base = "ⲙ̀ⲡⲉ" if is_bohairic else "ⲙ̄ⲡⲉ"
                neg_prefix = f"{neg_base}ϥ" if analysis.detected_person == GrammaticalPerson.THIRD_SG_M else f"{neg_base}"
                output_tokens.append(f"{neg_prefix}{next_coptic}")
                _add_note("نفي الزمن الماضي (Past Negation)", f"صيغت جملة النفي بالسابقة «{neg_prefix}» للفعل.")
                i += 2
                continue
            elif norm_ar in {"لا", "ما"} and i + 1 < tokens_count:
                # Present negative: ⲛ̀... ⲁⲛ
                next_item = breakdown[i + 1]
                next_coptic = next_item.get("coptic", "").strip()
                prefix = "ⲛ̀ϥ" if (is_bohairic and analysis.detected_person == GrammaticalPerson.THIRD_SG_M) else ("ⲛ̄ϥ" if is_sahidic else "ⲛ̀")
                output_tokens.append(f"{prefix}{next_coptic} ⲁⲛ")
                _add_note("نفي الزمن الحاضر (Present Negation)", f"صيغت جملة النفي بأداة النفي المزدوجة «{prefix}... ⲁⲛ».")
                i += 2
                continue
            elif norm_ar == "لن" and i + 1 < tokens_count:
                # Future negative: ⲛ̀ⲛⲉ-
                next_item = breakdown[i + 1]
                next_coptic = next_item.get("coptic", "").strip()
                neg_fut = "ⲛ̀ⲛⲉϥ" if is_bohairic else "ⲛ̄ⲛⲉϥ"
                output_tokens.append(f"{neg_fut}{next_coptic}")
                _add_note("نفي المستقبل (Future Negation)", f"صيغت جملة نفي المستقبل بالسابقة «{neg_fut}».")
                i += 2
                continue
            elif norm_ar in {"ليس", "ليست"}:
                output_tokens.append("ⲙ̀ⲙⲟⲛ" if is_bohairic else "ⲙⲛ̄")
                _add_note("نفي الكينونة (Negative Existential)", "استُخدمت أداة نفي الكينونة/الوجود.")
                i += 1
                continue

        # 2. Handle Vocative (يا ...)
        if norm_ar == "يا":
            _add_note("أسلوب النداء (Vocative)", "استُخدمت أداة النداء القبطية «ⲱ» قبل المنادى.")
            if i + 1 < tokens_count and breakdown[i + 1].get("coptic"):
                next_item = breakdown[i + 1]
                next_coptic = next_item["coptic"].strip()
                output_tokens.append(f"ⲱ {next_coptic}")
                i += 2
                continue
            else:
                output_tokens.append("ⲱ")
                i += 1
                continue

        # 3. Handle standalone Prepositions (في, على, من, تحت, فوق, قبل, بعد, بين, عند, بدون, بغير, بواسطة, حسب, ك, ب, ل)
        base_prep_ar = norm_ar[1:] if has_leading_waw else norm_ar
        if base_prep_ar in prep_map and norm_ar not in {"باسم", "بإسم"} and not norm_ar.startswith("بال"):
            p_coptic = prep_map[base_prep_ar]
            _add_note("حرف جر قبطي (Preposition)", f"تُرجم حرف الجر «{base_prep_ar}» إلى المقابل القبطي «{p_coptic}» في لهجة {dialect_key.capitalize()}.")
            output_tokens.append(p_coptic)
            i += 1
            continue

        # 2.5 Handle Attached Prepositions (بـ, بالـ, لـ, للـ, كـ, كالـ)
        if norm_ar in {"باسم", "بإسم"}:
            prep = "ϧⲉⲛ" if (is_bohairic or is_fayyumic) else "ϩⲙ̄"
            output_tokens.append(prep)
            _add_note("حرف الجر المتصل (Attached Preposition)", f"تُرجم حرف الجر المتصل «بـ» إلى «{prep}» في لهجة {dialect_key.capitalize()}.")
            
            head_noun_coptic = "ⲫ̀ⲣⲁⲛ" if is_bohairic else "ⲡⲣⲁⲛ"
            
            if i + 1 < tokens_count:
                next_item = breakdown[i + 1]
                next_ar = next_item.get("arabic", "").strip()
                next_norm_ar = normalize_arabic(next_ar)
                next_coptic = next_item.get("coptic", "").strip()
                
                is_next_target = (
                    next_ar.startswith("ال") or
                    next_norm_ar in {"الله", "الاب", "المسيح", "يسوع", "داود", "موسي", "ابراهيم", "يعقوب", "اسحق", "مريم"}
                )
                if is_next_target and next_coptic and next_norm_ar not in _ALL_VERBS:
                    if is_bohairic or is_fayyumic:
                        starts_labial = any(next_coptic.startswith(lab) for lab in _LABIALS_BOHAIRIC)
                        gen_particle = "ⲙ̀" if (next_norm_ar in {"الله", "الاب", "المسيح", "الرب"} or starts_labial) else "ⲛ̀ⲧⲉ"
                    else:
                        starts_labial = any(next_coptic.startswith(lab) for lab in _LABIALS_BOHAIRIC)
                        gen_particle = "ⲙ̄" if starts_labial else "ⲛ̄"
                    
                    output_tokens.append(head_noun_coptic)
                    if gen_particle in ("ⲙ̀", "ⲛ̀", "ⲙ̄", "ⲛ̄"):
                        output_tokens.append(f"{gen_particle}{next_coptic}")
                    else:
                        output_tokens.append(gen_particle)
                        output_tokens.append(next_coptic)
                    _add_note(
                        "أداة الإضافة والمضاف إليه (Genitive Linker)",
                        f"عُرِّف المضاف «اسم» ليكون «{head_noun_coptic}» ورُبط بالمضاف إليه «{next_ar}» بأداة الإضافة «{gen_particle}» قبل الحرف {'الشفهي' if starts_labial else 'المضاف إليه'}."
                    )
                    i += 2
                    continue
                else:
                    output_tokens.append(head_noun_coptic)
                    i += 1
                    continue
            else:
                output_tokens.append(head_noun_coptic)
                i += 1
                continue

        elif norm_ar.startswith("بال") and len(norm_ar) > 4:
            prep = "ϧⲉⲛ" if (is_bohairic or is_fayyumic) else "ϩⲛ̄"
            output_tokens.append(prep)
            _add_note("حرف الجر المتصل (Attached Preposition)", f"تُرجم حرف الجر المتصل «بـ» إلى «{prep}» في لهجة {dialect_key.capitalize()}.")
            
            if norm_ar == "بالله":
                god = "Ⲫⲛⲟⲩϯ" if is_bohairic else ("ⲡⲛⲟⲩⲧⲉ" if not is_fayyumic else "Ⲫⲛⲟⲩϯ")
                output_tokens.append(god)
                i += 1
                continue
            
            # Articled noun
            head_gender = GrammaticalGender.FEMININE if (norm_ar.endswith("ه") or norm_ar.endswith("ة")) else GrammaticalGender.MASCULINE
            head_articled, _ = NounDeclension.attach_definite_article(coptic_word, gender=head_gender, dialect=dialect_key)
            
            # Check for following adjective (e.g. بالروح القدس)
            if i + 1 < tokens_count:
                next_item = breakdown[i + 1]
                next_ar = next_item.get("arabic", "").strip()
                next_norm_ar = normalize_arabic(next_ar)
                is_def_adj = next_ar.startswith("ال")
                base_adj = next_norm_ar[2:] if is_def_adj and len(next_norm_ar) > 2 else next_norm_ar
                stripped_base = base_adj[:-1] if (base_adj.endswith("ه") or base_adj.endswith("ة")) else base_adj
                lookup_key = next_norm_ar if next_norm_ar in _GENDERED_ADJECTIVE_MAP else (base_adj if base_adj in _GENDERED_ADJECTIVE_MAP else (stripped_base if stripped_base in _GENDERED_ADJECTIVE_MAP else None))
                if is_def_adj and lookup_key:
                    adj_table = _GENDERED_ADJECTIVE_MAP[lookup_key].get(dialect_key, _GENDERED_ADJECTIVE_MAP[lookup_key]["bohairic"])
                    gender_key = "f" if head_gender == GrammaticalGender.FEMININE else "m"
                    coptic_adj = adj_table.get(gender_key, adj_table.get("m"))
                    output_tokens.append(head_articled)
                    output_tokens.append(coptic_adj)
                    _add_note("مطابقة الصفة للموصوف (Gender/Number Agreement)", f"طُوبقت الصفة «{next_ar}» مع الموصوف جنساً وعدداً ({gender_key}) باستخدام «{coptic_adj}».")
                    i += 2
                    continue
            
            output_tokens.append(head_articled)
            i += 1
            continue

        elif norm_ar in {"لله", "ولله"}:
            if norm_ar.startswith("و"):
                output_tokens.append("ⲟⲩⲟϩ" if is_bohairic else "ⲁⲩⲱ")
            prep = "ⲉ̀" if is_bohairic else "ⲉ-"
            god = "Ⲫⲛⲟⲩϯ" if is_bohairic else "ⲡⲛⲟⲩⲧⲉ"
            output_tokens.append(f"{prep}{god}" if is_bohairic else f"ⲉ{god}")
            _add_note("حرف الجر المتصل (Attached Preposition)", "تُرجم حرف الجر المتصل «لـ» إلى «ⲉ̀» قبل لفظ الجلالة «الله».")
            i += 1
            continue

        elif norm_ar.startswith("لل") and len(norm_ar) > 3 and norm_ar not in _ROOT_L_WORDS:
            prep = "ⲉ̀" if is_bohairic else "ⲉ-"
            output_tokens.append(prep)
            _add_note("حرف الجر المتصل (Attached Preposition)", f"تُرجم حرف الجر المتصل «لـ» إلى «{prep}» في لهجة {dialect_key.capitalize()}.")
            if norm_ar == "للرب":
                output_tokens.append("Ⲡϭⲟⲓⲥ" if is_bohairic else "ⲡϫⲟⲉⲓⲥ")
                i += 1
                continue
            head_gender = GrammaticalGender.FEMININE if (norm_ar.endswith("ه") or norm_ar.endswith("ة")) else GrammaticalGender.MASCULINE
            head_articled, _ = NounDeclension.attach_definite_article(coptic_word, gender=head_gender, dialect=dialect_key)
            output_tokens.append(head_articled)
            i += 1
            continue

        elif norm_ar.startswith("كال") and len(norm_ar) > 4:
            prep = "ⲙ̀ⲫⲣⲏϯ ⲛ̀" if is_bohairic else "ⲛ̄ⲑⲉ ⲛ̄"
            output_tokens.append(prep)
            _add_note("حرف الجر المتصل (Attached Preposition)", f"تُرجم حرف التشبيه المتصل «كـ» إلى «{prep}» في لهجة {dialect_key.capitalize()}.")
            head_gender = GrammaticalGender.FEMININE if (norm_ar.endswith("ه") or norm_ar.endswith("ة")) else GrammaticalGender.MASCULINE
            head_articled, _ = NounDeclension.attach_definite_article(coptic_word, gender=head_gender, dialect=dialect_key)
            output_tokens.append(head_articled)
            i += 1
            continue

        elif norm_ar.startswith("ب") and len(norm_ar) > 2 and norm_ar not in _ROOT_B_WORDS and not norm_ar.startswith("بال") and norm_ar not in prep_map:
            prep = "ϧⲉⲛ" if (is_bohairic or is_fayyumic) else "ϩⲛ̄"
            output_tokens.append(prep)
            _add_note("حرف الجر المتصل (Attached Preposition)", f"تُرجم حرف الجر المتصل «بـ» إلى «{prep}» في لهجة {dialect_key.capitalize()}.")
            if coptic_word:
                output_tokens.append(coptic_word)
            i += 1
            continue

        # 4. Handle standalone Conjunction (و)
        if norm_ar == "و":
            next_ar = breakdown[i + 1].get("arabic", "").strip() if i + 1 < tokens_count else ""
            next_norm = normalize_arabic(next_ar)
            is_next_prep = next_norm in prep_map or next_ar in prep_map
            conj = "ⲟⲩⲟϩ" if (is_bohairic and is_next_prep) else ("ⲛⲉⲙ" if (is_bohairic and i > 0 and i + 1 < tokens_count) else ("ⲟⲩⲟϩ" if is_bohairic else "ⲁⲩⲱ"))
            _add_note("أداة العطف (Conjunction)", f"استُخدمت أداة العطف «{conj}».")
            output_tokens.append(conj)
            i += 1
            continue

        # 5. Handle Verb Conjugation when preceded by Subject Pronoun: e.g. أنا أحب -> ⲁⲛⲟⲕ ϯⲙⲉⲓ, نحن نصلي -> ⲧⲉⲛϣⲗⲏⲗ
        if (norm_ar in {"انا", "أنا", "نحن", "هو", "هي", "انت", "أنت", "هم"}) and (i + 1 < tokens_count):
            next_item = breakdown[i + 1]
            next_ar = normalize_arabic(next_item.get("arabic", ""))
            next_pos = str(next_item.get("part_of_speech") or "").lower()

            if next_ar in _COPULA_WORDS_AR:
                output_tokens.append(coptic_word)
                output_tokens.append(analysis.copula_coptic)
                _add_note(
                    "رابط الكينونة القبطي (Nominal Copula)",
                    f"تُرجم فعل الكينونة «{next_item.get('arabic')}» إلى رابط الكينونة القبطي «{analysis.copula_coptic}» المتطابق مع الفاعل ({analysis.subject_gender.value})."
                )
                copula_inserted = True
                i += 2
                continue

            if (next_ar in _ALL_VERBS or next_pos in {"verb", "v"}) and next_ar not in _COPULA_WORDS_AR:
                conj_res = VerbConjugator.conjugate(
                    next_item.get("coptic", ""),
                    tense=analysis.detected_tense,
                    person=analysis.detected_person,
                    dialect=dialect_key,
                )
                output_tokens.append(coptic_word)
                output_tokens.append(conj_res.conjugated_form)
                _add_note("تصريف الفعل والفاعل (Verb Conjugation Agreement)", conj_res.explanation)
                i += 2
                continue
            elif analysis.sentence_type == SentenceType.NOMINAL and not analysis.has_verb and not copula_inserted:
                if next_ar not in _COPULA_WORDS_AR and next_ar not in {"هو", "هي", "هم"}:
                    output_tokens.append(coptic_word)
                    output_tokens.append(analysis.copula_coptic)
                    _add_note(
                        "رابط الكينونة في الجملة الاسمية (Nominal Copula)",
                        f"أُضيف رابط الكينونة القبطي «{analysis.copula_coptic}» بعد ضمير المبتدأ «{raw_ar}» لربطه بالخبر."
                    )
                    copula_inserted = True
                    i += 1
                    continue

        # 5.5 Handle Numerals & Counted Nouns: e.g. ثلاثة رجال -> ϣⲟⲙⲧ ⲛ̀ⲣⲱⲙⲓ / اله واحد -> ⲟⲩⲛⲟⲩϯ ⲛ̀ⲟⲩⲱⲧ
        num_val = CopticNumerals.AR_WORD_TO_NUMBER.get(norm_ar) or (int(norm_ar) if norm_ar.isdigit() else None)
        if num_val is not None and (i + 1 < tokens_count):
            next_item = breakdown[i + 1]
            next_ar = next_item.get("arabic", "").strip()
            next_coptic = next_item.get("coptic", "").strip()
            if next_coptic:
                gen = GrammaticalGender.FEMININE if (next_ar.endswith("ة") or next_ar.endswith("ه")) else GrammaticalGender.MASCULINE
                phrase, expl = CopticNumerals.format_numeral_with_noun(num_val, next_coptic, gender=gen, dialect=dialect_key)
                output_tokens.append(phrase)
                _add_note("العدد والمعدود (Numeral-Noun Syntax)", expl)
                i += 2
                continue

        if (i + 1 < tokens_count) and coptic_word:
            next_norm = normalize_arabic(breakdown[i + 1].get("arabic", ""))
            if next_norm in {"واحد", "واحده", "واحدة", "وحيد"}:
                phrase, expl = CopticNumerals.format_numeral_with_noun(1, coptic_word, dialect=dialect_key)
                output_tokens.append(phrase)
                _add_note("مطابقة عدد الوحدة (Adjectival Numeral 'One')", expl)
                i += 2
                continue

        # 6. Handle Direct Object Linkers after Transitive Verbs: e.g. أحب الله -> ϯⲙⲉⲓ ⲙ̀Ⲫⲛⲟⲩϯ
        if norm_ar in _TRANSITIVE_VERBS and (i + 1 < tokens_count):
            next_item = breakdown[i + 1]
            next_ar = next_item.get("arabic", "").strip()
            next_norm_ar = normalize_arabic(next_ar)
            next_coptic = next_item.get("coptic", "").strip()

            is_definite_object = (
                next_ar.startswith("ال") or
                next_norm_ar in {"الله", "المسيح", "يسوع", "داود", "موسي", "ابراهيم", "يعقوب", "اسحق", "مريم"}
            )

            if is_definite_object and next_coptic:
                output_tokens.append(coptic_word)
                starts_labial = any(next_coptic.startswith(lab) for lab in _LABIALS_BOHAIRIC)
                obj_marker = "ⲙ̀" if (is_bohairic and starts_labial) else ("ⲛ̀" if is_bohairic else "ⲛ̄")
                output_tokens.append(f"{obj_marker}{next_coptic}")
                _add_note(
                    "أداة المفعول به المباشر (Direct Object Linker)",
                    f"أُضيفت أداة المفعول به «{obj_marker}» بعد الفعل المتعدي لربط المفعول به المعرف."
                )
                i += 2
                continue

        # 7. Handle Adjective & Gender/Number Agreement: e.g. الملكة الصالحة -> ϯⲟⲩⲣⲱ ⲉⲑⲛⲁⲛⲉⲥ
        if (i + 1 < tokens_count) and norm_ar not in _ALL_VERBS:
            next_item = breakdown[i + 1]
            next_ar = next_item.get("arabic", "").strip()
            next_norm_ar = normalize_arabic(next_ar)
            is_def_adj = next_ar.startswith("ال")
            base_adj = next_norm_ar[2:] if is_def_adj and len(next_norm_ar) > 2 else next_norm_ar
            stripped_base = base_adj[:-1] if (base_adj.endswith("ه") or base_adj.endswith("ة")) else base_adj
            lookup_key = base_adj if base_adj in _GENDERED_ADJECTIVE_MAP else (stripped_base if stripped_base in _GENDERED_ADJECTIVE_MAP else None)

            if is_def_adj and lookup_key:
                adj_table = _GENDERED_ADJECTIVE_MAP[lookup_key].get(dialect_key, _GENDERED_ADJECTIVE_MAP[lookup_key]["bohairic"])
                # Determine gender from noun
                gender_key = "f" if analysis.subject_gender == GrammaticalGender.FEMININE else "m"
                if analysis.subject_number == GrammaticalNumber.PLURAL:
                    gender_key = "pl"

                coptic_adj = adj_table.get(gender_key, adj_table.get("m"))
                output_tokens.append(coptic_word)
                output_tokens.append(coptic_adj)
                _add_note(
                    "مطابقة الصفة للموصوف (Gender/Number Agreement)",
                    f"طُوبقت الصفة «{next_ar}» مع الموصوف جنساً وعدداً ({gender_key}) باستخدام «{coptic_adj}» في لهجة {dialect_key.capitalize()}."
                )
                i += 2
                continue

        # 8. Handle Genitive Constructs: e.g. حارس البيت, ابن الله, ملك الملوك
        base_head_ar = norm_ar[1:] if (has_leading_waw and not raw_ar.startswith("وال")) else norm_ar
        is_head_candidate = (
            base_head_ar in _GENITIVE_HEAD_WORDS or
            (not raw_ar.startswith("ال") and not raw_ar.startswith("وال") and base_head_ar not in _ALL_VERBS)
        )

        if is_head_candidate and (i + 1 < tokens_count) and base_head_ar not in _ALL_VERBS:
            next_item = breakdown[i + 1]
            next_ar = next_item.get("arabic", "").strip()
            next_norm_ar = normalize_arabic(next_ar)
            next_coptic = next_item.get("coptic", "").strip()

            is_next_genitive_target = (
                next_ar.startswith("ال") or
                next_norm_ar in {"الله", "المسيح", "يسوع", "داود", "موسي", "ابراهيم", "يعقوب", "اسحق", "مريم"}
            )

            if is_next_genitive_target and next_coptic and next_norm_ar not in _ALL_VERBS and next_norm_ar not in prep_map:
                # In Arabic, annexation to a definite noun ("معرّف بالإضافة") makes the head noun definite.
                # In Coptic with the indirect genitive (ⲛ̀ⲧⲉ), the definite head noun takes the definite article (ⲡⲓ- / ϯ- / ⲛⲓ-).
                # e.g. خبز الحياة -> ⲡⲓⲱⲓⲕ ⲛ̀ⲧⲉ ⲡⲓⲱⲛϧ
                head_gender = GrammaticalGender.FEMININE if (
                    raw_ar.endswith("ة") or (raw_ar.endswith("ه") and raw_ar not in {"الله", "اله", "إله", "وجه", "شبه", "فقيه"})
                ) else GrammaticalGender.MASCULINE
                head_number = GrammaticalNumber.PLURAL if (
                    raw_ar.endswith("ون") or raw_ar.endswith("ين") or raw_ar.endswith("ات")
                ) else GrammaticalNumber.SINGULAR

                head_with_article, def_note = NounDeclension.attach_definite_article(
                    coptic_word,
                    gender=head_gender,
                    number=head_number,
                    dialect=dialect_key,
                )
                output_tokens.append(head_with_article)
                _add_note(
                    "تعريف المضاف بالإضافة (Definite Genitive Head)",
                    f"عُرِّف المضاف «{raw_ar}» بأداة التعريف القبطية «{head_with_article}» لأنه معرّف بالإضافة إلى «{next_ar}»."
                )

                if is_bohairic:
                    starts_labial = any(next_coptic.startswith(lab) for lab in _LABIALS_BOHAIRIC)
                    genitive_particle = "ⲙ̀" if (next_norm_ar in {"الله", "الاب", "المسيح", "الرب"} and starts_labial) else "ⲛ̀ⲧⲉ"
                else:
                    genitive_particle = "ⲛ̄ⲧⲉ"

                if genitive_particle in ("ⲙ̀", "ⲛ̀"):
                    output_tokens.append(f"{genitive_particle}{next_coptic}")
                else:
                    output_tokens.append(genitive_particle)
                    output_tokens.append(next_coptic)

                _add_note(
                    "أداة الإضافة والمضاف إليه (Genitive Linker)",
                    f"أُضيفت أداة الإضافة «{genitive_particle}» لربط المضاف «{raw_ar}» بالمضاف إليه «{next_ar}»."
                )
                i += 2
                continue

        # Default: append word
        output_tokens.append(coptic_word)
        i += 1

    # 9. Handle Nominal Sentence Copula note
    if analysis.sentence_type == SentenceType.NOMINAL and not analysis.has_verb and not copula_inserted:
        _add_note(
            "رابط الكينونة في الجملة الاسمية (Nominal Copula)",
            f"الجملة الاسمية يربطها في القبطية رابط الكينونة «{analysis.copula_coptic}» المتطابق مع الفاعل ({analysis.subject_gender.value})."
        )

    composed = " ".join(output_tokens) if output_tokens else None
    return SyntaxComposition(coptic_text=composed, grammar_notes=notes)


def compose_coptic_sentence(breakdown: list[dict], dialect_id: int = 1) -> str | None:
    """Wrapper returning only the composed Coptic text."""
    res = compose_coptic_sentence_with_notes(breakdown, dialect_id=dialect_id)
    return res.coptic_text
