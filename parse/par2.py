import requests
from bs4 import BeautifulSoup
import psycopg2
import logging
import time
import re
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

def clean_text(text):
    if not text:
        return "No information available"
    text = re.sub(r'\s+', ' ', text)
    text = text.replace('\xa0', ' ').strip()
    return text

def fetch_with_retries(url, retries=3, delay=5):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
            time.sleep(delay)
    return None

def fetch_hero_info(hero_name, hero_url):
    response = fetch_with_retries(hero_url)
    if not response:
        logger.error(f"Failed to fetch page for {hero_name} after retries")
        return None, None

    soup = BeautifulSoup(response.text, 'html.parser')

    description_div = soup.find('div', class_='base-hero-hero__descr-text')
    hero_description = clean_text(description_div.get_text()) if description_div else "No information available"
    hero_description = re.sub(re.escape(hero_name), "", hero_description, flags=re.IGNORECASE)

    damage_data = soup.find(attrs={'data-base-damage': True})
    if damage_data:
        base_damage = re.match(r'(\d+)', damage_data['data-base-damage'])
        base_damage = int(base_damage.group(1)) if base_damage else None
    else:
        base_damage = None

    if base_damage is None:
        logger.warning(f"No base damage found for {hero_name}")

    return hero_description, base_damage

def insert_hero_info(name, info_data, base_damage):
    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        insert_query = """
        INSERT INTO heroes_info (name, info_data, base_damage) 
        VALUES (%s, %s, %s)
        ON CONFLICT (name) DO UPDATE SET 
            info_data = EXCLUDED.info_data,
            base_damage = EXCLUDED.base_damage;
        """
        cursor.execute(insert_query, (name, info_data, base_damage))
        conn.commit()
        logger.info(f"Info for {name} added/updated successfully")
    except Exception as e:
        logger.error(f"Error inserting info for {name}: {e}")
    finally:
        if conn:
            cursor.close()
            conn.close()

def update_heroes_info():
    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        select_query = "SELECT name, information FROM heroes;"
        cursor.execute(select_query)
        rows = cursor.fetchall()

        failed_heroes = []

        for row in rows:
            hero_name = row[0]
            hero_url = row[1]
            hero_info, base_damage = fetch_hero_info(hero_name, hero_url)

            if hero_info is not None:
                try:
                    insert_hero_info(hero_name, hero_info, base_damage)
                except Exception as e:
                    failed_heroes.append(hero_name)
                    logger.error(f"Failed to add info for {hero_name}: {e}")
            else:
                failed_heroes.append(hero_name)

            time.sleep(2)

        if failed_heroes:
            logger.error(f"Failed to update info for the following heroes: {', '.join(failed_heroes)}")

    except Exception as e:
        logger.error(f"Error updating heroes info: {e}")
    finally:
        if conn:
            cursor.close()
            conn.close()

def create_heroes_info_table():
    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        create_table_query = """
        CREATE TABLE IF NOT EXISTS heroes_info (
            name TEXT PRIMARY KEY,
            info_data TEXT,
            base_damage INTEGER
        );
        """
        cursor.execute(create_table_query)
        conn.commit()
        logger.info("Table heroes_info created successfully")
    except Exception as e:
        logger.error(f"Error creating table: {e}")
    finally:
        if conn:
            cursor.close()
            conn.close()
def print_heroes_info():
    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        select_query = "SELECT name, info_data, base_damage FROM heroes_info;"
        cursor.execute(select_query)
        rows = cursor.fetchall()

        if rows:
            print("Hero Information:\n")
            for row in rows:
                name, info_data, base_damage = row
                print(f"Name: {name}")
                print(f"Info: {info_data}")
                print(f"Base Damage: {base_damage}\n")
        else:
            print("No hero information found.")
    except Exception as e:
        logger.error(f"Error fetching hero info: {e}")
    finally:
        if conn:
            cursor.close()
            conn.close()

create_heroes_info_table()
update_heroes_info()
print_heroes_info()
