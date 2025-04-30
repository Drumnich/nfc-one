import psycopg2
import bcrypt
from datetime import datetime, timedelta

def init_database():
    # Connect to database
    conn = psycopg2.connect(
        dbname="postgres",
        user="postgres.xqyhrcznzkwkvgfcuebp",
        password="Y@rze2002",
        host="aws-0-eu-west-3.pooler.supabase.com",
        port="6543"
    )
    cursor = conn.cursor()

    # Create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS locations (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            UNIQUE(user_id, name)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS access_points (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL,
            location_id UUID NOT NULL,
            card_id TEXT NOT NULL,
            access_level INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (location_id) REFERENCES locations (id),
            UNIQUE(location_id, card_id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS card_history (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL,
            card_id TEXT NOT NULL,
            card_type TEXT NOT NULL,
            custom_name TEXT,
            frequency TEXT,
            first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # Create test users
    test_users = [
        {
            'username': 'admin',
            'password': 'admin123',
            'email': 'admin@example.com',
            'phone': '+1234567890'
        },
        {
            'username': 'test_user',
            'password': 'test123',
            'email': 'test@example.com',
            'phone': '+0987654321'
        }
    ]

    for user in test_users:
        password_hash = bcrypt.hashpw(user['password'].encode(), bcrypt.gensalt())
        try:
            cursor.execute('''
                INSERT INTO users (username, password_hash, email, phone)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (username) DO NOTHING
                RETURNING id
            ''', (user['username'], password_hash, user['email'], user['phone']))
            print(f"Created user: {user['username']}")
        except psycopg2.Error as e:
            print(f"Error creating user {user['username']}: {str(e)}")

    # Create test locations for admin user
    admin_locations = [
        ('Home', 'Main residence'),
        ('Office', 'Work location'),
        ('Garage', 'Car parking'),
        ('Storage', 'Storage unit')
    ]

    cursor.execute('SELECT id FROM users WHERE username = %s', ('admin',))
    admin_id = cursor.fetchone()[0]

    for name, description in admin_locations:
        try:
            cursor.execute('''
                INSERT INTO locations (user_id, name, description)
                VALUES (%s, %s, %s)
                ON CONFLICT (user_id, name) DO NOTHING
            ''', (admin_id, name, description))
            print(f"Created location: {name}")
        except psycopg2.Error as e:
            print(f"Error creating location {name}: {str(e)}")

    # Create some test card history
    test_cards = [
        {
            'card_id': 'AABB112233445566',
            'card_type': 'JCOP 3 (J3R200)',
            'custom_name': 'Main Access Card',
            'frequency': '13.56 MHz'
        },
        {
            'card_id': 'CCDD998877665544',
            'card_type': 'JCOP 3 (J3R200)',
            'custom_name': 'Backup Card',
            'frequency': '13.56 MHz'
        }
    ]

    # Get current timestamp
    now = datetime.now()

    for card in test_cards:
        try:
            # Add card to history
            cursor.execute('''
                INSERT INTO card_history 
                (user_id, card_id, card_type, custom_name, frequency, first_seen, last_seen)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            ''', (
                admin_id,
                card['card_id'],
                card['card_type'],
                card['custom_name'],
                card['frequency'],
                now - timedelta(days=30),  # First seen 30 days ago
                now  # Last seen now
            ))
            print(f"Added card to history: {card['custom_name']}")

            # Add card access to some locations
            cursor.execute('SELECT id FROM locations WHERE user_id = %s LIMIT 2', (admin_id,))
            locations = cursor.fetchall()
            
            for location_id in locations:
                try:
                    cursor.execute('''
                        INSERT INTO access_points (user_id, location_id, card_id)
                        VALUES (%s, %s, %s)
                        ON CONFLICT DO NOTHING
                    ''', (admin_id, location_id[0], card['card_id']))
                    print(f"Added card access for location ID: {location_id[0]}")
                except psycopg2.Error as e:
                    print(f"Error adding card access: {str(e)}")

        except psycopg2.Error as e:
            print(f"Error adding card {card['card_id']}: {str(e)}")

    # Commit changes and close connection
    conn.commit()
    conn.close()

if __name__ == '__main__':
    print("Initializing database...")
    init_database()
    print("Database initialization complete!") 