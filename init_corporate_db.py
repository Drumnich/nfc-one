import psycopg2
import bcrypt
from datetime import datetime

def init_corporate_database():
    # Connect to database
    conn = psycopg2.connect(
        dbname="postgres",
        user="postgres.xqyhrcznzkwkvgfcuebp",
        password="Y@rze2002",
        host="aws-0-eu-west-3.pooler.supabase.com",
        port="6543"
    )
    cursor = conn.cursor()

    try:
        # Add user_type to users table
        cursor.execute('''
            ALTER TABLE users 
            ADD COLUMN IF NOT EXISTS user_type TEXT DEFAULT 'individual' 
            CHECK (user_type IN ('individual', 'building_admin', 'corporate_admin'))
        ''')

        # Create buildings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS buildings (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name TEXT NOT NULL,
                address TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create access_points table for physical doors/entry points
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS access_points (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                building_id UUID NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                access_level INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (building_id) REFERENCES buildings (id),
                UNIQUE(building_id, name)
            )
        ''')

        # Create cards table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cards (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID NOT NULL,
                card_uid TEXT NOT NULL,
                card_type TEXT NOT NULL,
                name TEXT,
                status TEXT DEFAULT 'active' CHECK (status IN ('active', 'revoked', 'pending')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                UNIQUE(card_uid)
            )
        ''')

        # Create card_access table for mapping cards to access points with specific permissions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS card_access (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                card_id UUID NOT NULL,
                access_point_id UUID NOT NULL,
                access_level INTEGER DEFAULT 1,
                schedule_start TIME,
                schedule_end TIME,
                days_of_week INTEGER[], -- Array of days (0-6, where 0 is Sunday)
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (card_id) REFERENCES cards (id),
                FOREIGN KEY (access_point_id) REFERENCES access_points (id),
                UNIQUE(card_id, access_point_id)
            )
        ''')

        # Create access_logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS access_logs (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                card_id UUID NOT NULL,
                access_point_id UUID NOT NULL,
                access_granted BOOLEAN NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (card_id) REFERENCES cards (id),
                FOREIGN KEY (access_point_id) REFERENCES access_points (id)
            )
        ''')

        # Create building_admins table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS building_admins (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                building_id UUID NOT NULL,
                user_id UUID NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (building_id) REFERENCES buildings (id),
                FOREIGN KEY (user_id) REFERENCES users (id),
                UNIQUE(building_id, user_id)
            )
        ''')

        # Create corporate_admins table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS corporate_admins (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID NOT NULL,
                company_name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                UNIQUE(user_id)
            )
        ''')

        # Create test building
        cursor.execute('''
            INSERT INTO buildings (name, address, description)
            VALUES ('Test Building', '123 Corporate Ave', 'Test corporate building')
            ON CONFLICT DO NOTHING
            RETURNING id
        ''')
        building_id = cursor.fetchone()[0]

        # Create test access points
        test_access_points = [
            ('Main Entrance', 'Front door', 1),
            ('Parking Gate', 'Vehicle access', 2),
            ('Server Room', 'Restricted access', 3),
            ('Office Area', 'General office access', 1)
        ]

        for name, description, level in test_access_points:
            cursor.execute('''
                INSERT INTO access_points (building_id, name, description, access_level)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            ''', (building_id, name, description, level))

        # Create test corporate admin
        password_hash = bcrypt.hashpw('admin123'.encode(), bcrypt.gensalt())
        cursor.execute('''
            INSERT INTO users (username, password_hash, email, user_type)
            VALUES ('corporate_admin', %s, 'corporate@example.com', 'corporate_admin')
            ON CONFLICT (username) DO NOTHING
            RETURNING id
        ''', (password_hash.decode('utf-8'),))
        admin_id = cursor.fetchone()[0]

        cursor.execute('''
            INSERT INTO corporate_admins (user_id, company_name)
            VALUES (%s, 'Test Corporation')
            ON CONFLICT DO NOTHING
        ''', (admin_id,))

        # Create test building admin
        password_hash = bcrypt.hashpw('building123'.encode(), bcrypt.gensalt())
        cursor.execute('''
            INSERT INTO users (username, password_hash, email, user_type)
            VALUES ('building_admin', %s, 'building@example.com', 'building_admin')
            ON CONFLICT (username) DO NOTHING
            RETURNING id
        ''', (password_hash.decode('utf-8'),))
        building_admin_id = cursor.fetchone()[0]

        cursor.execute('''
            INSERT INTO building_admins (building_id, user_id)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING
        ''', (building_id, building_admin_id))

        conn.commit()
        print("Corporate database initialization complete!")

    except psycopg2.Error as e:
        conn.rollback()
        print(f"Error initializing corporate database: {str(e)}")
    finally:
        conn.close()

if __name__ == '__main__':
    init_corporate_database() 