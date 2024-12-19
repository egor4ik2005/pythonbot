import psycopg2
import logging
import os
import time

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

db_config = {
    'dbname': os.getenv('DB_NAME', 'egor'),
    'user': os.getenv('DB_USER', 'egor2005'),
    'password': os.getenv('DB_PASSWORD', '123'),
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', 5432)
}

def wait_for_db():
    while True:
        try:
            conn = psycopg2.connect(**db_config)
            conn.close()
            logger.info("Database is ready")
            break
        except psycopg2.OperationalError:
            logger.info("Database not ready, retrying in 5 seconds...")
            time.sleep(5)

def create_heroes_table():
    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()

        create_table_query = """
        CREATE TABLE IF NOT EXISTS heroes (
            name VARCHAR(255) PRIMARY KEY,
            information TEXT
        );
        """

        cursor.execute(create_table_query)
        conn.commit()

        logger.info("Table 'heroes' created successfully")

    except Exception as e:
        logger.error(f"Error creating table: {e}")
    finally:
        if conn:
            cursor.close()
            conn.close()

if __name__ == "__main__":
    wait_for_db()
    create_heroes_table()
