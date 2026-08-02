import os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings.local')
sys.path.insert(0, r'c:\Users\user\Desktop\Development\SMS')
import django; django.setup()
from django.db import connections
conn = connections['default']
conn.ensure_connection()
conn.connection.autocommit = True
cur = conn.connection.cursor()
cur.execute("SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'test_eduorbit' AND pid != pg_backend_pid()")
print('Terminated sessions:', cur.fetchall())
cur.execute('DROP DATABASE IF EXISTS test_eduorbit')
print('Dropped test_eduorbit OK')
