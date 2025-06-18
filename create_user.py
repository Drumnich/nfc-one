import psycopg2
import bcrypt

conn = psycopg2.connect(
    dbname="postgres",
    user="postgres.xqyhrcznzkwkvgfcuebp",
    password="Yarzedcembre",
    host="aws-0-eu-west-3.pooler.supabase.com",
    port="6543"
)
cur = conn.cursor()

email = 'drumnich@gmail.com'
password = 'Yarze2002'
password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

try:
    cur.execute('''
        INSERT INTO users (email, password_hash, username)
        VALUES (%s, %s, %s)
        ON CONFLICT (email) DO NOTHING
    ''', (email, password_hash, 'drumnich'))
    conn.commit()
    print('User created or already exists.')
except Exception as e:
    print('Error:', e)
finally:
    cur.close()
    conn.close() 