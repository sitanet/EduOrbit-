import psycopg2

def run():
    try:
        conn = psycopg2.connect(dbname='postgres', user='postgres', password='admin', host='127.0.0.1')
        conn.autocommit = True
        cur = conn.cursor()
        
        cur.execute("""
            SELECT pid, datname, query, state, wait_event_type, wait_event, query_start
            FROM pg_stat_activity 
            WHERE query NOT LIKE '%pg_stat_activity%';
        """)
        rows = cur.fetchall()
        print(f"All active/idle connections ({len(rows)}):")
        for row in rows:
            print(row)
            
        conn.close()
    except Exception as e:
        print("Error:", e)

if __name__ == '__main__':
    run()
