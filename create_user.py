import psycopg2
import bcrypt

def create_user(username, password, email=None, phone=None):
    conn = psycopg2.connect(
        dbname="postgres",
        user="postgres.xqyhrcznzkwkvgfcuebp",
        password="Y@rze2002",
        host="aws-0-eu-west-3.pooler.supabase.com",
        port="6543"
    )
    cursor = conn.cursor()
    
    try:
        # Hash the password
        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        
        # Create new user
        cursor.execute('''
            INSERT INTO users (username, password_hash, email, phone)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        ''', (username, password_hash, email, phone))
        
        user_id = cursor.fetchone()[0]
        conn.commit()
        print(f"Successfully created user: {username}")
        return True
    except psycopg2.Error as e:
        print(f"Error creating user: {str(e)}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    # Create user with exact case preference
    create_user(
        username="Drumnich",
        password="YourNewPassword123!",
        email=None,  # You can add your email if you want
        phone=None   # You can add your phone if you want
    ) 