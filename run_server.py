import os
import sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

from waitress import serve
from core.wsgi import application


# Add your project root to Python path
# sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("=" * 45)
print("  ManTech HRMS Server Starting...")
print("  URL: http://0.0.0.0:8000")
print("=" * 45)

serve(
    application,
    host='0.0.0.0',
    port=8000,
    threads=8,            # ← sweet spot for SQLite
    connection_limit=50,
    channel_timeout=60,
    cleanup_interval=10,
    ident='ManTech HRMS',
)

# waitress-serve --host=0.0.0.0 --port=8000 --threads=16 hrms_project.wsgi:application