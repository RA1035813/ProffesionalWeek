import os
import psycopg2
import time
from datetime import datetime
import logging

log = logging.getLogger("soilsms.db")

class DatabaseHandler:
    def __init__(self):
        self.dbname = os.getenv("POSTGRES_DB", "soilsms_db")
        self.user = os.getenv("POSTGRES_USER", "mijn_gebruiker")
        self.password = os.getenv("POSTGRES_PASSWORD", "mijn_wachtwoord")
        self.host = os.getenv("DB_HOST", "db")
        self.port = os.getenv("DB_PORT", "5432")
        self.conn = None

    def connect(self):
        try:
            self.conn = psycopg2.connect(
                dbname=self.dbname,
                user=self.user,
                password=self.password,
                host=self.host,
                port=self.port
            )
            log.info("Verbonden met de database.")
            return True
        except Exception as e:
            log.error(f"Database verbinding mislukt: {e}")
            return False

    def ensure_farmer_and_node(self, farmer_phone, node_id, lat, lon):
        if not self.conn: self.connect()
        try:
            with self.conn.cursor() as cur:
                # Check of boer bestaat
                cur.execute("SELECT id FROM farmers WHERE phone_number = %s", (farmer_phone,))
                farmer = cur.fetchone()
                if not farmer:
                    farmer_id = int(time.time())
                    cur.execute(
                        "INSERT INTO farmers (id, phone_number, name, created_at) VALUES (%s, %s, %s, %s) RETURNING id",
                        (farmer_id, farmer_phone, "Auto-Generated", datetime.now())
                    )
                    farmer_id = cur.fetchone()[0]
                else:
                    farmer_id = farmer[0]

                # Check of node bestaat
                cur.execute("SELECT node_id FROM farm_nodes WHERE node_id = %s", (node_id,))
                node = cur.fetchone()
                if not node:
                    cur.execute(
                        "INSERT INTO farm_nodes (node_id, farmer_id, latitude, longitude, installed_at) VALUES (%s, %s, %s, %s, %s)",
                        (node_id, farmer_id, lat, lon, datetime.now())
                    )
                self.conn.commit()
                return farmer_id
        except Exception as e:
            log.error(f"Error in ensure_farmer_and_node: {e}")
            self.conn.rollback()
            return None

    def log_reading(self, node_id, sensors, weather, advice, ai_model):
        if not self.conn: self.connect()
        try:
            reading_id = int(time.time() * 1000)
            with self.conn.cursor() as cur:
                # 1. Sensor Reading
                cur.execute(
                    """INSERT INTO sensor_readings 
                    (id, node_id, timestamp, moisture_pct, ph, nitrogen_mg_kg, phosphorus_mg_kg, potassium_mg_kg, soil_temp_c, air_temp_c, air_humid_pct)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (reading_id, node_id, datetime.now(), 
                     sensors.get('moisture_pct', 0), sensors.get('ph', 0),
                     sensors.get('nitrogen_mg_kg', 0), sensors.get('phosphorus_mg_kg', 0), sensors.get('potassium_mg_kg', 0),
                     sensors.get('soil_temp_c', 0), sensors.get('air_temp_c', 0), sensors.get('air_humid_pct', 0))
                )

                # 2. Weather Log (indien aanwezig)
                if weather and 'precipitation_sum' in weather:
                    rain = sum(weather['precipitation_sum']) if isinstance(weather['precipitation_sum'], list) else 0
                    temp = sum(weather['temperature_2m_max']) / len(weather['temperature_2m_max']) if 'temperature_2m_max' in weather else 0
                    cur.execute(
                        "INSERT INTO weather_logs (id, reading_id, forecast_rain_7d_mm, forecast_avg_temp_c) VALUES (%s, %s, %s, %s)",
                        (int(time.time() * 1000) + 1, reading_id, rain, temp)
                    )

                # 3. Advisory
                cur.execute(
                    "INSERT INTO advisories (id, reading_id, ai_model, message_content, sent_at, status) VALUES (%s, %s, %s, %s, %s, %s)",
                    (int(time.time() * 1000) + 2, reading_id, ai_model, advice, datetime.now(), "SENT")
                )

                self.conn.commit()
                log.info(f"Data succesvol opgeslagen in DB voor Node {node_id}")
        except Exception as e:
            log.error(f"Fout bij opslaan in database: {e}")
            self.conn.rollback()

    def close(self):
        if self.conn:
            self.conn.close()
