"""Add hash and parent hash columns

Revision ID: c225ea8fbf5e
Revises: ea8987f915b8
Create Date: 2019-09-08 16:33:03.743328

"""

# revision identifiers, used by Alembic.
revision = 'c225ea8fbf5e'
down_revision = 'ea8987f915b8'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa

from sqlalchemy_utils.types import TSVectorType
from sqlalchemy_searchable import make_searchable
import sqlalchemy_utils

# Patch in knowledge of the citext type, so it reflects properly.
from sqlalchemy.dialects.postgresql.base import ischema_names
import citext
import queue
import datetime
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import TSVECTOR
ischema_names['citext'] = citext.CIText

from sqlalchemy.dialects import postgresql

def upgrade():

    op.execute("SET statement_timeout TO 144000000;")

    # ### commands auto generated by Alembic - please adjust! ###
    print("Adding to rss_parser_feed_name_lut 1")
    op.add_column('rss_parser_feed_name_lut_version', sa.Column('data_hash', postgresql.UUID(), nullable=True, unique=True))
    print("Adding to rss_parser_feed_name_lut 2")
    op.add_column('rss_parser_feed_name_lut_version', sa.Column('parent_hash', postgresql.UUID(), nullable=True))
    print("Adding to rss_parser_feed_name_lut (foreign key)")
    op.create_foreign_key(None, 'rss_parser_feed_name_lut_version', 'rss_parser_feed_name_lut_version', ['parent_hash'], ['data_hash'])
    print("Dropping is_delta column on rss_parser_feed_name_lut")
    op.drop_column('rss_parser_feed_name_lut_version', 'is_delta')
    print("Adding to rss_parser_funcs 1")
    op.add_column('rss_parser_funcs_version', sa.Column('data_hash', postgresql.UUID(), nullable=True, unique=True))
    print("Adding to rss_parser_funcs 2")
    op.add_column('rss_parser_funcs_version', sa.Column('parent_hash', postgresql.UUID(), nullable=True))
    print("Adding to rss_parser_funcs (foreign key)")
    op.create_foreign_key(None, 'rss_parser_funcs_version', 'rss_parser_funcs_version', ['parent_hash'], ['data_hash'])
    print("Dropping is_delta column on rss_parser_funcs")
    op.drop_column('rss_parser_funcs_version', 'is_delta')
    print("Adding to web_pages 1")
    op.add_column('web_pages_version', sa.Column('data_hash', postgresql.UUID(), nullable=True, unique=True))
    print("Adding to web_pages 2")
    op.add_column('web_pages_version', sa.Column('parent_hash', postgresql.UUID(), nullable=True))
    print("Adding to web_pages (foreign key)")
    op.create_foreign_key(None, 'web_pages_version', 'web_pages_version', ['parent_hash'], ['data_hash'])
    print("Dropping is_delta column on web_pages")
    op.drop_column('web_pages_version', 'is_delta')

    print("Adding to raw_web_pages 1")
    op.add_column('raw_web_pages_version', sa.Column('data_hash', postgresql.UUID(), nullable=True, unique=True))
    print("Adding to raw_web_pages 2")
    op.add_column('raw_web_pages_version', sa.Column('parent_hash', postgresql.UUID(), nullable=True))
    print("Adding to raw_web_pages (foreign key)")
    op.create_foreign_key(None, 'raw_web_pages_version', 'raw_web_pages_version', ['parent_hash'], ['data_hash'])
    print("Dropping is_delta column on raw_web_pages")
    op.drop_column('raw_web_pages_version', 'is_delta')
    print("Done!")
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('web_pages_version', sa.Column('is_delta', sa.BOOLEAN(), autoincrement=False, nullable=True))
    op.drop_constraint(None, 'web_pages_version', type_='foreignkey')
    op.drop_column('web_pages_version', 'parent_hash')
    op.drop_column('web_pages_version', 'data_hash')
    op.add_column('rss_parser_funcs_version', sa.Column('is_delta', sa.BOOLEAN(), autoincrement=False, nullable=True))
    op.drop_constraint(None, 'rss_parser_funcs_version', type_='foreignkey')
    op.drop_column('rss_parser_funcs_version', 'parent_hash')
    op.drop_column('rss_parser_funcs_version', 'data_hash')
    op.add_column('rss_parser_feed_name_lut_version', sa.Column('is_delta', sa.BOOLEAN(), autoincrement=False, nullable=True))
    op.drop_constraint(None, 'rss_parser_feed_name_lut_version', type_='foreignkey')
    op.drop_column('rss_parser_feed_name_lut_version', 'parent_hash')
    op.drop_column('rss_parser_feed_name_lut_version', 'data_hash')
    op.add_column('raw_web_pages_version', sa.Column('is_delta', sa.BOOLEAN(), autoincrement=False, nullable=True))
    op.drop_constraint(None, 'raw_web_pages_version', type_='foreignkey')
    op.drop_column('raw_web_pages_version', 'parent_hash')
    op.drop_column('raw_web_pages_version', 'data_hash')
    # ### end Alembic commands ###
