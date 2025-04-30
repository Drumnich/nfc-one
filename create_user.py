import psycopg2
import bcrypt

def create_user(username, password, email):
    conn = psycopg2.connect(
        dbname="postgres",
        user="postgres.xqyhrcznzkwkvgfcuebp",
        password="Y@rze2002",
        host="aws-0-eu-west-3.pooler.supabase.com",
        port="6543"
    )
    cursor = conn.cursor()
    try:
        # Check if email already exists
        cursor.execute('SELECT email FROM users WHERE lower(email) = lower(%s)', (email,))
        if cursor.fetchone():
            print(f"User with email {email} already exists.")
            return
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        cursor.execute('INSERT INTO users (username, password_hash, email) VALUES (%s, %s, %s)',
                     (username, password_hash.decode('utf-8'), email))
        conn.commit()
        print(f"User created: {email}")
    except psycopg2.Error as e:
        print(f"Error creating user: {str(e)}")
    finally:
        conn.close()

if __name__ == "__main__":
    create_user("drumnich", "decembre 7", "drumnich@gmail.com") 