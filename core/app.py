# ============================================================
#  ManTech HRMS - apps.py
#  Location: C:\Users\Mantech PC_6\Documents\mantech_hrms_21\core\apps.py
#  REPLACE your entire apps.py with this file
# ============================================================

from django.apps import AppConfig
from django.db.backends.signals import connection_created


def set_sqlite_pragma(sender, connection, **kwargs):
    if connection.vendor == 'sqlite':
        cursor = connection.cursor()
        cursor.execute('PRAGMA journal_mode=WAL;')    # multiple users at same time
        cursor.execute('PRAGMA synchronous=NORMAL;')  # faster writes
        cursor.execute('PRAGMA cache_size=-64000;')   # 64MB memory cache
        cursor.execute('PRAGMA temp_store=MEMORY;')   # temp tables in RAM


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        connection_created.connect(set_sqlite_pragma)