"""add book_sections, book_figures, and typed-block columns on book_chunks

Revision ID: a1c7f2b3e4d5
Revises: db6f1536ede4
Create Date: 2026-05-06 21:00:00.000000

This migration is additive: every new column on book_chunks is nullable,
and the two new tables don't affect existing rows. Legacy text-only chunks
keep working with section_id = NULL.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "a1c7f2b3e4d5"
down_revision: Union[str, None] = "db6f1536ede4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "book_sections",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("book_id", sa.UUID(), nullable=False),
        sa.Column("parent_id", sa.UUID(), nullable=True),
        sa.Column("level", sa.Integer(), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("kind", sa.String(length=50), nullable=False, server_default="section"),
        sa.Column("number", sa.String(length=50), nullable=True),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("page_start", sa.Integer(), nullable=True),
        sa.Column("page_end", sa.Integer(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["book_id"], ["books.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["parent_id"], ["book_sections.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_book_sections_book_id", "book_sections", ["book_id"], unique=False)
    op.create_index("idx_book_sections_parent_id", "book_sections", ["parent_id"], unique=False)

    op.add_column("book_chunks", sa.Column("section_id", sa.UUID(), nullable=True))
    op.add_column(
        "book_chunks",
        sa.Column("blocks", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column("book_chunks", sa.Column("page_kind", sa.String(length=50), nullable=True))
    op.add_column("book_chunks", sa.Column("confidence", sa.Float(), nullable=True))
    op.create_foreign_key(
        "fk_book_chunks_section_id",
        "book_chunks",
        "book_sections",
        ["section_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "idx_book_chunks_section_id", "book_chunks", ["section_id"], unique=False
    )

    op.create_table(
        "book_figures",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("book_id", sa.UUID(), nullable=False),
        sa.Column("section_id", sa.UUID(), nullable=True),
        sa.Column("chunk_id", sa.UUID(), nullable=True),
        sa.Column("page", sa.Integer(), nullable=False),
        sa.Column("image_url", sa.String(length=1000), nullable=False),
        sa.Column("caption", sa.Text(), nullable=True),
        sa.Column("bbox_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["book_id"], ["books.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["section_id"], ["book_sections.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["chunk_id"], ["book_chunks.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_book_figures_book_id", "book_figures", ["book_id"], unique=False)
    op.create_index(
        "idx_book_figures_section_id", "book_figures", ["section_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index("idx_book_figures_section_id", table_name="book_figures")
    op.drop_index("idx_book_figures_book_id", table_name="book_figures")
    op.drop_table("book_figures")

    op.drop_index("idx_book_chunks_section_id", table_name="book_chunks")
    op.drop_constraint("fk_book_chunks_section_id", "book_chunks", type_="foreignkey")
    op.drop_column("book_chunks", "confidence")
    op.drop_column("book_chunks", "page_kind")
    op.drop_column("book_chunks", "blocks")
    op.drop_column("book_chunks", "section_id")

    op.drop_index("idx_book_sections_parent_id", table_name="book_sections")
    op.drop_index("idx_book_sections_book_id", table_name="book_sections")
    op.drop_table("book_sections")
