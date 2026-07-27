import psycopg2

def run():
    try:
        conn = psycopg2.connect(dbname='postgres', user='postgres', password='admin', host='127.0.0.1')
        conn.autocommit = True
        cur = conn.cursor()
        
        # Terminate
        cur.execute("SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'test_eduorbit' AND pid != pg_backend_pid();")
        print("Terminated connections.")
        
        # Drop
        cur.execute("DROP DATABASE IF EXISTS test_eduorbit;")
        print("Successfully dropped database 'test_eduorbit'.")
        
        conn.close()
    except Exception as e:
        print("Error:", e)

if __name__ == '__main__':
    run()
