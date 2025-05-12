"""Create all required tables

Revision ID: create_all_tables
Revises: 
Create Date: 2025-05-13 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.exc import OperationalError


# revision identifiers, used by Alembic.
revision = 'create_all_tables'
down_revision = None  # This is the first migration
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    
    # Create roles table first
    try:
        op.create_table('roles',
            sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
            sa.Column('name', sa.String(64), nullable=False, unique=True),
            sa.PrimaryKeyConstraint('id')
        )
        print("Created roles table")
    except OperationalError as e:
        if "already exists" in str(e):
            print("Table 'roles' already exists, skipping creation")
        else:
            raise
    
    # Create users table with reference to roles
    try:
        op.create_table('users',
            sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
            sa.Column('name', sa.String(128), nullable=False),
            sa.Column('email', sa.String(128), nullable=False, index=True, unique=True),
            sa.Column('password_hash', sa.String(255)),
            sa.Column('google_sso_id', sa.String(255), unique=True, nullable=True),
            sa.Column('role_id', sa.Integer(), sa.ForeignKey('roles.id'), nullable=True),
            sa.Column('is_active', sa.Boolean(), default=True),
            sa.Column('currency_context', sa.String(3), default='SGD'),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'),
                      server_onupdate=sa.text('CURRENT_TIMESTAMP')),
            sa.PrimaryKeyConstraint('id')
        )
        print("Created users table")
    except OperationalError as e:
        if "already exists" in str(e):
            print("Table 'users' already exists, skipping creation")
        else:
            raise
    
    # Create currencies table
    try:
        op.create_table('currencies',
            sa.Column('code', sa.String(3), primary_key=True),
            sa.Column('name', sa.String(50), nullable=False),
            sa.Column('symbol', sa.String(5), nullable=False),
            sa.Column('is_active', sa.Boolean(), server_default=sa.text('1')),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'),
                    server_onupdate=sa.text('CURRENT_TIMESTAMP')),
        )
        print("Created currencies table")
        
        # Insert initial currency data (only if we created the table)
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
        print("Inserted currency data")
    except OperationalError as e:
        if "already exists" in str(e):
            print("Table 'currencies' already exists, skipping creation")
        else:
            raise
    
    # Create user_currencies table (after both users and currencies exist)
    try:
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
        print("Created user_currencies table")
        
        # Add index on user_id for faster lookups
        op.create_index('ix_user_currencies_user_id', 'user_currencies', ['user_id'])
        print("Created index on user_currencies.user_id")
        
        # Try to migrate existing user preferences to user_currencies table
        try:
            # Get all users with currency_context
            result = conn.execute(sa.text("SELECT id, currency_context FROM users WHERE currency_context IS NOT NULL"))
            users = result.fetchall()
            
            # Insert into user_currencies table
            for user_id, currency_code in users:
                # Skip if currency code is invalid
                valid_currency = conn.execute(
                    sa.text("SELECT 1 FROM currencies WHERE code = :currency_code"),
                    {"currency_code": currency_code}
                ).fetchone()
                
                if not valid_currency:
                    continue
                    
                # Check if assignment already exists to avoid duplicates
                existing = conn.execute(
                    sa.text("SELECT 1 FROM user_currencies WHERE user_id = :user_id AND currency_code = :currency_code"),
                    {"user_id": user_id, "currency_code": currency_code}
                ).fetchone()
                
                if existing:
                    continue
                    
                # Insert the user currency assignment
                conn.execute(
                    sa.text(
                        "INSERT INTO user_currencies (user_id, currency_code, is_default) VALUES (:user_id, :currency_code, 1)"
                    ),
                    {"user_id": user_id, "currency_code": currency_code}
                )
            print("Successfully migrated user currency preferences")
        except Exception as e:
            print(f"Warning: Could not migrate existing user currency preferences: {e}")
    except OperationalError as e:
        if "already exists" in str(e):
            print("Table 'user_currencies' already exists, skipping creation")
        else:
            raise
    
    # Create audit_logs table
    try:
        op.create_table('audit_logs',
            sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
            sa.Column('entity_type', sa.String(64), nullable=False, index=True),
            sa.Column('entity_id', sa.Integer(), nullable=False, index=True),
            sa.Column('action', sa.String(16), nullable=False, index=True),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
            sa.Column('timestamp', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.Column('data', sa.Text(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        print("Created audit_logs table")
    except OperationalError as e:
        if "already exists" in str(e):
            print("Table 'audit_logs' already exists, skipping creation")
        else:
            raise
    
    # Create initial Admin role if it doesn't exist
    try:
        conn.execute(
            sa.text("INSERT INTO roles (name) VALUES ('Admin')")
        )
        print("Created Admin role")
    except Exception as e:
        # Likely a duplicate entry error, role exists
        print(f"Admin role likely exists: {e}")


def downgrade():
    # Drop tables in reverse order (dependencies first)
    try:
        op.drop_table('audit_logs')
    except:
        pass
        
    try:
        op.drop_index('ix_user_currencies_user_id', table_name='user_currencies')
        op.drop_table('user_currencies')
    except:
        pass
        
    try:
        op.drop_table('currencies')
    except:
        pass
        
    try:
        op.drop_table('users')
    except:
        pass
        
    try:
        op.drop_table('roles')
    except:
        pass