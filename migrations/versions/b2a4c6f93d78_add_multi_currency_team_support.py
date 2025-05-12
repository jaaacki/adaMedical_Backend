"""
Add multi-currency team support.

Revision ID: b2a4c6f93d78
Revises: 111f1bf5fcc5
Create Date: 2025-05-13 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'b2a4c6f93d78'
down_revision = '111f1bf5fcc5'
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
    currencies = table('currencies',
        column('code', sa.String),
        column('name', sa.String),
        column('symbol', sa.String),
        column('is_active', sa.Boolean)
    )
    
    op.bulk_insert(currencies, [
        {'code': 'SGD', 'name': 'Singapore Dollar', 'symbol': 'S$', 'is_active': True},
        {'code': 'IDR', 'name': 'Indonesian Rupiah', 'symbol': 'Rp', 'is_active': True}
    ])
    
    # Migrate existing user preferences to user_currencies table
    conn = op.get_bind()
    
    # Get all users with currency_context
    result = conn.execute("SELECT id, currency_context FROM users WHERE currency_context IS NOT NULL")
    users = result.fetchall()
    
    # Insert into user_currencies table
    user_currencies = table('user_currencies',
        column('user_id', sa.Integer),
        column('currency_code', sa.String),
        column('is_default', sa.Boolean)
    )
    
    for user_id, currency_code in users:
        # Skip if currency code is invalid
        if currency_code not in ('SGD', 'IDR'):
            continue
            
        # Check if the user already has this currency assigned
        check = conn.execute(
            f"SELECT COUNT(*) FROM user_currencies WHERE user_id = {user_id} AND currency_code = '{currency_code}'"
        ).scalar()
        
        if check == 0:
            # Insert the user currency assignment
            op.execute(
                user_currencies.insert().values(
                    user_id=user_id,
                    currency_code=currency_code,
                    is_default=True
                )
            )
    
    # Add currency columns to relevant tables
    tables_to_add_currency = []
    
    # Check if products table exists
    try:
        products_exists = conn.execute("SELECT 1 FROM information_schema.tables WHERE table_schema = DATABASE() AND table_name = 'products'").scalar() is not None
        if products_exists:
            # Check if currency_code column already exists
            col_exists = conn.execute("SELECT 1 FROM information_schema.columns WHERE table_schema = DATABASE() AND table_name = 'products' AND column_name = 'currency_code'").scalar() is not None
            if not col_exists:
                tables_to_add_currency.append('products')
    except:
        pass
    
    # Check if orders table exists
    try:
        orders_exists = conn.execute("SELECT 1 FROM information_schema.tables WHERE table_schema = DATABASE() AND table_name = 'orders'").scalar() is not None
        if orders_exists:
            # Check if currency_code column already exists
            col_exists = conn.execute("SELECT 1 FROM information_schema.columns WHERE table_schema = DATABASE() AND table_name = 'orders' AND column_name = 'currency_code'").scalar() is not None
            if not col_exists:
                tables_to_add_currency.append('orders')
    except:
        pass
    
    # Check if invoices table exists
    try:
        invoices_exists = conn.execute("SELECT 1 FROM information_schema.tables WHERE table_schema = DATABASE() AND table_name = 'invoices'").scalar() is not None
        if invoices_exists:
            # Check if currency_code column already exists
            col_exists = conn.execute("SELECT 1 FROM information_schema.columns WHERE table_schema = DATABASE() AND table_name = 'invoices' AND column_name = 'currency_code'").scalar() is not None
            if not col_exists:
                tables_to_add_currency.append('invoices')
    except:
        pass
    
    # Add currency_code column to the identified tables
    for table_name in tables_to_add_currency:
        op.add_column(
            table_name,
            sa.Column('currency_code', sa.String(3), nullable=False, server_default='SGD')
        )
    
    # Create the after_user_insert trigger
    # Note: Alembic doesn't have direct support for creating triggers,
    # so we'll use raw SQL execution
    op.execute("""
    DROP TRIGGER IF EXISTS after_user_insert
    """)
    
    op.execute("""
    CREATE TRIGGER after_user_insert
    AFTER INSERT ON users
    FOR EACH ROW
    BEGIN
        DECLARE default_currency VARCHAR(3);
        
        IF NEW.currency_context IS NOT NULL AND NEW.currency_context != '' THEN
            SET default_currency = NEW.currency_context;
        ELSE
            SET default_currency = 'SGD';
        END IF;
        
        IF EXISTS (SELECT 1 FROM currencies WHERE code = default_currency) THEN
            IF NOT EXISTS (SELECT 1 FROM user_currencies WHERE user_id = NEW.id AND currency_code = default_currency) THEN
                INSERT INTO user_currencies (user_id, currency_code, is_default) 
                VALUES (NEW.id, default_currency, TRUE);
            END IF;
        ELSE
            INSERT INTO user_currencies (user_id, currency_code, is_default) 
            VALUES (NEW.id, 'SGD', TRUE);
        END IF;
    END
    """)


def downgrade():
    # Drop the trigger first
    op.execute("DROP TRIGGER IF EXISTS after_user_insert")
    
    # Get database connection
    conn = op.get_bind()
    
    # Remove currency_code column from relevant tables
    tables_to_check = ['products', 'orders', 'invoices']
    for table_name in tables_to_check:
        try:
            # Check if table exists
            table_exists = conn.execute(f"SELECT 1 FROM information_schema.tables WHERE table_schema = DATABASE() AND table_name = '{table_name}'").scalar() is not None
            if table_exists:
                # Check if column exists
                col_exists = conn.execute(f"SELECT 1 FROM information_schema.columns WHERE table_schema = DATABASE() AND table_name = '{table_name}' AND column_name = 'currency_code'").scalar() is not None
                if col_exists:
                    op.drop_column(table_name, 'currency_code')
        except:
            pass
    
    # Drop tables in reverse order
    op.drop_table('user_currencies')
    op.drop_table('currencies')