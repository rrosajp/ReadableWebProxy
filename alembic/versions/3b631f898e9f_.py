"""empty message

Revision ID: 3b631f898e9f
Revises: 7f63439f1380
Create Date: 2016-09-09 03:59:33.953485

"""

# revision identifiers, used by Alembic.
revision = '3b631f898e9f'
down_revision = '7f63439f1380'
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
from sqlalchemy.dialects.postgresql import TSVECTOR
ischema_names['citext'] = citext.CIText



def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('raw_web_pages', 'fspath',
               existing_type=sa.TEXT(),
               nullable=True)
    op.drop_column('raw_web_pages', 'is_text')
    op.drop_column('raw_web_pages_version', 'is_text')
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('raw_web_pages_version', sa.Column('is_text', sa.BOOLEAN(), autoincrement=False, nullable=True))
    op.add_column('raw_web_pages', sa.Column('is_text', sa.BOOLEAN(), autoincrement=False, nullable=True))
    op.alter_column('raw_web_pages', 'fspath',
               existing_type=sa.TEXT(),
               nullable=False)
    ### end Alembic commands ###
