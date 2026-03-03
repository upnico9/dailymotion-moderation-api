from contextlib import contextmanager
from pathlib import Path

import psycopg2
from psycopg2 import pool


def create_connection_pool(
    database_url: str,
    min_connections: int = 2,
    max_connections: int = 10,
) -> pool.ThreadedConnectionPool:
    return pool.ThreadedConnectionPool(
        min_connections, max_connections, dsn=database_url
    )


@contextmanager
def get_connection(connection_pool: pool.ThreadedConnectionPool):

    connection = connection_pool.getconn()
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection_pool.putconn(connection)


def initialize_database(connection_pool: pool.ThreadedConnectionPool) -> None:
    migrations_path = Path(__file__).parent.parent / "migrations" / "init.sql"
    sql_script = migrations_path.read_text()

    with get_connection(connection_pool) as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql_script)
