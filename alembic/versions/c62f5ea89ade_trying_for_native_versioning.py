"""Trying for native versioning

Revision ID: c62f5ea89ade
Revises: 62f3c5b2444b
Create Date: 2016-09-03 05:08:42.811704

"""

# revision identifiers, used by Alembic.
revision = 'c62f5ea89ade'
down_revision = '62f3c5b2444b'
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

from sqlalchemy_continuum.dialects.postgresql import sync_trigger

def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    conn = op.get_bind()
    sync_trigger(conn, 'web_pages_version')
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    ### end Alembic commands ###
    pass
