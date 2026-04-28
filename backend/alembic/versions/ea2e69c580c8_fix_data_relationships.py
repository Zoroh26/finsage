"""fix_data_relationships

Revision ID: ea2e69c580c8
Revises: 229da01ffbd4
Create Date: 2025-10-24 11:36:05.999744

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ea2e69c580c8'
down_revision: Union[str, Sequence[str], None] = '229da01ffbd4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Fix data relationships by linking assets and holdings to accounts.

    Strategy:
    1. Link assets to accounts based on asset type → account type mapping
    2. Link holdings to assets based on account relationships
    3. Populate EPF table from asset data
    """

    # Get connection for executing SQL
    connection = op.get_bind()

    # Step 1: Link ASSET_TYPE_INDIAN_SECURITIES to EQUITIES accounts
    # Find the first EQUITIES account for each user and link their securities asset
    connection.execute(sa.text("""
        UPDATE assets 
        SET account_id = subq.account_id
        FROM (
            SELECT DISTINCT ON (user_id) 
                user_id, 
                account_id
            FROM accounts
            WHERE account_type = 'ACC_INSTRUMENT_TYPE_EQUITIES'
            ORDER BY user_id, account_id
        ) subq
        WHERE assets.user_id = subq.user_id
        AND assets.asset_type = 'ASSET_TYPE_INDIAN_SECURITIES'
        AND assets.account_id IS NULL;
    """))

    # Step 2: Link ASSET_TYPE_SAVINGS_ACCOUNTS to DEPOSIT accounts
    connection.execute(sa.text("""
        UPDATE assets 
        SET account_id = subq.account_id
        FROM (
            SELECT DISTINCT ON (user_id) 
                user_id, 
                account_id
            FROM accounts
            WHERE account_type = 'ACC_INSTRUMENT_TYPE_DEPOSIT'
            ORDER BY user_id, account_id
        ) subq
        WHERE assets.user_id = subq.user_id
        AND assets.asset_type = 'ASSET_TYPE_SAVINGS_ACCOUNTS'
        AND assets.account_id IS NULL;
    """))

    # Step 3: Link holdings to assets based on account and holding type
    # Link EQUITY holdings to INDIAN_SECURITIES asset
    connection.execute(sa.text("""
        UPDATE holdings 
        SET asset_id = subq.asset_id
        FROM (
            SELECT DISTINCT ON (a.user_id) 
                assets.asset_id,
                a.account_id
            FROM assets
            JOIN accounts a ON assets.user_id = a.user_id
            WHERE assets.asset_type = 'ASSET_TYPE_INDIAN_SECURITIES'
            ORDER BY a.user_id
        ) subq
        WHERE holdings.account_id = subq.account_id
        AND holdings.holding_type = 'EQUITY'
        AND holdings.asset_id IS NULL;
    """))

    # Link ETF holdings to asset (if exists)
    connection.execute(sa.text("""
        UPDATE holdings 
        SET asset_id = subq.asset_id
        FROM (
            SELECT DISTINCT ON (a.user_id) 
                assets.asset_id,
                a.account_id
            FROM assets
            JOIN accounts a ON assets.user_id = a.user_id
            WHERE assets.asset_type = 'ASSET_TYPE_INDIAN_SECURITIES'
            ORDER BY a.user_id
        ) subq
        WHERE holdings.account_id = subq.account_id
        AND holdings.holding_type = 'ETF'
        AND holdings.asset_id IS NULL;
    """))

    # Link REIT holdings
    connection.execute(sa.text("""
        UPDATE holdings 
        SET asset_id = subq.asset_id
        FROM (
            SELECT DISTINCT ON (a.user_id) 
                assets.asset_id,
                a.account_id
            FROM assets
            JOIN accounts a ON assets.user_id = a.user_id
            WHERE assets.asset_type = 'ASSET_TYPE_INDIAN_SECURITIES'
            ORDER BY a.user_id
        ) subq
        WHERE holdings.account_id = subq.account_id
        AND holdings.holding_type = 'REIT'
        AND holdings.asset_id IS NULL;
    """))

    # Link INVIT holdings
    connection.execute(sa.text("""
        UPDATE holdings 
        SET asset_id = subq.asset_id
        FROM (
            SELECT DISTINCT ON (a.user_id) 
                assets.asset_id,
                a.account_id
            FROM assets
            JOIN accounts a ON assets.user_id = a.user_id
            WHERE assets.asset_type = 'ASSET_TYPE_INDIAN_SECURITIES'
            ORDER BY a.user_id
        ) subq
        WHERE holdings.account_id = subq.account_id
        AND holdings.holding_type = 'INVIT'
        AND holdings.asset_id IS NULL;
    """))

    # Step 4: Populate EPF table from EPF assets
    connection.execute(sa.text("""
        INSERT INTO epfs (user_id, account_id, balance)
        SELECT 
            user_id,
            account_id,
            value as balance
        FROM assets
        WHERE asset_type = 'ASSET_TYPE_EPF'
        ON CONFLICT DO NOTHING;
    """))

    print("✅ Data relationships fixed successfully!")


def downgrade() -> None:
    """Downgrade schema - reset relationships."""
    connection = op.get_bind()

    # Remove EPF records that were auto-created
    connection.execute(sa.text("""
        DELETE FROM epfs 
        WHERE epf_id IN (
            SELECT e.epf_id 
            FROM epfs e
            JOIN assets a ON e.user_id = a.user_id AND e.balance = a.value
            WHERE a.asset_type = 'ASSET_TYPE_EPF'
        );
    """))

    # Reset asset account_id links
    connection.execute(sa.text("""
        UPDATE assets SET account_id = NULL
        WHERE asset_type IN (
            'ASSET_TYPE_INDIAN_SECURITIES',
            'ASSET_TYPE_SAVINGS_ACCOUNTS'
        );
    """))

    # Reset holding asset_id links
    connection.execute(sa.text("""
        UPDATE holdings SET asset_id = NULL;
    """))

    print("⬇️ Data relationships reverted")
