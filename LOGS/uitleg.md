structuur
![schema](schemaSQL.jpg)
### 1. `farmers` (Boeren)

Hierin sla je de gegevens van de boer op.
- **`id`** (Primary Key, Integer/UUID)
- **`phone_number`** (Varchar, Unique) - _Bijv. "+255712345678"_
- **`name`** (Varchar, Nullable) - _Voor als je later namen wilt toevoegen_
- **`created_at`** (Timestamp) - _Wanneer de boer is aangesloten op het systeem_

### 2. `farm_nodes` (Hardware)

Deze tabel representeert de fysieke Raspberry Pi/sensor-modules op de boerderij. Een boer kan theoretisch meerdere velden en dus meerdere nodes hebben.
- **`node_id`** (Primary Key, Varchar) - _Bijv. "FARM001" of "DEMO_NODE_001"_
- **`farmer_id`** (Foreign Key -> `farmers.id`)
- **`latitude`** (Decimal) - _Voor weersvoorspellingen (bijv. -6.3)_
- **`longitude`** (Decimal) - _Voor weersvoorspellingen (bijv. 34.8)_
- **`crop_type`** (Varchar, Nullable) - _Wat er momenteel groeit (bijv. "Maize")_
- **`installed_at`** (Timestamp)

### 3. `sensor_readings` (Metingen)

Dit is de zwaarste tabel, hier komt elk uur een nieuwe rij in per node. De kolommen matchen exact met de JSON-payload uit jouw `sensor_node.py`.
- **`id`** (Primary Key, BigInt/UUID)
- **`node_id`** (Foreign Key -> `farm_nodes.node_id`)
- **`timestamp`** (Timestamp) - _Tijdstip van de meting_
- **`moisture_pct`** (Decimal) - _Bodemvocht in %_
- **`ph`** (Decimal) - _Bodem pH-waarde_
- **`nitrogen_mg_kg`** (Integer) - _Stikstof (N)_
- **`phosphorus_mg_kg`** (Integer) - _Fosfor (P)_
- **`potassium_mg_kg`** (Integer) - _Kalium (K)_
- **`soil_temp_c`** (Decimal) - _Bodemtemperatuur in °C_
- **`air_temp_c`** (Decimal) - _Luchttemperatuur in °C_
- **`air_humid_pct`** (Decimal) - _Luchtvochtigheid in %_

### 4. `weather_logs` (Weersvoorspellingen)

Omdat je via de Open-Meteo API een 7-daagse weersvoorspelling ophaalt (`precipitation_sum`, `temperature_2m_max`), is het waardevol om op te slaan wát er destijds voorspeld was.
- **`id`** (Primary Key, BigInt)
- **`reading_id`** (Foreign Key -> `sensor_readings.id`) - _Koppelt het weer aan de specifieke sensormeting_
- **`forecast_rain_7d_mm`** (Decimal) - _Verwachte regen in de komende 7 dagen_
- **`forecast_avg_temp_c`** (Decimal) - _Verwachte gemiddelde temperatuur_

### 5. `advisories` (Verstuurde SMS Adviezen)

Hier houd je bij welk AI-advies er naar aanleiding van de data is gegenereerd en teruggestuurd.
- **`id`** (Primary Key, BigInt)
- **`reading_id`** (Foreign Key -> `sensor_readings.id`) - _Op welke specifieke meting is dit advies gebaseerd?_
- **`ai_model`** (Varchar) - _Bijv. "Gemini-1.5-flash" of "Ollama/Mistral"_
- **`message_content`** (Text/Varchar 160) - _De exacte SMS-tekst die verstuurd is_
- **`sent_at`** (Timestamp)
- **`status`** (Varchar) - _Bijv. "Success" of "Failed"_


```sql
DROP TABLE IF EXISTS advisories;
DROP TABLE IF EXISTS weather_logs;
DROP TABLE IF EXISTS sensor_readings;
DROP TABLE IF EXISTS farm_nodes;
DROP TABLE IF EXISTS farmers;


CREATE TABLE farmers(
    id INTEGER PRIMARY KEY NOT NULL,
    phone_number VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL
);

CREATE TABLE farm_nodes(
    node_id VARCHAR(255) PRIMARY KEY NOT NULL,
    farmer_id INTEGER NOT NULL REFERENCES farmers(id),
    latitude DECIMAL(8, 2) NOT NULL,
    longitude DECIMAL(8, 2) NOT NULL,
    crop_type VARCHAR(255) NULL,
    installed_at TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL
);

CREATE TABLE sensor_readings(
    id BIGINT PRIMARY KEY NOT NULL,
    node_id VARCHAR(255) NOT NULL REFERENCES farm_nodes(node_id),
    timestamp TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL,
    moisture_pct DECIMAL(8, 2) NOT NULL,
    ph DECIMAL(8, 2) NOT NULL,
    nitrogen_mg_kg INTEGER NOT NULL,
    phosphorus_mg_kg INTEGER NOT NULL,
    potassium_mg_kg INTEGER NOT NULL,
    soil_temp_c DECIMAL(8, 2) NOT NULL,
    air_temp_c DECIMAL(8, 2) NOT NULL,
    air_humid_pct DECIMAL(8, 2) NOT NULL
);

CREATE TABLE weather_logs(
    id BIGINT PRIMARY KEY NOT NULL,
    reading_id BIGINT NOT NULL REFERENCES sensor_readings(id),
    forecast_rain_7d_mm DECIMAL(8, 2) NOT NULL,
    forecast_avg_temp_c DECIMAL(8, 2) NOT NULL
);

CREATE TABLE advisories(
    id BIGINT PRIMARY KEY NOT NULL,
    reading_id BIGINT NOT NULL REFERENCES sensor_readings(id),
    ai_model VARCHAR(255) NOT NULL,
    message_content TEXT NOT NULL,
    sent_at TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL,
    status VARCHAR(255) NOT NULL
);
```