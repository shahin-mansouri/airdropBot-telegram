"""change get_or_create -if instance

Revision ID: 16b403a9c5fa
Revises: 600cd96ed71b
Create Date: 2024-12-12 13:47:20.780493

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '16b403a9c5fa'
down_revision: Union[str, None] = '600cd96ed71b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###
