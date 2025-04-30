import psycopg2

def check_user(username):
    conn = psycopg2.connect(
        dbname="postgres",
        user="postgres.xqyhrcznzkwkvgfcuebp",
        password="Y@rze2002",
        host="aws-0-eu-west-3.pooler.supabase.com",
        port="6543"
    )
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT username, password_hash, email, phone
            FROM users 
            WHERE lower(username) = lower(%s)
        ''', (username,))
        
        result = cursor.fetchone()
        if result:
            print(f"\nUser found:")
            print(f"Username: {result[0]}")
            print(f"Password hash: {result[1]}")
            print(f"Email: {result[2]}")
            print(f"Phone: {result[3]}")
        else:
            print(f"\nNo user found with username: {username}")
            
    except psycopg2.Error as e:
        print(f"Error checking user: {str(e)}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_user("Drumnich") 