"""
Sentence-Type & Grammatical Feature Analyzer.
Categorizes Arabic sentences into:
1. Negative (جملة منفية): detects 'لا', 'لم', 'لن', 'ما', 'ليس', 'غير'.
2. Verbal (جملة فعلية): detects main verb, aspect, tense, person, and transitive/intransitive status.
3. Nominal (جملة اسمية): detects subject and predicate, selects appropriate Coptic copula (ⲡⲉ / ⲧⲉ / ⲛⲉ).
"""
from __future__ import annotations

import enum
from dataclasses import dataclass, field
from app.services.morphology import (
    GrammaticalGender,
    GrammaticalNumber,
    GrammaticalPerson,
    GrammaticalTense,
)
from app.services.text import _BROKEN_PLURALS, normalize_arabic, tokenize_arabic


class SentenceType(str, enum.Enum):
    NOMINAL = "nominal"    # جملة اسمية (مبتدأ وخبر + ضمير كينونة)
    VERBAL = "verbal"      # جملة فعلية (فعل وفاعل ومفعول به)
    NEGATIVE = "negative"  # جملة منفية (نفي ماضٍ، حاضر، مستقبل، أو كينونة)


class NegationKind(str, enum.Enum):
    PAST = "past_negation"       # لم + مضارع -> ⲙ̀ⲡⲉ-
    PRESENT = "present_negation" # لا / ما + مضارع -> ⲛ̀... ⲁⲛ
    FUTURE = "future_negation"   # لن + مضارع -> ⲛ̀ⲛⲉ-
    COPULA = "copula_negation"   # ليس -> ⲙ̀ⲙⲟⲛ / ⲙⲛ̄


@dataclass
class SentenceAnalysis:
    sentence_type: SentenceType
    negation_kind: NegationKind | None = None
    negation_particle: str | None = None
    detected_tense: GrammaticalTense = GrammaticalTense.PRESENT_1
    detected_person: GrammaticalPerson = GrammaticalPerson.THIRD_SG_M
    subject_gender: GrammaticalGender = GrammaticalGender.MASCULINE
    subject_number: GrammaticalNumber = GrammaticalNumber.SINGULAR
    copula_coptic: str = "ⲡⲉ"
    has_verb: bool = False
    verb_token: str | None = None
    verb_coptic: str | None = None
    verb_pos_index: int | None = None
    explanations: list[str] = field(default_factory=list)


# Words that explicitly denote feminine gender in Arabic
_FEMININE_NOUNS = {
    normalize_arabic(w)
    for w in [
        "كنيسة", "سماء", "ارض", "أرض", "مدينة", "ام", "أم", "اخت", "أخت", "ابنة",
        "عذراء", "شمس", "نفس", "عين", "يد", "رجل", "قدم", "صلاة", "محبة", "نعمة",
        "بركة", "حياة", "شريعة", "وصية", "قيامة", "روح", "قوة", "حكمة", "طهارة",
    ]
}

# Arabic pronouns mapped to grammatical person and gender
_PRONOUN_MAP = {
    "انا": (GrammaticalPerson.FIRST_SG, GrammaticalGender.COMMON, GrammaticalNumber.SINGULAR),
    "أنا": (GrammaticalPerson.FIRST_SG, GrammaticalGender.COMMON, GrammaticalNumber.SINGULAR),
    "انت": (GrammaticalPerson.SECOND_SG_M, GrammaticalGender.MASCULINE, GrammaticalNumber.SINGULAR),
    "أنت": (GrammaticalPerson.SECOND_SG_M, GrammaticalGender.MASCULINE, GrammaticalNumber.SINGULAR),
    "انتي": (GrammaticalPerson.SECOND_SG_F, GrammaticalGender.FEMININE, GrammaticalNumber.SINGULAR),
    "أنتِ": (GrammaticalPerson.SECOND_SG_F, GrammaticalGender.FEMININE, GrammaticalNumber.SINGULAR),
    "هو": (GrammaticalPerson.THIRD_SG_M, GrammaticalGender.MASCULINE, GrammaticalNumber.SINGULAR),
    "هي": (GrammaticalPerson.THIRD_SG_F, GrammaticalGender.FEMININE, GrammaticalNumber.SINGULAR),
    "نحن": (GrammaticalPerson.FIRST_PL, GrammaticalGender.COMMON, GrammaticalNumber.PLURAL),
    "انتم": (GrammaticalPerson.SECOND_PL, GrammaticalGender.COMMON, GrammaticalNumber.PLURAL),
    "أنتم": (GrammaticalPerson.SECOND_PL, GrammaticalGender.COMMON, GrammaticalNumber.PLURAL),
    "هم": (GrammaticalPerson.THIRD_PL, GrammaticalGender.COMMON, GrammaticalNumber.PLURAL),
}

_COPULA_WORDS_AR: set[str] = {
    "اكون", "أكون", "تكون", "يكون", "نكون", "تكونوا", "يكونوا", "تكونون", "يكونون"
}


class SentenceTypeDetector:
    """
    Analyzes sentence structure to detect sentence type, negation, person, and copula.
    """

    @classmethod
    def analyze(cls, text: str, breakdown: list[dict] | None = None) -> SentenceAnalysis:
        norm = normalize_arabic(text)
        tokens = tokenize_arabic(norm)

        analysis = SentenceAnalysis(sentence_type=SentenceType.NOMINAL)

        # 1. Detect Negation
        neg_idx = -1
        for idx, tok in enumerate(tokens):
            if tok in {"لم"}:
                analysis.sentence_type = SentenceType.NEGATIVE
                analysis.negation_kind = NegationKind.PAST
                analysis.negation_particle = tok
                analysis.detected_tense = GrammaticalTense.PERFECT_1
                analysis.explanations.append("كُشف أسلوب نفي ماضٍ باستخدام «لم» (Past Negation).")
                neg_idx = idx
                break
            elif tok in {"لن"}:
                analysis.sentence_type = SentenceType.NEGATIVE
                analysis.negation_kind = NegationKind.FUTURE
                analysis.negation_particle = tok
                analysis.detected_tense = GrammaticalTense.FUTURE_1
                analysis.explanations.append("كُشف أسلوب نفي مستقبل باستخدام «لن» (Future Negation).")
                neg_idx = idx
                break
            elif tok in {"لا", "ما"}:
                analysis.sentence_type = SentenceType.NEGATIVE
                analysis.negation_kind = NegationKind.PRESENT
                analysis.negation_particle = tok
                analysis.detected_tense = GrammaticalTense.PRESENT_1
                analysis.explanations.append(f"كُشف أسلوب نفي حاضر/عام باستخدام «{tok}» (Present Negation).")
                neg_idx = idx
                break
            elif tok in {"ليس", "ليست"}:
                analysis.sentence_type = SentenceType.NEGATIVE
                analysis.negation_kind = NegationKind.COPULA
                analysis.negation_particle = tok
                analysis.explanations.append(f"كُشف نفي كينونة/وجود باستخدام «{tok}» (Negative Copula).")
                neg_idx = idx
                break

        # 2. Detect Copula Words and Verbs
        copula_found = False
        for tok in tokens:
            if tok in _COPULA_WORDS_AR:
                copula_found = True
                if tok in {"نكون", "يكونون", "تكونون", "يكونوا", "تكونوا"}:
                    analysis.subject_number = GrammaticalNumber.PLURAL
                    analysis.detected_person = GrammaticalPerson.THIRD_PL if ("وا" in tok or "ون" in tok) else GrammaticalPerson.FIRST_PL
                elif tok in {"اكون", "أكون"}:
                    analysis.detected_person = GrammaticalPerson.FIRST_SG
                elif tok == "يكون":
                    analysis.detected_person = GrammaticalPerson.THIRD_SG_M
                elif tok == "تكون":
                    if analysis.subject_gender == GrammaticalGender.FEMININE:
                        analysis.detected_person = GrammaticalPerson.THIRD_SG_F
                    else:
                        analysis.detected_person = GrammaticalPerson.SECOND_SG_M

        verb_found = False
        if breakdown:
            for b_idx, item in enumerate(breakdown):
                pos = str(item.get("part_of_speech") or "").lower()
                ar_word = item.get("arabic", "")
                norm_word = normalize_arabic(ar_word)

                if norm_word in _COPULA_WORDS_AR:
                    copula_found = True
                    continue

                is_prefix_verb = (
                    (norm_word.startswith("ي") and len(norm_word) > 3 and norm_word not in {"يوم", "ينبوع", "يد"}) or
                    (norm_word.startswith("ن") and len(norm_word) > 3 and norm_word not in {"ناس", "نفس", "نور", "نار", "نهر", "نبي", "نعمة"})
                )
                if pos in {"verb", "v"} or is_prefix_verb:
                    verb_found = True
                    analysis.has_verb = True
                    analysis.verb_token = ar_word
                    analysis.verb_coptic = item.get("coptic")
                    analysis.verb_pos_index = b_idx
                    if analysis.sentence_type != SentenceType.NEGATIVE:
                        analysis.sentence_type = SentenceType.VERBAL

                    # Infer person from Arabic verb prefix
                    if norm_word.startswith("أ") or norm_word.startswith("ا"):
                        analysis.detected_person = GrammaticalPerson.FIRST_SG
                    elif norm_word.startswith("ن"):
                        analysis.detected_person = GrammaticalPerson.FIRST_PL
                    elif norm_word.startswith("ت"):
                        analysis.detected_person = GrammaticalPerson.SECOND_SG_M
                    elif norm_word.startswith("ي"):
                        if norm_word.endswith("ون") or norm_word.endswith("وا"):
                            analysis.detected_person = GrammaticalPerson.THIRD_PL
                        else:
                            analysis.detected_person = GrammaticalPerson.THIRD_SG_M
                    break

        # 3. Detect Pronouns
        for tok in tokens:
            if tok in _PRONOUN_MAP:
                person, gender, number = _PRONOUN_MAP[tok]
                analysis.detected_person = person
                analysis.subject_gender = gender
                analysis.subject_number = number
                analysis.explanations.append(f"حُدد ضمير الفاعل من الكلمة «{tok}» ({person.value}).")
                break

        # 4. Gender & Number for Nominal Sentences (Copula Selection)
        raw_first = tokens[0] if tokens else ""
        first_noun = raw_first
        if first_noun.startswith("ال") and len(first_noun) > 2:
            first_noun = first_noun[2:]

        if raw_first in {"الله", "اله", "إله", "رب", "مسيح", "المسيح", "اب", "الاب", "يسوع"}:
            analysis.subject_gender = GrammaticalGender.MASCULINE
            analysis.subject_number = GrammaticalNumber.SINGULAR
        elif (
            first_noun in _BROKEN_PLURALS
            or first_noun.endswith("ون")
            or first_noun.endswith("ين")
            or first_noun.endswith("ات")
        ):
            analysis.subject_number = GrammaticalNumber.PLURAL
        elif (
            first_noun in _FEMININE_NOUNS
            or (first_noun.endswith("ه") and raw_first not in {"الله", "اله", "إله"})
            or first_noun.endswith("ة")
            or first_noun.endswith("اء")
        ):
            analysis.subject_gender = GrammaticalGender.FEMININE

        # Copula assignment: ⲡⲉ (m.sg), ⲧⲉ (f.sg), ⲛⲉ (pl)
        if analysis.subject_number == GrammaticalNumber.PLURAL:
            analysis.copula_coptic = "ⲛⲉ"
        elif analysis.subject_gender == GrammaticalGender.FEMININE:
            analysis.copula_coptic = "ⲧⲉ"
        else:
            analysis.copula_coptic = "ⲡⲉ"

        if analysis.sentence_type == SentenceType.NOMINAL and not verb_found:
            analysis.explanations.append(
                f"جملة اسمية: رُبط المبتدأ والخبر برابط الكينونة القبطي «{analysis.copula_coptic}» المتوافق مع الفاعل ({analysis.subject_gender.value})."
            )

        return analysis
