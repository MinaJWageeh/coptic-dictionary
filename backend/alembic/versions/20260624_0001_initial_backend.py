from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260624_0001"
down_revision = None
branch_labels = None
depends_on = None


def _timestamps() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    ]


role_enum = postgresql.ENUM("user", "reviewer", "admin", name="role", create_type=False)
source_type_enum = postgresql.ENUM(
    "dictionary",
    "corpus",
    "academic_paper",
    "user_submission",
    "other",
    "book",
    "manuscript",
    "paper",
    "website",
    "lexicon",
    "bible",
    name="source_type",
    create_type=False,
)
part_of_speech_enum = postgresql.ENUM(
    "noun",
    "verb",
    "adjective",
    "pronoun",
    "preposition",
    "conjunction",
    "adverb",
    "numeral",
    "article",
    "interjection",
    "particle",
    "other",
    name="part_of_speech",
    create_type=False,
)
review_status_enum = postgresql.ENUM(
    "draft",
    "pending",
    "approved",
    "rejected",
    "needs_revision",
    name="review_status",
    create_type=False,
)
translation_request_status_enum = postgresql.ENUM(
    "queued",
    "processing",
    "completed",
    "failed",
    "cancelled",
    "draft",
    "in_review",
    "approved",
    "rejected",
    name="translation_request_status",
    create_type=False,
)


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute("CREATE EXTENSION IF NOT EXISTS citext")

    role_enum.create(op.get_bind(), checkfirst=True)
    source_type_enum.create(op.get_bind(), checkfirst=True)
    part_of_speech_enum.create(op.get_bind(), checkfirst=True)
    review_status_enum.create(op.get_bind(), checkfirst=True)
    translation_request_status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "dialects",
        sa.Column("id", sa.Integer(), primary_key=True),
        *_timestamps(),
        sa.Column("code", sa.String(40), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("native_name", sa.String(120), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.UniqueConstraint("code"),
    )
    op.create_index("ix_dialects_code", "dialects", ["code"])

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        *_timestamps(),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("display_name", sa.String(120), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", role_enum, nullable=False, server_default="user"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("preferred_dialect_id", sa.Integer(), sa.ForeignKey("dialects.id"), nullable=True),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_role", "users", ["role"])

    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), primary_key=True),
        *_timestamps(),
        sa.Column("name", sa.String(60), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "user_roles",
        sa.Column("id", sa.Integer(), primary_key=True),
        *_timestamps(),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("role_id", sa.Integer(), sa.ForeignKey("roles.id"), nullable=False),
        sa.UniqueConstraint("user_id", "role_id", name="uq_user_role"),
    )
    op.create_index("ix_user_roles_user_id", "user_roles", ["user_id"])
    op.create_index("ix_user_roles_role_id", "user_roles", ["role_id"])

    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.Integer(), primary_key=True),
        *_timestamps(),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("token_hash", sa.String(255), nullable=False),
        sa.Column("expires_at", sa.Integer(), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
    op.create_index("ix_refresh_tokens_token_hash", "refresh_tokens", ["token_hash"])

    op.create_table(
        "sources",
        sa.Column("id", sa.Integer(), primary_key=True),
        *_timestamps(),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("author", sa.String(255), nullable=True),
        sa.Column("type", source_type_enum, nullable=False, server_default="book"),
        sa.Column("year", sa.Integer(), nullable=True),
        sa.Column("url", sa.String(500), nullable=True),
        sa.Column("isbn", sa.String(32), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
    )
    op.create_index("ix_sources_title_trgm", "sources", ["title"], postgresql_using="gin", postgresql_ops={"title": "gin_trgm_ops"})

    op.create_table(
        "dictionary_entries",
        sa.Column("id", sa.Integer(), primary_key=True),
        *_timestamps(),
        sa.Column("coptic_text", sa.Text(), nullable=False),
        sa.Column("normalized_coptic_text", sa.Text(), nullable=False),
        sa.Column("transliteration", sa.String(255), nullable=True),
        sa.Column("dialect_id", sa.Integer(), sa.ForeignKey("dialects.id"), nullable=False),
        sa.Column("source_id", sa.Integer(), sa.ForeignKey("sources.id"), nullable=False),
        sa.Column("part_of_speech", part_of_speech_enum, nullable=False),
        sa.Column("gender", sa.String(40), nullable=True),
        sa.Column("grammatical_number", sa.String(40), nullable=True),
        sa.Column("root", sa.String(120), nullable=True),
        sa.Column("example_sentence", sa.Text(), nullable=True),
        sa.Column("example_embedding", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("review_status", review_status_enum, nullable=False, server_default="pending"),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("reviewed_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.UniqueConstraint(
            "normalized_coptic_text",
            "dialect_id",
            "part_of_speech",
            "source_id",
            name="uq_dictionary_entry_identity",
        ),
    )
    op.execute("ALTER TABLE dictionary_entries ALTER COLUMN example_embedding TYPE vector(384) USING NULL")
    op.create_index("ix_dictionary_entries_dialect_id", "dictionary_entries", ["dialect_id"])
    op.create_index("ix_dictionary_entries_source_id", "dictionary_entries", ["source_id"])
    op.create_index("ix_dictionary_entries_part_of_speech", "dictionary_entries", ["part_of_speech"])
    op.create_index("ix_dictionary_entries_review_status", "dictionary_entries", ["review_status"])
    op.create_index("ix_dictionary_entries_coptic_trgm", "dictionary_entries", ["coptic_text"], postgresql_using="gin", postgresql_ops={"coptic_text": "gin_trgm_ops"})
    op.create_index("ix_dictionary_entries_example_embedding", "dictionary_entries", ["example_embedding"], postgresql_using="ivfflat", postgresql_ops={"example_embedding": "vector_cosine_ops"})

    op.create_table(
        "arabic_senses",
        sa.Column("id", sa.Integer(), primary_key=True),
        *_timestamps(),
        sa.Column("arabic_lemma", sa.String(255), nullable=False),
        sa.Column("normalized_arabic_lemma", sa.String(255), nullable=False),
        sa.Column("sense_key", sa.String(120), nullable=True),
        sa.Column("definition_ar", sa.Text(), nullable=False),
        sa.Column("part_of_speech", part_of_speech_enum, nullable=True),
        sa.Column("example_ar", sa.Text(), nullable=True),
        sa.Column("example_embedding", sa.Text(), nullable=True),
        sa.Column("source_id", sa.Integer(), sa.ForeignKey("sources.id"), nullable=True),
        sa.Column("review_status", review_status_enum, nullable=False, server_default="pending"),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("reviewed_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
    )
    op.execute("ALTER TABLE arabic_senses ALTER COLUMN example_embedding TYPE vector(384) USING NULL")
    op.create_index("ix_arabic_senses_normalized_arabic_lemma", "arabic_senses", ["normalized_arabic_lemma"])
    op.create_index("ix_arabic_senses_lemma_trgm", "arabic_senses", ["arabic_lemma"], postgresql_using="gin", postgresql_ops={"arabic_lemma": "gin_trgm_ops"})
    op.create_index("ix_arabic_senses_example_embedding", "arabic_senses", ["example_embedding"], postgresql_using="ivfflat", postgresql_ops={"example_embedding": "vector_cosine_ops"})

    op.create_table(
        "sense_mappings",
        sa.Column("id", sa.Integer(), primary_key=True),
        *_timestamps(),
        sa.Column("arabic_sense_id", sa.Integer(), sa.ForeignKey("arabic_senses.id"), nullable=False),
        sa.Column("dictionary_entry_id", sa.Integer(), sa.ForeignKey("dictionary_entries.id"), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("usage_note", sa.Text(), nullable=True),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("review_status", review_status_enum, nullable=False, server_default="pending"),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("reviewed_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.UniqueConstraint("arabic_sense_id", "dictionary_entry_id", name="uq_sense_mapping"),
    )
    op.create_index("ix_sense_mappings_arabic_sense_id", "sense_mappings", ["arabic_sense_id"])
    op.create_index("ix_sense_mappings_dictionary_entry_id", "sense_mappings", ["dictionary_entry_id"])
    op.create_index("ix_sense_mappings_confidence", "sense_mappings", ["confidence"])

    op.create_table(
        "corpus_texts",
        sa.Column("id", sa.Integer(), primary_key=True),
        *_timestamps(),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("source_id", sa.Integer(), sa.ForeignKey("sources.id"), nullable=False),
        sa.Column("dialect_id", sa.Integer(), sa.ForeignKey("dialects.id"), nullable=True),
        sa.Column("language", sa.String(40), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("review_status", review_status_enum, nullable=False, server_default="pending"),
        sa.Column("metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("reviewed_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
    )
    op.create_index("ix_corpus_texts_source_id", "corpus_texts", ["source_id"])
    op.create_index("ix_corpus_texts_review_status", "corpus_texts", ["review_status"])

    op.create_table(
        "parallel_segments",
        sa.Column("id", sa.Integer(), primary_key=True),
        *_timestamps(),
        sa.Column("corpus_text_id", sa.Integer(), sa.ForeignKey("corpus_texts.id"), nullable=True),
        sa.Column("source_id", sa.Integer(), sa.ForeignKey("sources.id"), nullable=False),
        sa.Column("dialect_id", sa.Integer(), sa.ForeignKey("dialects.id"), nullable=True),
        sa.Column("segment_order", sa.Integer(), nullable=True),
        sa.Column("arabic_text", sa.Text(), nullable=False),
        sa.Column("coptic_text", sa.Text(), nullable=True),
        sa.Column("normalized_arabic_text", sa.Text(), nullable=True),
        sa.Column("normalized_coptic_text", sa.Text(), nullable=True),
        sa.Column("alignment_score", sa.Float(), nullable=True),
        sa.Column("sentence_embedding", sa.Text(), nullable=True),
        sa.Column("review_status", review_status_enum, nullable=False, server_default="pending"),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("reviewed_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
    )
    op.execute("ALTER TABLE parallel_segments ALTER COLUMN sentence_embedding TYPE vector(384) USING NULL")
    op.create_index("ix_parallel_segments_source_id", "parallel_segments", ["source_id"])
    op.create_index("ix_parallel_segments_dialect_id", "parallel_segments", ["dialect_id"])
    op.create_index("ix_parallel_segments_review_status", "parallel_segments", ["review_status"])
    op.create_index("ix_parallel_segments_arabic_trgm", "parallel_segments", ["arabic_text"], postgresql_using="gin", postgresql_ops={"arabic_text": "gin_trgm_ops"})
    op.create_index("ix_parallel_segments_coptic_trgm", "parallel_segments", ["coptic_text"], postgresql_using="gin", postgresql_ops={"coptic_text": "gin_trgm_ops"})
    op.create_index("ix_parallel_segments_sentence_embedding", "parallel_segments", ["sentence_embedding"], postgresql_using="ivfflat", postgresql_ops={"sentence_embedding": "vector_cosine_ops"})

    op.create_table(
        "grammar_rules",
        sa.Column("id", sa.Integer(), primary_key=True),
        *_timestamps(),
        sa.Column("dialect_id", sa.Integer(), sa.ForeignKey("dialects.id"), nullable=True),
        sa.Column("source_id", sa.Integer(), sa.ForeignKey("sources.id"), nullable=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("rule_code", sa.String(120), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("pattern", sa.Text(), nullable=True),
        sa.Column("replacement", sa.Text(), nullable=True),
        sa.Column("examples", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("review_status", review_status_enum, nullable=False, server_default="pending"),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("reviewed_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.UniqueConstraint("rule_code"),
    )
    op.create_index("ix_grammar_rules_dialect_id", "grammar_rules", ["dialect_id"])
    op.create_index("ix_grammar_rules_review_status", "grammar_rules", ["review_status"])

    op.create_table(
        "translation_requests",
        sa.Column("id", sa.Integer(), primary_key=True),
        *_timestamps(),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("source_language", sa.String(20), nullable=False, server_default="ar"),
        sa.Column("target_dialect_id", sa.Integer(), sa.ForeignKey("dialects.id"), nullable=True),
        sa.Column("input_text", sa.Text(), nullable=False),
        sa.Column("normalized_input_text", sa.Text(), nullable=True),
        sa.Column("context", sa.Text(), nullable=True),
        sa.Column("status", translation_request_status_enum, nullable=False, server_default="queued"),
        sa.Column("requested_model", sa.String(120), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
    )
    op.create_index("ix_translation_requests_user_id", "translation_requests", ["user_id"])
    op.create_index("ix_translation_requests_status", "translation_requests", ["status"])
    op.create_index("ix_translation_requests_input_trgm", "translation_requests", ["input_text"], postgresql_using="gin", postgresql_ops={"input_text": "gin_trgm_ops"})

    op.create_table(
        "translation_candidates",
        sa.Column("id", sa.Integer(), primary_key=True),
        *_timestamps(),
        sa.Column("translation_request_id", sa.Integer(), sa.ForeignKey("translation_requests.id"), nullable=False),
        sa.Column("candidate_text", sa.Text(), nullable=False),
        sa.Column("normalized_candidate_text", sa.Text(), nullable=True),
        sa.Column("dialect_id", sa.Integer(), sa.ForeignKey("dialects.id"), nullable=True),
        sa.Column("generated_by", sa.String(40), nullable=False, server_default="ai"),
        sa.Column("model_name", sa.String(120), nullable=True),
        sa.Column("rank", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("evidence", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("review_status", review_status_enum, nullable=False, server_default="draft"),
    )
    op.create_index("ix_translation_candidates_translation_request_id", "translation_candidates", ["translation_request_id"])
    op.create_index("ix_translation_candidates_review_status", "translation_candidates", ["review_status"])
    op.create_index("ix_translation_candidates_text_trgm", "translation_candidates", ["candidate_text"], postgresql_using="gin", postgresql_ops={"candidate_text": "gin_trgm_ops"})

    op.create_table(
        "translation_reviews",
        sa.Column("id", sa.Integer(), primary_key=True),
        *_timestamps(),
        sa.Column("translation_candidate_id", sa.Integer(), sa.ForeignKey("translation_candidates.id"), nullable=False),
        sa.Column("reviewer_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("review_status", review_status_enum, nullable=False),
        sa.Column("rating", sa.Integer(), nullable=True),
        sa.Column("corrected_text", sa.Text(), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
    )
    op.create_index("ix_translation_reviews_translation_candidate_id", "translation_reviews", ["translation_candidate_id"])
    op.create_index("ix_translation_reviews_reviewer_id", "translation_reviews", ["reviewer_id"])

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        *_timestamps(),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("action", sa.String(60), nullable=False),
        sa.Column("table_name", sa.String(120), nullable=True),
        sa.Column("record_id", sa.Integer(), nullable=True),
        sa.Column("old_data", sa.JSON(), nullable=True),
        sa.Column("new_data", sa.JSON(), nullable=True),
        sa.Column("ip_address", sa.String(64), nullable=True),
        sa.Column("user_agent", sa.String(255), nullable=True),
    )
    op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"])
    op.create_index("ix_audit_logs_table_record", "audit_logs", ["table_name", "record_id"])


def downgrade() -> None:
    for table in [
        "audit_logs",
        "translation_reviews",
        "translation_candidates",
        "translation_requests",
        "grammar_rules",
        "parallel_segments",
        "corpus_texts",
        "sense_mappings",
        "arabic_senses",
        "dictionary_entries",
        "sources",
        "refresh_tokens",
        "user_roles",
        "roles",
        "users",
        "dialects",
    ]:
        op.drop_table(table)
    translation_request_status_enum.drop(op.get_bind(), checkfirst=True)
    review_status_enum.drop(op.get_bind(), checkfirst=True)
    part_of_speech_enum.drop(op.get_bind(), checkfirst=True)
    source_type_enum.drop(op.get_bind(), checkfirst=True)
    role_enum.drop(op.get_bind(), checkfirst=True)
