import psycopg2

def setup():
    conn = psycopg2.connect(dbname='postgres', user='postgres', host='127.0.0.1')
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("ALTER USER postgres WITH PASSWORD 'admin';")
    print("PostgreSQL user 'postgres' password set to 'admin'.")
    
    cur.execute("SELECT 1 FROM pg_database WHERE datname='eduorbit'")
    exists = cur.fetchone()
    if not exists:
        cur.execute("CREATE DATABASE eduorbit;")
        print("Created PostgreSQL database 'eduorbit'.")
    else:
        print("PostgreSQL database 'eduorbit' already exists.")
        
    conn.close()

if __name__ == '__main__':
    setup()
