from app.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    rows = conn.execute(text("SELECT s.id, s.arabic_lemma, s.definition_ar, d.coptic_text, d.dialect_id FROM arabic_senses s JOIN sense_mappings m ON m.arabic_sense_id = s.id JOIN dictionary_entries d ON d.id = m.dictionary_entry_id WHERE s.normalized_arabic_lemma IN ('اكون', 'كان', 'يكون', 'هو', 'انا')")).fetchall()
    for r in rows:
        print(f"Lemma: {r[1]} | Def: {r[2]} | Coptic: {r[3]} | Dialect: {r[4]}")
