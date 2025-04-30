import psycopg2
import bcrypt

# Set the email and new password
email = "drumnich@gmail.com"
new_password = "decembre 7"

def reset_password(email, new_password):
    conn = psycopg2.connect(
        dbname="postgres",
        user="postgres.xqyhrcznzkwkvgfcuebp",
        password="Y@rze2002",
        host="aws-0-eu-west-3.pooler.supabase.com",
        port="6543"
    )
    cursor = conn.cursor()
    try:
        password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
        cursor.execute('''
            UPDATE users
            SET password_hash = %s, updated_at = CURRENT_TIMESTAMP
            WHERE lower(email) = lower(%s)
            RETURNING id
        ''', (password_hash.decode('utf-8'), email))
        if cursor.fetchone():
            conn.commit()
            print(f"Password successfully reset for user: {email}")
        else:
            print(f"User with email {email} not found")
    except psycopg2.Error as e:
        print(f"Error resetting password: {str(e)}")
    finally:
        conn.close()

if __name__ == "__main__":
    reset_password(email, new_password) 