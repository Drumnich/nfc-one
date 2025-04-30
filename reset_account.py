import psycopg2
import bcrypt

def reset_account(username, new_password):
    conn = psycopg2.connect(
        dbname="postgres",
        user="postgres.xqyhrcznzkwkvgfcuebp",
        password="Y@rze2002",
        host="aws-0-eu-west-3.pooler.supabase.com",
        port="6543"
    )
    cursor = conn.cursor()
    
    try:
        # First, delete the existing account
        cursor.execute('DELETE FROM users WHERE lower(username) = lower(%s)', (username,))
        
        # Create new password hash
        password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
        
        # Create new account
        cursor.execute('''
            INSERT INTO users (username, password_hash)
            VALUES (%s, %s)
            RETURNING id
        ''', (username, password_hash.decode('utf-8')))  # Store hash as string
        
        conn.commit()
        print(f"Successfully reset account for {username}")
        print(f"You can now log in with:")
        print(f"Username: {username}")
        print(f"Password: {new_password}")
        
    except psycopg2.Error as e:
        print(f"Error resetting account: {str(e)}")
    finally:
        conn.close()

if __name__ == "__main__":
    # Reset the account with a new password
    reset_account("Drumnich", "MyNewPassword123!") 