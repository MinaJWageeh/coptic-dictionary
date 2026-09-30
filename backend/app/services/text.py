from __future__ import annotations

import re

_ARABIC_DIACRITICS = re.compile(r"[\u064b-\u065f\u0670]")

# Map common Arabic broken plurals to their singular base lemmas
_BROKEN_PLURALS: dict[str, str] = {
    "ملوك": "ملك",
    "ارباب": "رب",
    "ابناء": "ابن",
    "بنين": "ابن",
    "اباء": "اب",
    "امهات": "ام",
    "اخوه": "اخ",
    "اخوان": "اخ",
    "اخوات": "اخت",
    "قلوب": "قلب",
    "عيون": "عين",
    "اعين": "عين",
    "ايادي": "يد",
    "ايدي": "يد",
    "ارجل": "قدم",
    "اقدام": "قدم",
    "رؤوس": "راس",
    "ارؤس": "راس",
    "افواه": "فم",
    "السنه": "لسان",
    "مياه": "ماء",
    "امواه": "ماء",
    "اشجار": "شجرة",
    "شجر": "شجرة",
    "ثمار": "ثمرة",
    "ثمر": "ثمرة",
    "نجوم": "نجم",
    "انجم": "نجم",
    "بحار": "بحر",
    "ابحر": "بحر",
    "انهار": "نهر",
    "جبال": "جبل",
    "اجبال": "جبل",
    "بيوت": "بيت",
    "طرق": "طريق",
    "طرقات": "طريق",
    "مدن": "مدينة",
    "قرى": "قرية",
    "ابواب": "باب",
    "كتب": "كتاب",
    "رسائل": "رسالة",
    "ايام": "يوم",
    "ليالي": "ليل",
    "اوقات": "وقت",
    "ساعات": "ساعة",
    "سنوات": "سنة",
    "سنين": "سنة",
    "اعمال": "عمل",
    "خطايا": "خطيئة",
    "خطاياهم": "خطيئة",
    "وصايا": "وصية",
    "عهود": "عهد",
    "مزامير": "مزمور",
    "ترانيم": "ترنيمة",
    "ذبائح": "ذبيحة",
    "قرابين": "قربان",
    "صلوات": "صلاة",
    "بركات": "بركة",
    "نعم": "نعمة",
    "الام": "الم",
    "اوجاع": "وجع",
    "اموات": "موت",
    "موتى": "موت",
    "شهداء": "شهيد",
    "قديسين": "قديس",
    "قديسون": "قديس",
    "ملائكه": "ملاك",
    "انبياء": "نبي",
    "رسل": "رسول",
    "تلاميذ": "تلميذ",
    "عذارى": "عذراء",
    "رعاه": "راعي",
    "خراف": "خروف",
    "نعاج": "نعجة",
    "حملان": "حمل",
    "شعوب": "شعب",
    "امم": "امة",
    "عوالم": "عالم",
    "ارواح": "روح",
    "اجساد": "جسد",
    "دماء": "دم",
    "عظام": "عظم",
    "سماوات": "سماء",
    "سموات": "سماء",
    "اراضي": "ارض",
    "اصوات": "صوت",
    "اسماء": "اسم",
    "كلمات": "كلمة",
    "نيران": "نار",
}

# Map common Arabic verb conjugations to base lemmas
_VERB_MAPPINGS: dict[str, str] = {
    "يقول": "قال", "تقول": "قال", "نقول": "قال", "اقول": "قال", "قلت": "قال", "قالوا": "قال",
    "يتكلم": "تكلم", "تتكلم": "تكلم", "نتكلم": "تكلم", "اتكلم": "تكلم", "تكلموا": "تكلم",
    "يسمع": "سمع", "تسمع": "سمع", "نسمع": "سمع", "اسمع": "سمع", "سمعوا": "سمع",
    "يرى": "راى", "ترى": "راى", "نرى": "راى", "ارى": "راى", "راوا": "راى",
    "ينظر": "نظر", "تنظر": "نظر", "ننظر": "نظر", "انظر": "نظر", "نظروا": "نظر",
    "ياتي": "جاء", "تاتي": "جاء", "ناتي": "جاء", "اتي": "جاء", "جاؤوا": "جاء", "جاءوا": "جاء",
    "يذهب": "ذهب", "تذهب": "ذهب", "نذهب": "ذهب", "اذهب": "ذهب", "ذهبوا": "ذهب",
    "يعطي": "اعطى", "تعطي": "اعطى", "نعطي": "اعطى", "اعطي": "اعطى", "اعطوا": "اعطى",
    "ياخذ": "اخذ", "تاخذ": "اخذ", "ناخذ": "اخذ", "اخذوا": "اخذ",
    "يصنع": "صنع", "تصنع": "صنع", "نصنع": "صنع", "اصنع": "صنع", "صنعوا": "صنع",
    "يفعل": "فعل", "تفعل": "فعل", "نفعل": "فعل", "افعل": "فعل", "فعلوا": "فعل",
    "يعمل": "عمل", "تعمل": "عمل", "نعمل": "عمل", "اعمل": "عمل", "عملوا": "عمل",
    "يعرف": "عرف", "تعرف": "عرف", "نعرف": "عرف", "اعرف": "عرف", "عرفوا": "عرف",
    "يعلم": "علم", "تعلم": "علم", "نعلم": "علم", "اعلم": "علم", "علموا": "علم",
    "يحب": "احب", "تحب": "احب", "نحب": "احب", "احبوا": "احب",
    "يعيش": "عاش", "تعيش": "عاش", "نعيش": "عاش", "اعيش": "عاش", "عاشوا": "عاش",
    "يموت": "مات", "تموت": "مات", "نموت": "مات", "اموت": "مات", "ماتوا": "مات",
    "يقوم": "قام", "تقوم": "قام", "نقوم": "قام", "اقوم": "قام", "قاموا": "قام",
    "يسجد": "سجد", "تسجد": "سجد", "نسجد": "سجد", "اسجد": "سجد", "سجدوا": "سجد",
    "يصلي": "صلى", "تصلي": "صلى", "نصلي": "صلى", "اصلي": "صلى", "صلوا": "صلى",
    "يبارك": "بارك", "تبارك": "بارك", "نبارك": "بارك", "ابارك": "بارك", "باركوا": "بارك",
    "يسبح": "سبح", "تسبح": "سبح", "نسبح": "سبح", "اسبح": "سبح", "سبحوا": "سبح",
    "يشكر": "شكر", "تشكر": "شكر", "نشكر": "شكر", "اشكر": "شكر", "شكروا": "شكر",
    "يخلص": "خلص", "تخلص": "خلص", "نخلص": "خلص", "اخلص": "خلص", "خلصوا": "خلص",
    "يغفر": "غفر", "تغفر": "غفر", "نغفر": "غفر", "اغفر": "غفر", "غفروا": "غفر",
    "يخلق": "خلق", "تخلق": "خلق", "نخلق": "خلق", "اخلق": "خلق", "خلقوا": "خلق",
    "يرحم": "ارحم", "ترحَم": "ارحم", "نرحم": "ارحم", "ارحمنا": "ارحم",
    "يضيء": "اضاء", "تضيء": "اضاء", "نضيء": "اضاء", "اضاءت": "اضاء", "اضاءوا": "اضاء",
    "يكون": "كان", "تكون": "كان", "نكون": "كان", "اكون": "كان", "كانوا": "كان", "كنت": "كان",
    "يصير": "صار", "تصير": "صار", "نصير": "صار", "اصير": "صار", "صاروا": "صار",
}


def normalize_arabic(text: str) -> str:
    value = _ARABIC_DIACRITICS.sub("", text.strip())
    value = re.sub("[إأآا]", "ا", value)
    value = value.replace("ى", "ي").replace("ة", "ه")
    value = re.sub(r"\s+", " ", value)
    return value


def tokenize_arabic(text: str) -> list[str]:
    normalized = normalize_arabic(text)
    return [token for token in re.split(r"[^\w\u0600-\u06ff]+", normalized) if token]


def arabic_lookup_variants(normalized_token: str) -> list[str]:
    """
    Generate all possible linguistic candidate lemmas for an Arabic word.
    Handles prefixes, suffixes, broken plurals, and verb conjugations.
    """
    seen: set[str] = set()
    variants: list[str] = []

    def _add(cand: str):
        c = normalize_arabic(cand)
        if c and c not in seen:
            seen.add(c)
            variants.append(c)

    _add(normalized_token)

    # Special handling for common religious and contracted forms
    if normalized_token in {"لله", "ولله", "بالله", "فلله", "كالله"}:
        _add("الله")
    if normalized_token in {"العلى", "الاعالي", "العلي", "الاعلي"}:
        _add("الاعالي")
        _add("العلى")
    if normalized_token in {"القدس", "قدس", "مقدس", "مقدسة", "مقدسه", "طاهر", "طاهرة"}:
        _add("قدوس")

    # Check direct verb / broken plural mappings
    if normalized_token in _BROKEN_PLURALS:
        _add(_BROKEN_PLURALS[normalized_token])
    if normalized_token in _VERB_MAPPINGS:
        _add(_VERB_MAPPINGS[normalized_token])

    # Strip prefixes (ال, وال, فال, بال, كال, لل, و, ف, ب, ل, ك, س, يا)
    stripped_prefix = _strip_arabic_prefix(normalized_token)
    if stripped_prefix != normalized_token:
        _add(stripped_prefix)
        if stripped_prefix in _BROKEN_PLURALS:
            _add(_BROKEN_PLURALS[stripped_prefix])
        if stripped_prefix in _VERB_MAPPINGS:
            _add(_VERB_MAPPINGS[stripped_prefix])

    # Strip suffixes from token and stripped_prefix
    for base in [normalized_token, stripped_prefix]:
        for sfx in ("هم", "كم", "نا", "ها", "ات", "ون", "ين", "ان", "ه", "ي", "ك", "ت", "وا"):
            if len(base) > len(sfx) + 2 and base.endswith(sfx):
                sub = base[:-len(sfx)]
                _add(sub)
                if sub in _BROKEN_PLURALS:
                    _add(_BROKEN_PLURALS[sub])
                if sub in _VERB_MAPPINGS:
                    _add(_VERB_MAPPINGS[sub])

    return variants


def _strip_arabic_prefix(token: str) -> str:
    for prefix in ("وال", "فال", "بال", "كال", "لال", "لل"):
        if token.startswith(prefix) and len(token) > len(prefix):
            return token[len(prefix):]
    if token.startswith("ال") and len(token) > 2:
        return token[2:]
    if token.startswith("يا") and len(token) > 2:
        return token[2:]
    for prefix in ("و", "ف", "ب", "ل", "ك", "س"):
        if token.startswith(prefix) and len(token) > len(prefix):
            return token[len(prefix):]
    return token


def is_single_word(text: str) -> bool:
    return len(tokenize_arabic(text)) == 1


def normalize_coptic(text: str) -> str:
    """Normalize Coptic text by trimming, lowercasing, and normalizing whitespace."""
    if not text:
        return ""
    value = text.strip().lower()
    value = re.sub(r"\s+", " ", value)
    return value
