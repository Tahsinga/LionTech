from django.db import connections
from django.utils.deprecation import MiddlewareMixin
import logging


class SqlitePragmaMiddleware(MiddlewareMixin):
    """Middleware that ensures SQLite uses WAL and a busy timeout on first request.

    This runs when the DB is available and avoids doing this during app import / ready().
    It's best-effort and non-fatal.
    """
    executed = False

    def process_request(self, request):
        if SqlitePragmaMiddleware.executed:
            return None
        try:
            conn = connections['default']
            if conn.settings_dict.get('ENGINE', '').endswith('sqlite3'):
                cursor = conn.cursor()
                try:
                    cursor.execute('PRAGMA journal_mode=WAL;')
                    cursor.execute('PRAGMA busy_timeout=20000;')
                    logging.getLogger(__name__).info('Applied SQLite WAL and busy_timeout via middleware')
                finally:
                    try:
                        cursor.close()
                    except Exception:
                        pass
        except Exception:
            logging.exception('Failed to apply SQLite pragmas in middleware')
        SqlitePragmaMiddleware.executed = True
        return None
