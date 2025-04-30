import psycopg2

def list_users():
    conn = psycopg2.connect(
        dbname="postgres",
        user="postgres.xqyhrcznzkwkvgfcuebp",
        password="Y@rze2002",
        host="aws-0-eu-west-3.pooler.supabase.com",
        port="6543"
    )
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT username FROM users')
        users = cursor.fetchall()
        print("\nRegistered users:")
        print("----------------")
        for user in users:
            print(user[0])
    except psycopg2.Error as e:
        print(f"Error listing users: {str(e)}")
    finally:
        conn.close()

if __name__ == "__main__":
    list_users() 