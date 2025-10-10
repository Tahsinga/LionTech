from django.apps import AppConfig
from django.db import connections
from django.db.utils import OperationalError
import logging


class WebsiteConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'website'

    def ready(self):
        # Import signal handlers so they are registered
        try:
            from . import signals  # noqa: F401
        except Exception:
            pass
        # Ensure SQLite uses WAL journal mode and a reasonable busy timeout to reduce
        # "database is locked" errors during concurrent access in development.
        # This is best-effort and non-fatal if it fails.
        try:
            logger = logging.getLogger(__name__)
            conn = connections['default']
            # Only apply for sqlite backend
            if conn.settings_dict.get('ENGINE', '').endswith('sqlite3'):
                cursor = conn.cursor()
                try:
                    cursor.execute('PRAGMA journal_mode=WAL;')
                    cursor.execute('PRAGMA busy_timeout=20000;')
                    logger.info('Enabled SQLite WAL and busy_timeout')
                finally:
                    try:
                        cursor.close()
                    except Exception:
                        pass
        except OperationalError:
            # DB might not exist yet during migrations; ignore
            pass
        except Exception:
            # Non-fatal; log and continue
            logging.exception('Failed to set SQLite pragmas in ready()')
