import requests
from bs4 import BeautifulSoup
import psycopg2
import logging
import os


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


db_config = {
    'dbname': os.getenv('DB_NAME', 'egor'),
    'user': os.getenv('DB_USER', 'egor2005'),
    'password': os.getenv('DB_PASSWORD', '123'),
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', 5432)
}

def insert_hero(name, info_url):
    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()

        insert_query = """
        INSERT INTO heroes (name, information) 
        VALUES (%s, %s)
        ON CONFLICT (name) DO NOTHING;
        """

        cursor.execute(insert_query, (name, info_url))
        conn.commit()

        logger.info(f"Hero {name} added successfully")

    except Exception as e:
        logger.error(f"Error inserting hero {name}: {e}")
    finally:
        if conn:
            cursor.close()
            conn.close()


def fetch_heroes():
    url = "https://dota2.ru/esport/stats/filter/1/"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        
        soup = BeautifulSoup(response.text, 'html.parser')

        
        rows = soup.find_all('tr', class_='title')

        for row in rows:
            
            hero_name = row.find('span', class_='text-clip').text.strip()
            hero_link = "https://dota2.ru" + row.find('a')['href']

            
            insert_hero(hero_name, hero_link)

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching page: {e}")


fetch_heroes()
