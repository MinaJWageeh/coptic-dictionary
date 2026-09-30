from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260624_0002"
down_revision = "20260624_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("parallel_segments", sa.Column("arabic_embedding", sa.Text(), nullable=True))
    op.add_column("parallel_segments", sa.Column("coptic_embedding", sa.Text(), nullable=True))
    op.add_column("arabic_senses", sa.Column("meaning_embedding", sa.Text(), nullable=True))
    op.add_column("grammar_rules", sa.Column("description_embedding", sa.Text(), nullable=True))

    op.execute("ALTER TABLE parallel_segments ALTER COLUMN arabic_embedding TYPE vector(384) USING NULL")
    op.execute("ALTER TABLE parallel_segments ALTER COLUMN coptic_embedding TYPE vector(384) USING NULL")
    op.execute("ALTER TABLE arabic_senses ALTER COLUMN meaning_embedding TYPE vector(384) USING NULL")
    op.execute("ALTER TABLE grammar_rules ALTER COLUMN description_embedding TYPE vector(384) USING NULL")

    op.create_index(
        "ix_parallel_segments_arabic_embedding",
        "parallel_segments",
        ["arabic_embedding"],
        postgresql_using="ivfflat",
        postgresql_ops={"arabic_embedding": "vector_cosine_ops"},
    )
    op.create_index(
        "ix_parallel_segments_coptic_embedding",
        "parallel_segments",
        ["coptic_embedding"],
        postgresql_using="ivfflat",
        postgresql_ops={"coptic_embedding": "vector_cosine_ops"},
    )
    op.create_index(
        "ix_arabic_senses_meaning_embedding",
        "arabic_senses",
        ["meaning_embedding"],
        postgresql_using="ivfflat",
        postgresql_ops={"meaning_embedding": "vector_cosine_ops"},
    )
    op.create_index(
        "ix_grammar_rules_description_embedding",
        "grammar_rules",
        ["description_embedding"],
        postgresql_using="ivfflat",
        postgresql_ops={"description_embedding": "vector_cosine_ops"},
    )


def downgrade() -> None:
    op.drop_index("ix_grammar_rules_description_embedding", table_name="grammar_rules")
    op.drop_index("ix_arabic_senses_meaning_embedding", table_name="arabic_senses")
    op.drop_index("ix_parallel_segments_coptic_embedding", table_name="parallel_segments")
    op.drop_index("ix_parallel_segments_arabic_embedding", table_name="parallel_segments")
    op.drop_column("grammar_rules", "description_embedding")
    op.drop_column("arabic_senses", "meaning_embedding")
    op.drop_column("parallel_segments", "coptic_embedding")
    op.drop_column("parallel_segments", "arabic_embedding")
