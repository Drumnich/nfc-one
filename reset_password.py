import psycopg2
import bcrypt
import sys

def reset_password(username, new_password):
    # Database connection
    conn = psycopg2.connect(
        dbname="postgres",
        user="postgres.xqyhrcznzkwkvgfcuebp",
        password="Y@rze2002",
        host="aws-0-eu-west-3.pooler.supabase.com",
        port="6543"
    )
    cursor = conn.cursor()
    
    try:
        # Hash the new password
        password_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt())
        
        # Update the user's password
        cursor.execute('''
            UPDATE users 
            SET password_hash = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE username = %s
            RETURNING id
        ''', (password_hash, username))
        
        if cursor.fetchone():
            conn.commit()
            print(f"Password successfully reset for user: {username}")
            return True
        else:
            print(f"User {username} not found")
            return False
            
    except psycopg2.Error as e:
        print(f"Error resetting password: {str(e)}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python reset_password.py <username> <new_password>")
        sys.exit(1)
        
    username = sys.argv[1]
    new_password = sys.argv[2]
    reset_password(username, new_password) 