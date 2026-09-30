from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260624_0003"
down_revision = "20260624_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # A candidate is only persisted with text when the pipeline could compose a
    # safe translation; when it cannot (unknown words / low confidence) the row
    # must stay NULL instead of an empty string.
    op.alter_column(
        "translation_candidates",
        "candidate_text",
        existing_type=sa.Text(),
        nullable=True,
    )


def downgrade() -> None:
    op.execute("UPDATE translation_candidates SET candidate_text = '' WHERE candidate_text IS NULL")
    op.alter_column(
        "translation_candidates",
        "candidate_text",
        existing_type=sa.Text(),
        nullable=False,
    )
