from contextlib import contextmanager
from django.db import connection
from psycopg2.extras import RealDictCursor


@contextmanager
def get_cursor():
    with connection.cursor() as cur:
        yield DictCursorWrapper(cur)


class DictCursorWrapper:
    """Wraps Django's cursor so fetchone/fetchall return dicts."""

    def __init__(self, cursor):
        self._cur = cursor

    def execute(self, sql, params=None):
        self._cur.execute(sql, params or [])

    def fetchone(self):
        row = self._cur.fetchone()
        if row is None:
            return None
        cols = [col[0] for col in self._cur.description]
        return dict(zip(cols, row))

    def fetchall(self):
        cols = [col[0] for col in self._cur.description]
        return [dict(zip(cols, row)) for row in self._cur.fetchall()]


def execute_query(sql, params=None, *, fetch="none"):
    with get_cursor() as cur:
        cur.execute(sql, params or [])
        if fetch == "one":
            return cur.fetchone()
        if fetch == "all":
            return cur.fetchall()
    return None