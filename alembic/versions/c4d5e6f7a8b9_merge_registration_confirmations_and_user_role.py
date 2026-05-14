"""merge registration confirmations and default user role heads

Revision ID: c4d5e6f7a8b9
Revises: 9a2f0d1c4e77, 9b4ec1d2a6f3
Create Date: 2026-05-14 00:00:00.000000

"""
from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = "c4d5e6f7a8b9"
down_revision: Union[str, Sequence[str], None] = ("9a2f0d1c4e77", "9b4ec1d2a6f3")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
