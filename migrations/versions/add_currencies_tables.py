"""Add currencies tables

Revision ID: add_currencies_tables
Revises: 5847bc308102
Create Date: 2025-05-13 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_currencies_tables'
down_revision = '5847bc308102'  # Update this to your most recent migration ID if needed
branch_labels = None
depends_on = None


def upgrade():
    # Create currencies table
    op.create_table('currencies',
        sa.Column('code', sa.String(3), primary_key=True),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('symbol', sa.String(5), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('1')),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'),
                  server_onupdate=sa.text('CURRENT_TIMESTAMP')),
    )
    
    # Create user_currencies table
    op.create_table('user_currencies',
        sa.Column('id', sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('currency_code', sa.String(3), nullable=False),
        sa.Column('is_default', sa.Boolean(), server_default=sa.text('0')),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'),
                  server_onupdate=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['currency_code'], ['currencies.code'], ondelete='CASCADE'),
        sa.UniqueConstraint('user_id', 'currency_code', name='uq_user_currency')
    )
    
    # Add index on user_id for faster lookups
    op.create_index('ix_user_currencies_user_id', 'user_currencies', ['user_id'])
    
    # Insert initial currency data
    op.bulk_insert(
        sa.table('currencies',
            sa.column('code', sa.String),
            sa.column('name', sa.String),
            sa.column('symbol', sa.String),
            sa.column('is_active', sa.Boolean)
        ),
        [
            {'code': 'SGD', 'name': 'Singapore Dollar', 'symbol': 'S$', 'is_active': True},
            {'code': 'IDR', 'name': 'Indonesian Rupiah', 'symbol': 'Rp', 'is_active': True},
            {'code': 'USD', 'name': 'US Dollar', 'symbol': '$', 'is_active': True},
            {'code': 'EUR', 'name': 'Euro', 'symbol': '€', 'is_active': True},
            {'code': 'GBP', 'name': 'British Pound', 'symbol': '£', 'is_active': True},
            {'code': 'JPY', 'name': 'Japanese Yen', 'symbol': '¥', 'is_active': True},
            {'code': 'AUD', 'name': 'Australian Dollar', 'symbol': 'A$', 'is_active': True},
            {'code': 'CNY', 'name': 'Chinese Yuan', 'symbol': '¥', 'is_active': True}
        ]
    )
    
    # Try to migrate existing user preferences to user_currencies table
    try:
        conn = op.get_bind()
        
        # Get all users with currency_context
        result = conn.execute("SELECT id, currency_context FROM users WHERE currency_context IS NOT NULL")
        users = result.fetchall()
        
        # Insert into user_currencies table
        for user_id, currency_code in users:
            # Skip if currency code is invalid
            if currency_code not in ('SGD', 'IDR', 'USD', 'EUR', 'GBP', 'JPY', 'AUD', 'CNY'):
                continue
                
            # Insert the user currency assignment
            op.execute(
                sa.text(
                    "INSERT INTO user_currencies (user_id, currency_code, is_default) VALUES (:user_id, :currency_code, 1)"
                ).bindparams(user_id=user_id, currency_code=currency_code)
            )
    except Exception as e:
        print(f"Warning: Could not migrate existing user currency preferences: {e}")


def downgrade():
    # Drop tables in reverse order
    op.drop_index('ix_user_currencies_user_id', table_name='user_currencies')
    op.drop_table('user_currencies')
    op.drop_table('currencies')