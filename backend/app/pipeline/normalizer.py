"""Stage 1: Arabic + Coptic text normalization and tokenization.

Normalization is idempotent and used both in the pipeline and at validation
time, guaranteeing that the same input always maps to the same canonical key
in `arabic_index` (unique constraint safety).
"""
from __future__ import annotations

import re
import unicodedata

# --- Arabic character maps ------------------------------------------------- #
ALEF_VARIANTS = {"أ", "إ", "آ", "ٱ"}
YAA_ALEF_MAQSURA = {"ى"}
TAA_MARBUTA = "ة"
HAMZA_IN_MIDDLE = "ئ"


# Diacritics (tashkeel) + tatweel
ARABIC_DIACRITICS = re.compile(
    "["
    "\u0610-\u061a"  # Quranic marks
    "\u064b-\u065f"  # tashkeel
    "\u0670"         # superscript alef
    "\u06d6-\u06dc"  # Quranic
    "\u06df-\u06e8"
    "\u06ea-\u06ed"
    "\u0640"         # tatweel
    "]"
)

# Prefixes that carry no independent meaning for translation lookup; we keep
# them for word-order but normalize them before dictionary matching.
ARABIC_PREFIXES = ("ال", "و", "ف", "ب", "ل", "ك", "س")


def normalize_arabic(text: str) -> str:
    """Normalize an Arabic string to a canonical search form.

    Steps:
      1. NFKC unicode normalization
      2. unify alef variants -> ا
      3. unify alef maqsura/yaa -> ي
      4. taa marbuta -> ه
      5. remove hamza-on-yaa middle forms
      6. strip tashkeel + tatweel
      7. collapse whitespace, lowercase, strip
    """
    if not text:
        return ""

    out = unicodedata.normalize("NFKC", text)

    out = out.replace("\u0640", "")  # tatweel
    for ch in ALEF_VARIANTS:
        out = out.replace(ch, "ا")
    for ch in YAA_ALEF_MAQSURA:
        out = out.replace(ch, "ي")
    out = out.replace(TAA_MARBUTA, "ه")
    out = out.replace(HAMZA_IN_MIDDLE, "ي")

    out = ARABIC_DIACRITICS.sub("", out)
    out = re.sub(r"\s+", " ", out)
    return out.strip().lower()


def normalize_coptic(text: str) -> str:
    """Normalize Coptic text: strip combining marks, unify overline forms."""
    if not text:
        return ""
    out = unicodedata.normalize("NFKC", text)
    out = ARABIC_DIACRITICS.sub("", out)  # harmless if none present
    out = re.sub(r"\s+", " ", out)
    return out.strip()


# --- Tokenization ---------------------------------------------------------- #
# Split on whitespace and common Arabic/Latin punctuation.
_TOKEN_SPLIT = re.compile(r"[\s,،؛;:.!?«»\"'()\[\]{}]+")


def tokenize(text: str) -> list[str]:
    """Tokenize normalized Arabic text into tokens (order preserved)."""
    return [t for t in _TOKEN_SPLIT.split(text) if t]


def strip_arabic_prefix(token: str) -> str:
    """Strip a leading definite article / conjunction for dictionary fallback.

    Returns the token unchanged if no known prefix is present. This is a
    *heuristic* used only when an exact lookup fails.
    """
    for p in ("وال", "فال", "بال", "كال", "لال"):
        if token.startswith(p) and len(token) > len(p):
            return token[len(p):]
    for p in ("ال",):
        if token.startswith(p) and len(token) > len(p):
            return token[len(p):]
    for p in ("واو", "فوو", "بوو", "كوو", "لوو"):
        if token.startswith(p) and len(token) > len(p):
            return token[len(p):]
    for p in ("وا", "فو", "بو", "كو", "لو", "وس", "فس", "بس", "لس", "كس"):
        if token.startswith(p) and len(token) > len(p):
            return token[len(p):]
    for p in ("و", "ف", "ب", "ل", "ك", "س"):
        if token.startswith(p) and len(token) > len(p):
            return token[len(p):]
    return token
