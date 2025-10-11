import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv


def main():
    load_dotenv()
    database_url = os.getenv('DATABASE_URL', 'postgresql://user:password@localhost:5432/smart_campus_db')
    sql_path = Path(__file__).parent / 'database.sql'
    sql = sql_path.read_text()

    conn = psycopg2.connect(database_url)
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            print('Database schema applied successfully.')
    finally:
        conn.close()


if __name__ == '__main__':
    main()
