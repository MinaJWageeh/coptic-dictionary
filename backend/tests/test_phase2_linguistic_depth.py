from __future__ import annotations

import pytest
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
from app.services.syntax import compose_coptic_sentence_with_notes


def test_verb_conjugation_across_tenses_and_persons() -> None:
    # 1. Present I (Bohairic)
    res_1s_boh = VerbConjugator.conjugate("ⲙⲉⲓ", tense=GrammaticalTense.PRESENT_1, person=GrammaticalPerson.FIRST_SG, dialect="bohairic")
    assert res_1s_boh.conjugated_form == "ϯⲙⲉⲓ"
    assert res_1s_boh.prefix == "ϯ"

    res_1p_boh = VerbConjugator.conjugate("ⲙⲉⲓ", tense=GrammaticalTense.PRESENT_1, person=GrammaticalPerson.FIRST_PL, dialect="bohairic")
    assert res_1p_boh.conjugated_form == "ⲧⲉⲛⲙⲉⲓ"

    # Present I (Sahidic)
    res_1p_sah = VerbConjugator.conjugate("ⲙⲉ", tense=GrammaticalTense.PRESENT_1, person=GrammaticalPerson.FIRST_PL, dialect="sahidic")
    assert res_1p_sah.conjugated_form == "ⲧⲛ̄ⲙⲉ"

    # 2. Perfect I (Past)
    res_past_3sm = VerbConjugator.conjugate("ϣⲗⲏⲗ", tense=GrammaticalTense.PERFECT_1, person=GrammaticalPerson.THIRD_SG_M, dialect="bohairic")
    assert res_past_3sm.conjugated_form == "ⲁϥϣⲗⲏⲗ"

    res_past_1p = VerbConjugator.conjugate("ϣⲗⲏⲗ", tense=GrammaticalTense.PERFECT_1, person=GrammaticalPerson.FIRST_PL, dialect="bohairic")
    assert res_past_1p.conjugated_form == "ⲁⲛϣⲗⲏⲗ"

    # 3. Future I
    res_fut_1s = VerbConjugator.conjugate("ϣⲗⲏⲗ", tense=GrammaticalTense.FUTURE_1, person=GrammaticalPerson.FIRST_SG, dialect="bohairic")
    assert res_fut_1s.conjugated_form == "ϯⲛⲁϣⲗⲏⲗ"

    res_fut_3sm = VerbConjugator.conjugate("ϣⲗⲏⲗ", tense=GrammaticalTense.FUTURE_1, person=GrammaticalPerson.THIRD_SG_M, dialect="bohairic")
    assert res_fut_3sm.conjugated_form == "ϥⲛⲁϣⲗⲏⲗ"


def test_noun_declension_articles_and_possessives() -> None:
    # 1. Definite articles by gender/number in Bohairic
    m_boh, _ = NounDeclension.attach_definite_article("ⲟⲩⲣⲟ", gender=GrammaticalGender.MASCULINE, dialect="bohairic")
    assert m_boh == "ⲡⲓⲟⲩⲣⲟ"

    f_boh, _ = NounDeclension.attach_definite_article("ⲟⲩⲣⲱ", gender=GrammaticalGender.FEMININE, dialect="bohairic")
    assert f_boh == "ϯⲟⲩⲣⲱ"

    pl_boh, _ = NounDeclension.attach_definite_article("ⲟⲩⲣⲱⲟⲩ", number=GrammaticalNumber.PLURAL, dialect="bohairic")
    assert pl_boh == "ⲛⲓⲟⲩⲣⲱⲟⲩ"

    # 2. Definite articles in Sahidic
    m_sah, _ = NounDeclension.attach_definite_article("ⲣⲣⲟ", gender=GrammaticalGender.MASCULINE, dialect="sahidic")
    assert m_sah == "ⲡⲣⲣⲟ"

    f_sah, _ = NounDeclension.attach_definite_article("ⲣⲣⲱ", gender=GrammaticalGender.FEMININE, dialect="sahidic")
    assert f_sah == "ⲧⲣⲣⲱ"

    # 3. Indefinite articles
    sg_indef, _ = NounDeclension.attach_indefinite_article("ⲣⲱⲙⲓ", number=GrammaticalNumber.SINGULAR, dialect="bohairic")
    assert sg_indef == "ⲟⲩ ⲣⲱⲙⲓ"

    pl_indef_boh, _ = NounDeclension.attach_indefinite_article("ⲣⲱⲙⲓ", number=GrammaticalNumber.PLURAL, dialect="bohairic")
    assert pl_indef_boh == "ϩⲁⲛ ⲣⲱⲙⲓ"

    pl_indef_sah, _ = NounDeclension.attach_indefinite_article("ⲣⲱⲙⲉ", number=GrammaticalNumber.PLURAL, dialect="sahidic")
    assert pl_indef_sah == "ϩⲉⲛ ⲣⲱⲙⲉ"

    # 4. Possessive prefixes
    my_father, _ = NounDeclension.attach_possessive_prefix("ⲓⲱⲧ", person=GrammaticalPerson.FIRST_SG)
    assert my_father == "ⲡⲁⲓⲱⲧ"

    our_father, _ = NounDeclension.attach_possessive_prefix("ⲓⲱⲧ", person=GrammaticalPerson.FIRST_PL)
    assert our_father == "ⲡⲉⲛⲓⲱⲧ"


def test_sentence_type_detection() -> None:
    # 1. Negative past
    neg_past = SentenceTypeDetector.analyze("لم يصلّ")
    assert neg_past.sentence_type == SentenceType.NEGATIVE
    assert neg_past.negation_kind == NegationKind.PAST

    # 2. Negative future
    neg_fut = SentenceTypeDetector.analyze("لن يحب")
    assert neg_fut.sentence_type == SentenceType.NEGATIVE
    assert neg_fut.negation_kind == NegationKind.FUTURE

    # 3. Negative present
    neg_pres = SentenceTypeDetector.analyze("لا يعبد")
    assert neg_pres.sentence_type == SentenceType.NEGATIVE
    assert neg_pres.negation_kind == NegationKind.PRESENT

    # 4. Negative copula
    neg_cop = SentenceTypeDetector.analyze("ليس صالحا")
    assert neg_cop.sentence_type == SentenceType.NEGATIVE
    assert neg_cop.negation_kind == NegationKind.COPULA

    # 5. Nominal sentence with copula gender assignment
    nom_m = SentenceTypeDetector.analyze("الملك عظيم")
    assert nom_m.sentence_type == SentenceType.NOMINAL
    assert nom_m.subject_gender == GrammaticalGender.MASCULINE
    assert nom_m.copula_coptic == "ⲡⲉ"

    nom_f = SentenceTypeDetector.analyze("الكنيسة مقدسة")
    assert nom_f.sentence_type == SentenceType.NOMINAL
    assert nom_f.subject_gender == GrammaticalGender.FEMININE
    assert nom_f.copula_coptic == "ⲧⲉ"

    nom_pl = SentenceTypeDetector.analyze("الملوك عظام")
    assert nom_pl.subject_number == GrammaticalNumber.PLURAL
    assert nom_pl.copula_coptic == "ⲛⲉ"


def test_gender_number_adjective_agreement_in_syntax_composer() -> None:
    # Masculine noun + adjective in Bohairic
    breakdown_m = [
        {"arabic": "الملك", "coptic": "ⲡⲓⲟⲩⲣⲟ", "status": "known", "part_of_speech": "noun"},
        {"arabic": "الصالح", "coptic": "ⲁⲅⲁⲑⲟⲥ", "status": "known", "part_of_speech": "adjective"},
    ]
    res_m = compose_coptic_sentence_with_notes(breakdown_m, dialect_id=1)
    assert "ⲉⲑⲛⲁⲛⲉϥ" in res_m.coptic_text  # masculine adjective suffix -ϥ

    # Feminine noun + adjective in Bohairic
    breakdown_f = [
        {"arabic": "الكنيسة", "coptic": "ϯⲉⲕⲕⲗⲏⲥⲓⲁ", "status": "known", "part_of_speech": "noun"},
        {"arabic": "الصالحة", "coptic": "ⲁⲅⲁⲑⲟⲥ", "status": "known", "part_of_speech": "adjective"},
    ]
    res_f = compose_coptic_sentence_with_notes(breakdown_f, dialect_id=1)
    assert "ⲉⲑⲛⲁⲛⲉⲥ" in res_f.coptic_text  # feminine adjective suffix -ⲥ


def test_dialect_specific_grammar_priorities() -> None:
    # Test preposition and conjunction in Bohairic vs Sahidic
    breakdown = [
        {"arabic": "في", "coptic": "ϧⲉⲛ", "status": "known", "part_of_speech": "preposition"},
        {"arabic": "السماء", "coptic": "ⲧⲫⲉ", "status": "known", "part_of_speech": "noun"},
        {"arabic": "و", "coptic": "ⲟⲩⲟϩ", "status": "known", "part_of_speech": "conjunction"},
        {"arabic": "على", "coptic": "ϩⲓϫⲉⲛ", "status": "known", "part_of_speech": "preposition"},
        {"arabic": "الارض", "coptic": "ⲡⲓⲕⲁϩⲓ", "status": "known", "part_of_speech": "noun"},
    ]

    # Bohairic (dialect_id=1) uses ϧⲉⲛ, ⲟⲩⲟϩ, ϩⲓϫⲉⲛ
    res_boh = compose_coptic_sentence_with_notes(breakdown, dialect_id=1)
    assert "ϧⲉⲛ" in res_boh.coptic_text
    assert "ϩⲓϫⲉⲛ" in res_boh.coptic_text
    assert "ⲟⲩⲟϩ" in res_boh.coptic_text

    # Sahidic (dialect_id=2) uses ϩⲛ̄, ⲁⲩⲱ, ⲉϫⲛ̄
    res_sah = compose_coptic_sentence_with_notes(breakdown, dialect_id=2)
    assert "ϩⲛ̄" in res_sah.coptic_text
    assert "ⲉϫⲛ̄" in res_sah.coptic_text
    assert "ⲁⲩⲱ" in res_sah.coptic_text


def test_negation_sentence_composition() -> None:
    # 1. Past negation: لم يحب
    breakdown_past_neg = [
        {"arabic": "لم", "coptic": "", "status": "known", "part_of_speech": "particle"},
        {"arabic": "يحب", "coptic": "ⲙⲉⲓ", "status": "known", "part_of_speech": "verb"},
    ]
    res_past = compose_coptic_sentence_with_notes(breakdown_past_neg, dialect_id=1)
    assert "ⲙ̀ⲡⲉϥⲙⲉⲓ" in res_past.coptic_text

    # 2. Present negation: لا يحب
    breakdown_pres_neg = [
        {"arabic": "لا", "coptic": "", "status": "known", "part_of_speech": "particle"},
        {"arabic": "يحب", "coptic": "ⲙⲉⲓ", "status": "known", "part_of_speech": "verb"},
    ]
    res_pres = compose_coptic_sentence_with_notes(breakdown_pres_neg, dialect_id=1)
    assert "ⲛ̀ϥⲙⲉⲓ ⲁⲛ" in res_pres.coptic_text


def test_nominal_sentence_copula_composition() -> None:
    # 1. Nominal sentence with explicit copular verb: انا اكون خبز الحياة -> ⲁⲛⲟⲕ ⲡⲉ ⲡⲓⲱⲓⲕ ⲛ̀ⲧⲉ Ⲡⲓⲱⲛϧ
    breakdown_explicit = [
        {"arabic": "انا", "coptic": "ⲁⲛⲟⲕ", "status": "known", "part_of_speech": "pronoun"},
        {"arabic": "اكون", "coptic": "ⲛⲁϥ", "status": "known", "part_of_speech": "verb"},
        {"arabic": "خبز", "coptic": "ⲱⲓⲕ", "status": "known", "part_of_speech": "noun"},
        {"arabic": "الحياة", "coptic": "Ⲡⲓⲱⲛϧ", "status": "known", "part_of_speech": "noun"},
    ]
    res_explicit = compose_coptic_sentence_with_notes(breakdown_explicit, dialect_id=1)
    assert "ⲡⲉ" in res_explicit.coptic_text
    assert "ⲛⲁϥ" not in res_explicit.coptic_text
    assert res_explicit.coptic_text == "ⲁⲛⲟⲕ ⲡⲉ ⲡⲓⲱⲓⲕ ⲛ̀ⲧⲉ Ⲡⲓⲱⲛϧ"
    copula_notes = [n for n in res_explicit.grammar_notes if "رابط الكينونة" in n["title"]]
    assert len(copula_notes) > 0

    # 2. Nominal sentence with implicit copula: انا خبز الحياة -> ⲁⲛⲟⲕ ⲡⲉ ⲡⲓⲱⲓⲕ ⲛ̀ⲧⲉ Ⲡⲓⲱⲛϧ
    breakdown_implicit = [
        {"arabic": "انا", "coptic": "ⲁⲛⲟⲕ", "status": "known", "part_of_speech": "pronoun"},
        {"arabic": "خبز", "coptic": "ⲱⲓⲕ", "status": "known", "part_of_speech": "noun"},
        {"arabic": "الحياة", "coptic": "Ⲡⲓⲱⲛϧ", "status": "known", "part_of_speech": "noun"},
    ]
    res_implicit = compose_coptic_sentence_with_notes(breakdown_implicit, dialect_id=1)
    assert res_implicit.coptic_text == "ⲁⲛⲟⲕ ⲡⲉ ⲡⲓⲱⲓⲕ ⲛ̀ⲧⲉ Ⲡⲓⲱⲛϧ"


def test_attached_prepositions_and_genitive_composition() -> None:
    # 1. باسم الاب -> ϧⲉⲛ ⲫ̀ⲣⲁⲛ ⲙ̀Ⲫⲓⲱⲧ (Bohairic)
    breakdown_name_of_father_boh = [
        {"arabic": "باسم", "coptic": "ⲣⲁⲛ", "status": "known", "part_of_speech": "noun"},
        {"arabic": "الاب", "coptic": "Ⲫⲓⲱⲧ", "status": "known", "part_of_speech": "noun"},
    ]
    res_boh = compose_coptic_sentence_with_notes(breakdown_name_of_father_boh, dialect_id=1)
    assert res_boh.coptic_text == "ϧⲉⲛ ⲫ̀ⲣⲁⲛ ⲙ̀Ⲫⲓⲱⲧ"
    prep_notes = [n for n in res_boh.grammar_notes if "حرف الجر المتصل" in n["title"]]
    assert len(prep_notes) > 0

    # 2. باسم الاب -> ϩⲙ̄ ⲡⲣⲁⲛ ⲙ̄Ⲫⲓⲱⲧ (Sahidic)
    res_sah = compose_coptic_sentence_with_notes(breakdown_name_of_father_boh, dialect_id=2)
    assert res_sah.coptic_text == "ϩⲙ̄ ⲡⲣⲁⲛ ⲙ̄Ⲫⲓⲱⲧ"

    # 3. بالروح القدس -> ϧⲉⲛ ⲡⲓⲡⲛⲉⲩⲙⲁ ⲉⲑⲟⲩⲁⲃ (Bohairic)
    breakdown_spirit = [
        {"arabic": "بالروح", "coptic": "ⲡⲛⲉⲩⲙⲁ", "status": "known", "part_of_speech": "noun"},
        {"arabic": "القدس", "coptic": "ⲉⲑⲟⲩⲁⲃ", "status": "known", "part_of_speech": "adjective"},
    ]
    res_spirit = compose_coptic_sentence_with_notes(breakdown_spirit, dialect_id=1)
    assert res_spirit.coptic_text == "ϧⲉⲛ ⲡⲓⲡⲛⲉⲩⲙⲁ ⲉⲑⲟⲩⲁⲃ"

    # 4. لله -> ⲉ̀Ⲫⲛⲟⲩϯ
    breakdown_to_god = [
        {"arabic": "لله", "coptic": "Ⲫⲛⲟⲩϯ", "status": "known", "part_of_speech": "noun"},
    ]
    res_god = compose_coptic_sentence_with_notes(breakdown_to_god, dialect_id=1)
    assert res_god.coptic_text == "ⲉ̀Ⲫⲛⲟⲩϯ"


def test_comprehensive_prepositions_across_dialects() -> None:
    # 1. في السماء وعلى الارض (Bohairic)
    breakdown_heaven_earth = [
        {"arabic": "في", "coptic": "ϧⲉⲛ", "status": "known", "part_of_speech": "preposition"},
        {"arabic": "السماء", "coptic": "ⲧⲫⲉ", "status": "known", "part_of_speech": "noun"},
        {"arabic": "وعلى", "coptic": "ϩⲓϫⲉⲛ", "status": "known", "part_of_speech": "preposition"},
        {"arabic": "الارض", "coptic": "ⲡⲕⲁϩⲓ", "status": "known", "part_of_speech": "noun"},
    ]
    res_boh = compose_coptic_sentence_with_notes(breakdown_heaven_earth, dialect_id=1)
    assert res_boh.coptic_text == "ϧⲉⲛ ⲧⲫⲉ ⲟⲩⲟϩ ϩⲓϫⲉⲛ ⲡⲕⲁϩⲓ"

    # 2. في السماء وعلى الارض (Sahidic)
    res_sah = compose_coptic_sentence_with_notes(breakdown_heaven_earth, dialect_id=2)
    assert res_sah.coptic_text == "ϩⲛ̄ ⲧⲫⲉ ⲁⲩⲱ ⲉϫⲛ̄ ⲡⲕⲁϩⲓ"

    # 3. تحت السماء -> ϧⲁ ⲧⲫⲉ (Bohairic) / ϩⲁ ⲧⲫⲉ (Sahidic)
    breakdown_under = [
        {"arabic": "تحت", "coptic": "ϧⲁ", "status": "known", "part_of_speech": "preposition"},
        {"arabic": "السماء", "coptic": "ⲧⲫⲉ", "status": "known", "part_of_speech": "noun"},
    ]
    assert compose_coptic_sentence_with_notes(breakdown_under, dialect_id=1).coptic_text == "ϧⲁ ⲧⲫⲉ"
    assert compose_coptic_sentence_with_notes(breakdown_under, dialect_id=2).coptic_text == "ϩⲁ ⲧⲫⲉ"

    # 4. بدون خوف -> ⲁϭⲛⲉ ϩⲟϯ (Bohairic) / ⲁϫⲛ̄ ϩⲟϯ (Sahidic)
    breakdown_without = [
        {"arabic": "بدون", "coptic": "ⲁϭⲛⲉ", "status": "known", "part_of_speech": "preposition"},
        {"arabic": "خوف", "coptic": "ϩⲟϯ", "status": "known", "part_of_speech": "noun"},
    ]
    assert compose_coptic_sentence_with_notes(breakdown_without, dialect_id=1).coptic_text == "ⲁϭⲛⲉ ϩⲟϯ"
    assert compose_coptic_sentence_with_notes(breakdown_without, dialect_id=2).coptic_text == "ⲁϫⲛ̄ ϩⲟϯ"


def test_imperfect_tense_conjugation() -> None:
    # 1. Bohairic Imperfect (الماضي الناقص المستمر)
    res_boh_1s = VerbConjugator.conjugate("ⲥⲱⲧⲉⲙ", tense=GrammaticalTense.IMPERFECT, person=GrammaticalPerson.FIRST_SG, dialect="bohairic")
    assert res_boh_1s.conjugated_form == "ⲛⲁⲓⲥⲱⲧⲉⲙ"
    assert res_boh_1s.prefix == "ⲛⲁⲓ"

    res_boh_3sm = VerbConjugator.conjugate("ⲙⲉⲓ", tense=GrammaticalTense.IMPERFECT, person=GrammaticalPerson.THIRD_SG_M, dialect="bohairic")
    assert res_boh_3sm.conjugated_form == "ⲛⲁϥⲙⲉⲓ"

    res_boh_1p = VerbConjugator.conjugate("ϣⲗⲏⲗ", tense=GrammaticalTense.IMPERFECT, person=GrammaticalPerson.FIRST_PL, dialect="bohairic")
    assert res_boh_1p.conjugated_form == "ⲛⲁⲛϣⲗⲏⲗ"

    # 2. Sahidic Imperfect
    res_sah_1s = VerbConjugator.conjugate("ⲥⲱⲧⲙ̄", tense=GrammaticalTense.IMPERFECT, person=GrammaticalPerson.FIRST_SG, dialect="sahidic")
    assert res_sah_1s.conjugated_form == "ⲛⲉⲓⲥⲱⲧⲙ̄"

    res_sah_3sm = VerbConjugator.conjugate("ⲙⲉ", tense=GrammaticalTense.IMPERFECT, person=GrammaticalPerson.THIRD_SG_M, dialect="sahidic")
    assert res_sah_3sm.conjugated_form == "ⲛⲉϥⲙⲉ"


def test_specific_definite_articles_and_vilmor_rule() -> None:
    # 1. Bohairic Masculine before Vilmor (ⲫ̀-): ⲣⲁⲛ -> ⲫ̀ⲣⲁⲛ, ⲓⲱⲧ -> ⲫ̀ⲓⲱⲧ, ⲙⲱⲓⲧ -> ⲫ̀ⲙⲱⲓⲧ
    m_vilmor, note_mv = NounDeclension.attach_specific_definite_article("ⲣⲁⲛ", gender=GrammaticalGender.MASCULINE, dialect="bohairic")
    assert m_vilmor == "ⲫ̀ⲣⲁⲛ"
    assert "فيلمور" in note_mv

    # 2. Bohairic Feminine before Vilmor (ⲑ̀-): ⲙⲁⲩ -> ⲑ̀ⲙⲁⲩ
    f_vilmor, note_fv = NounDeclension.attach_specific_definite_article("ⲙⲁⲩ", gender=GrammaticalGender.FEMININE, dialect="bohairic")
    assert f_vilmor == "ⲑ̀ⲙⲁⲩ"
    assert "فيلمور" in note_fv

    # 3. Bohairic Masculine before Non-Vilmor (ⲡ̀-): ϭⲟⲓⲥ -> ⲡ̀ϭⲟⲓⲥ, ϣⲏⲣⲓ -> ⲡ̀ϣⲏⲣⲓ
    m_non_vilmor, _ = NounDeclension.attach_specific_definite_article("ϭⲟⲓⲥ", gender=GrammaticalGender.MASCULINE, dialect="bohairic")
    assert m_non_vilmor == "ⲡ̀ϭⲟⲓⲥ"

    # 4. Bohairic Feminine before Non-Vilmor (ⲧ̀-): ⲫⲉ -> ⲧ̀ⲫⲉ
    f_non_vilmor, _ = NounDeclension.attach_specific_definite_article("ⲫⲉ", gender=GrammaticalGender.FEMININE, dialect="bohairic")
    assert f_non_vilmor == "ⲧ̀ⲫⲉ"

    # 5. Bohairic Plural Construct (ⲛⲉⲛ-): ⲓⲟϯ -> ⲛⲉⲛⲓⲟϯ
    pl_specific, _ = NounDeclension.attach_specific_definite_article("ⲓⲟϯ", number=GrammaticalNumber.PLURAL, dialect="bohairic")
    assert pl_specific == "ⲛⲉⲛⲓⲟϯ"


def test_object_markers_nominal_and_pronominal() -> None:
    # 1. Nominal object markers
    # Labials: ⲃ, ⲙ, ⲡ, ⲫ, ⲯ -> ⲙ̀ in Bohairic, ⲙ̄ in Sahidic
    assert ObjectMarker.get_nominal_marker("Ⲫⲛⲟⲩϯ", dialect="bohairic") == "ⲙ̀"
    assert ObjectMarker.get_nominal_marker("ⲙⲱⲓⲧ", dialect="bohairic") == "ⲙ̀"
    assert ObjectMarker.get_nominal_marker("ⲡⲓⲱⲛϧ", dialect="bohairic") == "ⲙ̀"
    assert ObjectMarker.get_nominal_marker("ⲣⲁⲛ", dialect="bohairic") == "ⲛ̀"

    assert ObjectMarker.get_nominal_marker("ⲡⲛⲟⲩⲧⲉ", dialect="sahidic") == "ⲙ̄"
    assert ObjectMarker.get_nominal_marker("ⲣⲁⲛ", dialect="sahidic") == "ⲛ̄"

    # 2. Pronominal object markers: ⲙ̀ⲙⲟ=
    assert ObjectMarker.get_pronominal_marker(GrammaticalPerson.FIRST_SG, dialect="bohairic") == "ⲙ̀ⲙⲟⲓ"
    assert ObjectMarker.get_pronominal_marker(GrammaticalPerson.SECOND_SG_M, dialect="bohairic") == "ⲙ̀ⲙⲟⲕ"
    assert ObjectMarker.get_pronominal_marker(GrammaticalPerson.THIRD_SG_M, dialect="bohairic") == "ⲙ̀ⲙⲟϥ"
    assert ObjectMarker.get_pronominal_marker(GrammaticalPerson.THIRD_SG_F, dialect="bohairic") == "ⲙ̀ⲙⲟⲥ"
    assert ObjectMarker.get_pronominal_marker(GrammaticalPerson.FIRST_PL, dialect="bohairic") == "ⲙ̀ⲙⲟⲛ"
    assert ObjectMarker.get_pronominal_marker(GrammaticalPerson.SECOND_PL, dialect="bohairic") == "ⲙ̀ⲙⲱⲧⲉⲛ"
    assert ObjectMarker.get_pronominal_marker(GrammaticalPerson.THIRD_PL, dialect="bohairic") == "ⲙ̀ⲙⲱⲟⲩ"

    # Sahidic pronominal object markers
    assert ObjectMarker.get_pronominal_marker(GrammaticalPerson.THIRD_SG_M, dialect="sahidic") == "ⲙ̄ⲙⲟϥ"
    assert ObjectMarker.get_pronominal_marker(GrammaticalPerson.SECOND_PL, dialect="sahidic") == "ⲙ̄ⲙⲱⲧⲛ̄"


def test_genitive_linkers_direct_and_indirect() -> None:
    # 1. Direct genitive: ⲛ̀- / ⲙ̀-
    assert GenitiveLinker.get_direct_marker("Ⲫⲓⲱⲧ", dialect="bohairic") == "ⲙ̀"
    assert GenitiveLinker.get_direct_marker("ⲱⲛϧ", dialect="bohairic") == "ⲛ̀"

    # 2. Indirect genitive: ⲛ̀ⲧⲉ (Bohairic) vs ⲛ̄ⲧⲉ (Sahidic)
    assert GenitiveLinker.get_indirect_marker(dialect="bohairic") == "ⲛ̀ⲧⲉ"
    assert GenitiveLinker.get_indirect_marker(dialect="sahidic") == "ⲛ̄ⲧⲉ"


def test_coptic_numerals_and_counting_rules() -> None:
    # 1. Cardinals 1–10 in Bohairic
    assert CopticNumerals.get_cardinal(1, gender=GrammaticalGender.MASCULINE, dialect="bohairic") == "ⲟⲩⲁⲓ"
    assert CopticNumerals.get_cardinal(1, gender=GrammaticalGender.FEMININE, dialect="bohairic") == "ⲟⲩⲓ"
    assert CopticNumerals.get_cardinal(2, gender=GrammaticalGender.MASCULINE, dialect="bohairic") == "ⲥⲛⲁⲩ"
    assert CopticNumerals.get_cardinal(2, gender=GrammaticalGender.FEMININE, dialect="bohairic") == "ⲥⲛⲟⲩϯ"
    assert CopticNumerals.get_cardinal(3, gender=GrammaticalGender.MASCULINE, dialect="bohairic") == "ϣⲟⲙⲧ"
    assert CopticNumerals.get_cardinal(3, gender=GrammaticalGender.FEMININE, dialect="bohairic") == "ϣⲟⲙϯ"
    assert CopticNumerals.get_cardinal(4, gender=GrammaticalGender.MASCULINE, dialect="bohairic") == "ϥⲧⲟⲟⲩ"
    assert CopticNumerals.get_cardinal(5, gender=GrammaticalGender.MASCULINE, dialect="bohairic") == "ϯⲟⲩ"
    assert CopticNumerals.get_cardinal(10, gender=GrammaticalGender.MASCULINE, dialect="bohairic") == "ⲙⲏⲧ"
    assert CopticNumerals.get_cardinal(100, dialect="bohairic") == "ϣⲉ"
    assert CopticNumerals.get_cardinal(1000, dialect="bohairic") == "ϣⲟ"

    # 2. Number 1 with noun (adjectival postpositive with ⲛ̀ⲟⲩⲱⲧ)
    p1, _ = CopticNumerals.format_numeral_with_noun(1, "ⲛⲟⲩϯ", dialect="bohairic")
    assert p1 == "ⲟⲩⲛⲟⲩϯ ⲛ̀ⲟⲩⲱⲧ"

    # 3. Numbers 2–10 with noun (preceding numeral + ⲛ̀- / ⲙ̀- linker)
    p2, _ = CopticNumerals.format_numeral_with_noun(2, "ⲣⲱⲙⲓ", dialect="bohairic")
    assert p2 == "ⲥⲛⲁⲩ ⲛ̀ⲣⲱⲙⲓ"

    p3, _ = CopticNumerals.format_numeral_with_noun(3, "ⲉ̀ϩⲟⲟⲩ", dialect="bohairic")
    assert p3 == "ϣⲟⲙⲧ ⲛ̀ⲉ̀ϩⲟⲟⲩ"


def test_numeral_noun_syntax_composition() -> None:
    # 1. ثلاثة رجال -> ϣⲟⲙⲧ ⲛ̀ⲣⲱⲙⲓ
    breakdown_three_men = [
        {"arabic": "ثلاثة", "coptic": "ϣⲟⲙⲧ", "status": "known", "part_of_speech": "numeral"},
        {"arabic": "رجال", "coptic": "ⲣⲱⲙⲓ", "status": "known", "part_of_speech": "noun"},
    ]
    res_three = compose_coptic_sentence_with_notes(breakdown_three_men, dialect_id=1)
    assert res_three.coptic_text == "ϣⲟⲙⲧ ⲛ̀ⲣⲱⲙⲓ"
    num_notes = [n for n in res_three.grammar_notes if "العدد والمعدود" in n["title"]]
    assert len(num_notes) > 0

    # 2. اله واحد -> ⲟⲩⲛⲟⲩϯ ⲛ̀ⲟⲩⲱⲧ
    breakdown_one_god = [
        {"arabic": "اله", "coptic": "ⲛⲟⲩϯ", "status": "known", "part_of_speech": "noun"},
        {"arabic": "واحد", "coptic": "ⲟⲩⲁⲓ", "status": "known", "part_of_speech": "numeral"},
    ]
    res_one = compose_coptic_sentence_with_notes(breakdown_one_god, dialect_id=1)
    assert res_one.coptic_text == "ⲟⲩⲛⲟⲩϯ ⲛ̀ⲟⲩⲱⲧ"
    single_notes = [n for n in res_one.grammar_notes if "عدد الوحدة" in n["title"]]
    assert len(single_notes) > 0



