"""
Coptic Morphology & Conjugation Engine.
Handles:
1. Verb conjugation across tenses (Present I, Past / Perfect I, Future I, Imperative, Aorist)
   and grammatical persons (1s, 2sm, 2sf, 3sm, 3sf, 1p, 2p, 3p).
2. Noun declensions: definite articles (m.sg, f.sg, pl), indefinite articles, possessive prefixes.
3. Dialect-specific variations (Bohairic, Sahidic, Fayyumic).
"""
from __future__ import annotations

import enum
from dataclasses import dataclass


class GrammaticalPerson(str, enum.Enum):
    FIRST_SG = "1s"       # أنا
    SECOND_SG_M = "2sm"   # أنتَ
    SECOND_SG_F = "2sf"   # أنتِ
    THIRD_SG_M = "3sm"    # هو
    THIRD_SG_F = "3sf"    # هي
    FIRST_PL = "1p"       # نحن
    SECOND_PL = "2p"      # أنتم / أنتن
    THIRD_PL = "3p"       # هم / هن


class GrammaticalTense(str, enum.Enum):
    PRESENT_1 = "present_1"    # الحاضر الأول
    PERFECT_1 = "perfect_1"    # الماضي التام الأول
    IMPERFECT = "imperfect"    # الماضي الناقص / المستمر (كان يفعل)
    FUTURE_1 = "future_1"      # المستقبل الأول
    IMPERATIVE = "imperative"  # صيغة الأمر
    AORIST = "aorist"          # المعتاد



class GrammaticalGender(str, enum.Enum):
    MASCULINE = "masculine"
    FEMININE = "feminine"
    COMMON = "common"


class GrammaticalNumber(str, enum.Enum):
    SINGULAR = "singular"
    PLURAL = "plural"


@dataclass(frozen=True)
class VerbConjugationResult:
    conjugated_form: str
    prefix: str
    base_verb: str
    tense: GrammaticalTense
    person: GrammaticalPerson
    dialect: str
    explanation: str


class VerbConjugator:
    """
    Engine for conjugating Coptic verbs according to tense, person, and dialect.
    """

    # Present I Subject Prefixes (سوابق الحاضر الأول)
    _PRESENT_PREFIXES_BOH = {
        GrammaticalPerson.FIRST_SG: "ϯ",       # ϯⲙⲉⲓ (أنا أحب)
        GrammaticalPerson.SECOND_SG_M: "ⲕ",    # ⲕⲙⲉⲓ (أنتَ تحب)
        GrammaticalPerson.SECOND_SG_F: "ⲧⲉ",   # ⲧⲉⲙⲉⲓ (أنتِ تحبين)
        GrammaticalPerson.THIRD_SG_M: "ϥ",     # ϥⲙⲉⲓ (هو يحب)
        GrammaticalPerson.THIRD_SG_F: "ⲥ",     # ⲥⲙⲉⲓ (هي تحب)
        GrammaticalPerson.FIRST_PL: "ⲧⲉⲛ",     # ⲧⲉⲛⲙⲉⲓ (نحن نحب)
        GrammaticalPerson.SECOND_PL: "ⲧⲉⲧⲉⲛ", # ⲧⲉⲧⲉⲛⲙⲉⲓ (أنتم تحبون)
        GrammaticalPerson.THIRD_PL: "ⲥⲉ",      # ⲥⲉⲙⲉⲓ (هم يحبون)
    }

    _PRESENT_PREFIXES_SAH = {
        GrammaticalPerson.FIRST_SG: "ϯ",
        GrammaticalPerson.SECOND_SG_M: "ⲕ",
        GrammaticalPerson.SECOND_SG_F: "ⲧⲉ",
        GrammaticalPerson.THIRD_SG_M: "ϥ",
        GrammaticalPerson.THIRD_SG_F: "ⲥ",
        GrammaticalPerson.FIRST_PL: "ⲧⲛ̄",
        GrammaticalPerson.SECOND_PL: "ⲧⲉⲧⲛ̄",
        GrammaticalPerson.THIRD_PL: "ⲥⲉ",
    }

    # Past / Perfect I Prefixes (سوابق الماضي الأول التام)
    _PERFECT_PREFIXES_BOH = {
        GrammaticalPerson.FIRST_SG: "ⲁⲓ",       # ⲁⲓⲙⲉⲓ (أحببتُ)
        GrammaticalPerson.SECOND_SG_M: "ⲁⲕ",    # ⲁⲕⲙⲉⲓ (أحببتَ)
        GrammaticalPerson.SECOND_SG_F: "ⲁⲣⲉ",   # ⲁⲣⲉⲙⲉⲓ (أحببتِ)
        GrammaticalPerson.THIRD_SG_M: "ⲁϥ",     # ⲁϥⲙⲉⲓ (أحبَّ)
        GrammaticalPerson.THIRD_SG_F: "ⲁⲥ",     # ⲁⲥⲙⲉⲓ (أحبَّت)
        GrammaticalPerson.FIRST_PL: "ⲁⲛ",       # ⲁⲛⲙⲉⲓ (أحببنا)
        GrammaticalPerson.SECOND_PL: "ⲁⲣⲉⲧⲉⲛ", # ⲁⲣⲉⲧⲉⲛⲙⲉⲓ (أحببتم)
        GrammaticalPerson.THIRD_PL: "ⲁⲩ",       # ⲁⲩⲙⲉⲓ (أحبّوا)
    }

    _PERFECT_PREFIXES_SAH = {
        GrammaticalPerson.FIRST_SG: "ⲁⲓ",
        GrammaticalPerson.SECOND_SG_M: "ⲁⲕ",
        GrammaticalPerson.SECOND_SG_F: "ⲁⲣ",
        GrammaticalPerson.THIRD_SG_M: "ⲁϥ",
        GrammaticalPerson.THIRD_SG_F: "ⲁⲥ",
        GrammaticalPerson.FIRST_PL: "ⲁⲛ",
        GrammaticalPerson.SECOND_PL: "ⲁⲧⲉⲧⲛ̄",
        GrammaticalPerson.THIRD_PL: "ⲁⲩ",
    }

    # Future I Prefixes (سوابق المستقبل الأول)
    _FUTURE_PREFIXES_BOH = {
        GrammaticalPerson.FIRST_SG: "ϯⲛⲁ",
        GrammaticalPerson.SECOND_SG_M: "ⲭⲛⲁ",
        GrammaticalPerson.SECOND_SG_F: "ⲧⲉⲛⲁ",
        GrammaticalPerson.THIRD_SG_M: "ϥⲛⲁ",
        GrammaticalPerson.THIRD_SG_F: "ⲥⲛⲁ",
        GrammaticalPerson.FIRST_PL: "ⲧⲉⲛⲛⲁ",
        GrammaticalPerson.SECOND_PL: "ⲧⲉⲧⲉⲛⲛⲁ",
        GrammaticalPerson.THIRD_PL: "ⲥⲉⲛⲁ",
    }

    _FUTURE_PREFIXES_SAH = {
        GrammaticalPerson.FIRST_SG: "ϯⲛⲁ",
        GrammaticalPerson.SECOND_SG_M: "ⲕⲛⲁ",
        GrammaticalPerson.SECOND_SG_F: "ⲧⲉⲛⲁ",
        GrammaticalPerson.THIRD_SG_M: "ϥⲛⲁ",
        GrammaticalPerson.THIRD_SG_F: "ⲥⲛⲁ",
        GrammaticalPerson.FIRST_PL: "ⲧⲛ̄ⲛⲁ",
        GrammaticalPerson.SECOND_PL: "ⲧⲉⲧⲛ̄ⲛⲁ",
        GrammaticalPerson.THIRD_PL: "ⲥⲉⲛⲁ",
    }

    # Imperfect / Past Continuous Prefixes (سوابق الماضي الناقص / المستمر - كان يفعل)
    _IMPERFECT_PREFIXES_BOH = {
        GrammaticalPerson.FIRST_SG: "ⲛⲁⲓ",       # ⲛⲁⲓⲙⲉⲓ (كنتُ أحب)
        GrammaticalPerson.SECOND_SG_M: "ⲛⲁⲕ",    # ⲛⲁⲕⲙⲉⲓ (كنتَ تحب)
        GrammaticalPerson.SECOND_SG_F: "ⲛⲁⲣⲉ",   # ⲛⲁⲣⲉⲙⲉⲓ (كنتِ تحبين)
        GrammaticalPerson.THIRD_SG_M: "ⲛⲁϥ",     # ⲛⲁϥⲙⲉⲓ (كان يحب)
        GrammaticalPerson.THIRD_SG_F: "ⲛⲁⲥ",     # ⲛⲁⲥⲙⲉⲓ (كانت تحب)
        GrammaticalPerson.FIRST_PL: "ⲛⲁⲛ",       # ⲛⲁⲛⲙⲉⲓ (كنا نحب)
        GrammaticalPerson.SECOND_PL: "ⲛⲁⲣⲉⲧⲉⲛ", # ⲛⲁⲣⲉⲧⲉⲛⲙⲉⲓ (كنتم تحبون)
        GrammaticalPerson.THIRD_PL: "ⲛⲁⲩ",       # ⲛⲁⲩⲙⲉⲓ (كانوا يحبون)
    }

    _IMPERFECT_PREFIXES_SAH = {
        GrammaticalPerson.FIRST_SG: "ⲛⲉⲓ",
        GrammaticalPerson.SECOND_SG_M: "ⲛⲉⲕ",
        GrammaticalPerson.SECOND_SG_F: "ⲛⲉⲣⲉ",
        GrammaticalPerson.THIRD_SG_M: "ⲛⲉϥ",
        GrammaticalPerson.THIRD_SG_F: "ⲛⲉⲥ",
        GrammaticalPerson.FIRST_PL: "ⲛⲉⲛ",
        GrammaticalPerson.SECOND_PL: "ⲛⲉⲧⲛ̄",
        GrammaticalPerson.THIRD_PL: "ⲛⲉⲩ",
    }

    @classmethod
    def conjugate(
        cls,
        base_verb: str,
        *,
        tense: GrammaticalTense = GrammaticalTense.PRESENT_1,
        person: GrammaticalPerson = GrammaticalPerson.THIRD_SG_M,
        dialect: str = "bohairic",
    ) -> VerbConjugationResult:
        dia = dialect.lower().strip()
        is_sahidic = dia in {"sahidic", "2"}
        is_fayyumic = dia in {"fayyumic", "3"}

        clean_verb = base_verb.strip()

        if tense == GrammaticalTense.PRESENT_1:
            prefixes = cls._PRESENT_PREFIXES_SAH if is_sahidic else cls._PRESENT_PREFIXES_BOH
            tense_name = "الحاضر الأول (Present I)"
        elif tense == GrammaticalTense.PERFECT_1:
            prefixes = cls._PERFECT_PREFIXES_SAH if is_sahidic else cls._PERFECT_PREFIXES_BOH
            tense_name = "الماضي التام الأول (Perfect I)"
        elif tense == GrammaticalTense.IMPERFECT:
            prefixes = cls._IMPERFECT_PREFIXES_SAH if is_sahidic else cls._IMPERFECT_PREFIXES_BOH
            tense_name = "الماضي الناقص المستمر (Imperfect)"
        elif tense == GrammaticalTense.FUTURE_1:
            prefixes = cls._FUTURE_PREFIXES_SAH if is_sahidic else cls._FUTURE_PREFIXES_BOH
            tense_name = "المستقبل الأول (Future I)"
        else:
            prefixes = cls._PRESENT_PREFIXES_BOH
            tense_name = "صيغة الفعل الأساسية"

        prefix = prefixes.get(person, "ϥ")
        conjugated = f"{prefix}{clean_verb}"
        explanation = f"صُرِّف الفعل في زمن {tense_name} للضمير ({person.value}) بإضافة السابقة «{prefix}»."

        return VerbConjugationResult(
            conjugated_form=conjugated,
            prefix=prefix,
            base_verb=clean_verb,
            tense=tense,
            person=person,
            dialect=dialect,
            explanation=explanation,
        )


class NounDeclension:
    """
    Handles Coptic noun declension, definite/indefinite articles, and possessive prefixes.
    """

    # Definite Articles
    # Bohairic: ⲡⲓ- / ϯ- / ⲛⲓ-
    # Sahidic:  ⲡ-  / ⲧ-  / ⲛ-
    # Fayyumic: ⲡ-  / ⲧ-  / ⲛ-

    @classmethod
    def attach_definite_article(
        cls,
        noun: str,
        *,
        gender: GrammaticalGender = GrammaticalGender.MASCULINE,
        number: GrammaticalNumber = GrammaticalNumber.SINGULAR,
        dialect: str = "bohairic",
    ) -> tuple[str, str]:
        """
        Attaches the correct Coptic definite article based on gender, number, and dialect.
        Returns (articled_noun, grammar_explanation).
        """
        clean_noun = noun.strip()
        dia = dialect.lower().strip()
        is_bohairic = dia in {"bohairic", "1"}

        if number == GrammaticalNumber.PLURAL:
            article = "ⲛⲓ" if is_bohairic else "ⲛ"
            explanation = f"أُضيفت أداة التعريف للجمع «{article}-»."
        elif gender == GrammaticalGender.FEMININE:
            article = "ϯ" if is_bohairic else "ⲧ"
            explanation = f"أُضيفت أداة التعريف للمفرد المؤنث «{article}-»."
        else:
            article = "ⲡⲓ" if is_bohairic else "ⲡ"
            explanation = f"أُضيفت أداة التعريف للمفرد المذكر «{article}-»."

        # If already starts with the article, avoid duplicate
        clean_lower = clean_noun.lower()
        art_lower = article.lower()
        if (clean_lower.startswith(art_lower) and len(clean_noun) > len(article)) or clean_lower.startswith(("ⲡⲓ", "ϯ", "ⲛⲓ")):
            return clean_noun, explanation

        return f"{article}{clean_noun}", explanation

    @classmethod
    def attach_indefinite_article(
        cls,
        noun: str,
        *,
        number: GrammaticalNumber = GrammaticalNumber.SINGULAR,
        dialect: str = "bohairic",
    ) -> tuple[str, str]:
        """
        Attaches the Coptic indefinite article (ⲟⲩ- for singular, ϩⲁⲛ- / ϩⲉⲛ- for plural).
        """
        clean_noun = noun.strip()
        dia = dialect.lower().strip()
        is_bohairic = dia in {"bohairic", "1"}

        if number == GrammaticalNumber.PLURAL:
            article = "ϩⲁⲛ" if is_bohairic else "ϩⲉⲛ"
            explanation = f"أُضيفت أداة التنكير للجمع «{article} »."
            return f"{article} {clean_noun}", explanation
        else:
            article = "ⲟⲩ"
            explanation = f"أُضيفت أداة التنكير للمفرد «{article} »."
            return f"{article} {clean_noun}", explanation

    @classmethod
    def attach_possessive_prefix(
        cls,
        noun: str,
        *,
        person: GrammaticalPerson = GrammaticalPerson.FIRST_SG,
        gender: GrammaticalGender = GrammaticalGender.MASCULINE,
        number: GrammaticalNumber = GrammaticalNumber.SINGULAR,
        dialect: str = "bohairic",
    ) -> tuple[str, str]:
        """
        Attaches possessive prefix (ضمائر الملكية: بي، نا، ك، ه، ها، هم).
        E.g. ⲡⲁⲓⲱⲧ (أبي), ⲡⲉⲛⲓⲱⲧ (أبونا).
        """
        clean_noun = noun.strip()
        is_fem = (gender == GrammaticalGender.FEMININE)
        is_pl = (number == GrammaticalNumber.PLURAL)

        base_char = "ⲛ" if is_pl else ("ⲧ" if is_fem else "ⲡ")

        possessive_suffixes = {
            GrammaticalPerson.FIRST_SG: "ⲁ",        # ⲡⲁ- (my)
            GrammaticalPerson.FIRST_PL: "ⲉⲛ",      # ⲡⲉⲛ- (our)
            GrammaticalPerson.SECOND_SG_M: "ⲉⲕ",   # ⲡⲉⲕ- (your m)
            GrammaticalPerson.SECOND_SG_F: "ⲟⲩ",   # ⲡⲟⲩ- / ⲡⲉ-
            GrammaticalPerson.THIRD_SG_M: "ⲉϥ",    # ⲡⲉϥ- (his)
            GrammaticalPerson.THIRD_SG_F: "ⲉⲥ",    # ⲡⲉⲥ- (her)
            GrammaticalPerson.THIRD_PL: "ⲟⲩ",      # ⲡⲟⲩ- (their)
        }

        suffix = possessive_suffixes.get(person, "ⲁ")
        prefix = f"{base_char}{suffix}"
        explanation = f"أُضيف ضمير الملكية «{prefix}-» للملكية ({person.value})."
        return f"{prefix}{clean_noun}", explanation

    # Vilmor letters in Bohairic (حروف فيلمور التي تؤثر على أداة التعريف الخاصة): ⲃ, ⲓ, ⲗ, ⲙ, ⲛ, ⲟⲩ, ⲣ
    VILMOR_LETTERS = ("ⲃ", "ⲓ", "ⲗ", "ⲙ", "ⲛ", "ⲟⲩ", "ⲣ", "Ⲃ", "Ⲓ", "Ⲗ", "Ⲙ", "Ⲛ", "ⲞⲨ", "Ⲣ")

    @classmethod
    def attach_specific_definite_article(
        cls,
        noun: str,
        *,
        gender: GrammaticalGender = GrammaticalGender.MASCULINE,
        number: GrammaticalNumber = GrammaticalNumber.SINGULAR,
        dialect: str = "bohairic",
    ) -> tuple[str, str]:
        """
        Attaches the specific/simple Coptic definite article (أداة التعريف الخاصة / البسيطة):
        - Bohairic:
          * Before Vilmor consonants (ⲃ, ⲓ, ⲗ, ⲙ, ⲛ, ⲟⲩ, ⲣ): ⲫ̀- (m) / ⲑ̀- (f)
          * Before other consonants: ⲡ̀- (m) / ⲧ̀- (f)
          * Plural construct: ⲛⲉⲛ-
        - Sahidic:
          * ⲡ- / ⲧ- / ⲛ- (or ⲡⲉ- / ⲧⲉ- / ⲛⲉ- before consonant clusters)
        """
        clean_noun = noun.strip()
        dia = dialect.lower().strip()
        is_bohairic = dia in {"bohairic", "1"}

        if not is_bohairic:
            # Sahidic simple definite article
            if number == GrammaticalNumber.PLURAL:
                return f"ⲛ{clean_noun}", "أُضيفت أداة التعريف البسيطة للجمع في الصعيدية «ⲛ-»."
            elif gender == GrammaticalGender.FEMININE:
                return f"ⲧ{clean_noun}", "أُضيفت أداة التعريف البسيطة للمؤنث في الصعيدية «ⲧ-»."
            else:
                return f"ⲡ{clean_noun}", "أُضيفت أداة التعريف البسيطة للمذكر في الصعيدية «ⲡ-»."

        # Bohairic specific definite article
        if number == GrammaticalNumber.PLURAL:
            return f"ⲛⲉⲛ{clean_noun}", "أُضيفت أداة التعريف الخاصة للجمع المضاف في البحيرية «ⲛⲉⲛ-»."

        starts_vilmor = any(clean_noun.startswith(v) for v in cls.VILMOR_LETTERS)

        if starts_vilmor:
            if gender == GrammaticalGender.FEMININE:
                art = "ⲑ̀"
                rule = "حرف فيلمور في أول الاسم المؤنث أخذ السابقة الخاصة «ⲑ̀-»."
            else:
                art = "ⲫ̀"
                rule = "حرف فيلمور في أول الاسم المذكر أخذ السابقة الخاصة «ⲫ̀-»."
        else:
            if gender == GrammaticalGender.FEMININE:
                art = "ⲧ̀"
                rule = "الحرف غير فيلمور في أول الاسم المؤنث أخذ السابقة الخاصة «ⲧ̀-»."
            else:
                art = "ⲡ̀"
                rule = "الحرف غير فيلمور في أول الاسم المذكر أخذ السابقة الخاصة «ⲡ̀-»."

        # If already starts with the specific article
        if clean_noun.startswith(("ⲫ̀", "ⲑ̀", "ⲡ̀", "ⲧ̀", "Ⲫ̀", "Ⲑ̀", "Ⲡ̀", "Ⲧ̀")):
            return clean_noun, rule

        return f"{art}{clean_noun}", rule


class ObjectMarker:
    """
    Handles Coptic direct and indirect object markers (علامات المفعول به).
    - Nominal Direct Object: ⲛ̀- / ⲙ̀- (before labials ⲃ, ⲙ, ⲡ, ⲫ, ⲯ in Bohairic; ⲛ̄- / ⲙ̄- in Sahidic).
    - Pronominal Direct Object: ⲙ̀ⲙⲟ= (Bohairic) / ⲙ̄ⲙⲟ= (Sahidic).
    """

    _LABIALS = ("ⲃ", "ⲙ", "ⲡ", "ⲫ", "ⲯ", "Ⲃ", "Ⲙ", "Ⲡ", "Ⲫ", "Ⲯ")

    _PRONOMINAL_OBJECTS_BOH = {
        GrammaticalPerson.FIRST_SG: "ⲙ̀ⲙⲟⲓ",      # إياي
        GrammaticalPerson.SECOND_SG_M: "ⲙ̀ⲙⲟⲕ",   # إياكَ
        GrammaticalPerson.SECOND_SG_F: "ⲙ̀ⲙⲟ",    # إياكِ
        GrammaticalPerson.THIRD_SG_M: "ⲙ̀ⲙⲟϥ",    # إياه
        GrammaticalPerson.THIRD_SG_F: "ⲙ̀ⲙⲟⲥ",    # إياها
        GrammaticalPerson.FIRST_PL: "ⲙ̀ⲙⲟⲛ",      # إيانا
        GrammaticalPerson.SECOND_PL: "ⲙ̀ⲙⲱⲧⲉⲛ",   # إياكم
        GrammaticalPerson.THIRD_PL: "ⲙ̀ⲙⲱⲟⲩ",     # إياهم
    }

    _PRONOMINAL_OBJECTS_SAH = {
        GrammaticalPerson.FIRST_SG: "ⲙ̄ⲙⲟⲓ",
        GrammaticalPerson.SECOND_SG_M: "ⲙ̄ⲙⲟⲕ",
        GrammaticalPerson.SECOND_SG_F: "ⲙ̄ⲙⲟ",
        GrammaticalPerson.THIRD_SG_M: "ⲙ̄ⲙⲟϥ",
        GrammaticalPerson.THIRD_SG_F: "ⲙ̄ⲙⲟⲥ",
        GrammaticalPerson.FIRST_PL: "ⲙ̄ⲙⲟⲛ",
        GrammaticalPerson.SECOND_PL: "ⲙ̄ⲙⲱⲧⲛ̄",
        GrammaticalPerson.THIRD_PL: "ⲙ̄ⲙⲟⲟⲩ",
    }

    @classmethod
    def get_nominal_marker(cls, next_word: str, dialect: str = "bohairic") -> str:
        """Returns ⲙ̀- (or ⲙ̄-) before labial consonants, else ⲛ̀- (or ⲛ̄-)."""
        dia = dialect.lower().strip()
        is_bohairic = dia in {"bohairic", "1"}
        clean = next_word.strip()
        starts_labial = any(clean.startswith(lab) for lab in cls._LABIALS)

        if is_bohairic:
            return "ⲙ̀" if starts_labial else "ⲛ̀"
        return "ⲙ̄" if starts_labial else "ⲛ̄"

    @classmethod
    def get_pronominal_marker(cls, person: GrammaticalPerson, dialect: str = "bohairic") -> str:
        """Returns the suffixed pronominal object form (ⲙ̀ⲙⲟ= / ⲙ̄ⲙⲟ=)."""
        dia = dialect.lower().strip()
        is_bohairic = dia in {"bohairic", "1"}
        table = cls._PRONOMINAL_OBJECTS_BOH if is_bohairic else cls._PRONOMINAL_OBJECTS_SAH
        return table.get(person, "ⲙ̀ⲙⲟϥ")


class GenitiveLinker:
    """
    Handles Coptic Genitive Relations (علامات الإضافة):
    - Direct Genitive (إضافة مباشرة): ⲛ̀- / ⲙ̀- (before labials).
    - Indirect Genitive (إضافة غير مباشرة): ⲛ̀ⲧⲉ (Bohairic) / ⲛ̄ⲧⲉ (Sahidic).
    """

    @classmethod
    def get_direct_marker(cls, next_word: str, dialect: str = "bohairic") -> str:
        return ObjectMarker.get_nominal_marker(next_word, dialect=dialect)

    @classmethod
    def get_indirect_marker(cls, dialect: str = "bohairic") -> str:
        dia = dialect.lower().strip()
        return "ⲛ̀ⲧⲉ" if dia in {"bohairic", "1"} else "ⲛ̄ⲧⲉ"


class CopticNumerals:
    """
    Coptic Numerals System (نظام الأعداد القبطية):
    - Cardinal numbers (1–10, 100, 1000) for masculine and feminine.
    - Genitive connection rule (ربط العدد بالمعدود بواسطة ⲛ̀- / ⲙ̀-).
    - Unique adjectival rule for 'one' (ⲟⲩⲱⲧ).
    """

    CARDINALS_BOHAIRIC = {
        1: {"m": "ⲟⲩⲁⲓ", "f": "ⲟⲩⲓ", "single": "ⲟⲩⲱⲧ"},
        2: {"m": "ⲥⲛⲁⲩ", "f": "ⲥⲛⲟⲩϯ"},
        3: {"m": "ϣⲟⲙⲧ", "f": "ϣⲟⲙϯ"},
        4: {"m": "ϥⲧⲟⲟⲩ", "f": "ϥϯ"},
        5: {"m": "ϯⲟⲩ", "f": "ϯ"},
        6: {"m": "ⲥⲟⲟⲩ", "f": "ⲥⲟ"},
        7: {"m": "ϣⲁϣϥ", "f": "ϣⲁϣϥⲓ"},
        8: {"m": "ϣⲙⲏⲛ", "f": "ϣⲙⲏⲛⲓ"},
        9: {"m": "ⲯⲓⲧ", "f": "ⲯⲓϯ"},
        10: {"m": "ⲙⲏⲧ", "f": "ⲙⲏϯ"},
        100: {"m": "ϣⲉ", "f": "ϣⲉ"},
        1000: {"m": "ϣⲟ", "f": "ϣⲟ"},
    }

    CARDINALS_SAHIDIC = {
        1: {"m": "ⲟⲩⲁ", "f": "ⲟⲩⲉⲓ", "single": "ⲟⲩⲱⲧ"},
        2: {"m": "ⲥⲛⲁⲩ", "f": "ⲥⲛ̄ⲧⲉ"},
        3: {"m": "ϣⲟⲙⲛ̄ⲧ", "f": "ϣⲟⲙⲧⲉ"},
        4: {"m": "ϥⲧⲟⲟⲩ", "f": "ϥⲧⲟⲉ"},
        5: {"m": "ϯⲟⲩ", "f": "ϯⲉ"},
        6: {"m": "ⲥⲟⲟⲩ", "f": "ⲥⲟⲉ"},
        7: {"m": "ϣⲁϣϥ̄", "f": "ϣⲁϣϥⲉ"},
        8: {"m": "ϣⲙⲟⲩⲛ", "f": "ϣⲙⲟⲩⲛⲉ"},
        9: {"m": "ⲯⲓⲥ", "f": "ⲯⲓⲥⲉ"},
        10: {"m": "ⲙⲏⲧ", "f": "ⲙⲏⲧⲉ"},
        100: {"m": "ϣⲉ", "f": "ϣⲉ"},
        1000: {"m": "ϣⲟ", "f": "ϣⲟ"},
    }

    AR_WORD_TO_NUMBER = {
        "واحد": 1, "واحدة": 1, "واحده": 1, "أحد": 1, "احد": 1,
        "اثنان": 2, "اثنين": 2, "اثنتان": 2, "اثنتين": 2, "زوج": 2,
        "ثلاثة": 3, "ثلاثه": 3, "ثلاث": 3,
        "اربعة": 4, "أربعة": 4, "اربعه": 4, "أربعه": 4, "اربع": 4, "أربع": 4,
        "خمسة": 5, "خمسه": 5, "خمس": 5,
        "ستة": 6, "سته": 6, "ست": 6,
        "سبعة": 7, "سبعه": 7, "سبع": 7,
        "ثمانية": 8, "ثمانيه": 8, "ثمان": 8, "ثماني": 8,
        "تسعة": 9, "تسعه": 9, "تسع": 9,
        "عشرة": 10, "عشره": 10, "عشر": 10,
        "مائة": 100, "مائه": 100, "مئة": 100, "مئه": 100,
        "الف": 1000, "ألف": 1000,
    }

    @classmethod
    def get_cardinal(
        cls,
        number: int,
        *,
        gender: GrammaticalGender = GrammaticalGender.MASCULINE,
        dialect: str = "bohairic",
    ) -> str:
        """Returns the cardinal numeral for a given number, gender, and dialect."""
        dia = dialect.lower().strip()
        is_sahidic = dia in {"sahidic", "2"}
        table = cls.CARDINALS_SAHIDIC if is_sahidic else cls.CARDINALS_BOHAIRIC
        entry = table.get(number)
        if not entry:
            return str(number)
        g_key = "f" if gender == GrammaticalGender.FEMININE else "m"
        return entry.get(g_key, entry.get("m", str(number)))

    @classmethod
    def format_numeral_with_noun(
        cls,
        number: int,
        noun_coptic: str,
        *,
        gender: GrammaticalGender = GrammaticalGender.MASCULINE,
        dialect: str = "bohairic",
    ) -> tuple[str, str]:
        """
        Formats a number with a noun following Coptic grammar rules:
        - 1: Noun takes indefinite article and is followed by ⲛ̀ⲟⲩⲱⲧ (e.g., ⲟⲩⲛⲟⲩϯ ⲛ̀ⲟⲩⲱⲧ 'one God').
        - 2–10: Numeral precedes noun, connected by ⲛ̀- / ⲙ̀- (e.g., ⲥⲛⲁⲩ ⲛ̀ⲣⲱⲙⲓ 'two men').
        """
        dia = dialect.lower().strip()
        is_bohairic = dia in {"bohairic", "1"}
        clean_noun = noun_coptic.strip()

        if number == 1:
            linker = "ⲛ̀" if is_bohairic else "ⲛ̄"
            phrase = f"ⲟⲩ{clean_noun} {linker}ⲟⲩⲱⲧ"
            explanation = f"العدد 1 يعامل كصفة تتبع الاسم المنكر: «{phrase}»."
            return phrase, explanation

        num_str = cls.get_cardinal(number, gender=gender, dialect=dialect)
        linker = ObjectMarker.get_nominal_marker(clean_noun, dialect=dialect)
        phrase = f"{num_str} {linker}{clean_noun}"
        explanation = f"العدد «{num_str}» يسبق المعدود ويُربط به بواسطة أداة الإضافة «{linker}»: «{phrase}»."
        return phrase, explanation

