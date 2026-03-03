import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from infrastructure.database import create_connection_pool, get_connection, initialize_database


@pytest.fixture(scope="session")
def db_pool():
    database_url = os.environ.get(
        "DATABASE_URL",
        "host=localhost port=5438 dbname=moderation_db user=moderation password=moderation",
    )
    pool = create_connection_pool(database_url, min_connections=1, max_connections=5)
    initialize_database(pool)
    yield pool
    pool.closeall()


@pytest.fixture(autouse=True)
def clean_db(db_pool):
    with get_connection(db_pool) as conn:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE video_logs, videos_queue CASCADE")
    yield
