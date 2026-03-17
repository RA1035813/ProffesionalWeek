structuur
![schema](schemaSQL.jpg)

### 1. `farmers` (Farmers)

This is where you store the farmer's data.
- **`id`** (Primary Key, Integer/UUID)
- **`phone_number`** (Varchar, Unique) - _e.g., “+255712345678”_
- **`name`** (Varchar, Nullable) - _In case you want to add names later_
- **`created_at`** (Timestamp) - _When the farmer was added to the system_

### 2. `farm_nodes` (Hardware)

This table represents the physical Raspberry Pi/sensor modules on the farm. A farmer can theoretically have multiple fields and thus multiple nodes.
- **`node_id`** (Primary Key, Varchar) - _E.g., “FARM001” or “DEMO_NODE_001”_
- **`farmer_id`** (Foreign Key -> `farmers.id`)
- **`latitude`** (Decimal) - _For weather forecasts (e.g., -6.3)_
- **`longitude`** (Decimal) - _For weather forecasts (e.g., 34.8)_
- **`crop_type`** (Varchar, Nullable) - _What is currently growing (e.g., “Maize”)_
- **`installed_at`** (Timestamp)


### 3. `sensor_readings` (Measurements)

This is the heaviest table; a new row is added here every hour for each node. The columns match exactly the JSON payload from your `sensor_node.py`.
- **`id`** (Primary Key, BigInt/UUID)
- **`node_id`** (Foreign Key -> `farm_nodes.node_id`)
- **`timestamp`** (Timestamp) - _Time of measurement_
- **`moisture_pct`** (Decimal) - _Soil moisture in %_
- **`ph`** (Decimal) - _Soil pH value_
- **`nitrogen_mg_kg`** (Integer) - _Nitrogen (N)_
- **`phosphorus_mg_kg`** (Integer) - _Phosphorus (P)_
- **`potassium_mg_kg`** (Integer) - _Potassium (K)_
- **`soil_temp_c`** (Decimal) - _Soil temperature in °C_
- **`air_temp_c`** (Decimal) - _Air temperature in °C_
- **`air_humid_pct`** (Decimal) - _Humidity in %_

### 4. `weather_logs` (Weather Forecasts)

Since you retrieve a 7-day weather forecast via the Open-Meteo API (`precipitation_sum`, `temperature_2m_max`), it’s useful to store what was actually forecast at the time.
- **`id`** (Primary Key, BigInt)
- **`reading_id`** (Foreign Key -> `sensor_readings.id`) - _Links the weather to the specific sensor reading_
- **`forecast_rain_7d_mm`** (Decimal) - _Expected rainfall over the next 7 days_
- **`forecast_avg_temp_c`** (Decimal) - _Expected average temperature_

### 5. `advisories` (Sent SMS Advisories)

Here you track which AI advisory was generated based on the data and sent back.
- **`id`** (Primary Key, BigInt)
- **`reading_id`** (Foreign Key -> `sensor_readings.id`) - _Which specific measurement is this recommendation based on?_
- **`ai_model`** (Varchar) - _E.g., “Gemini-1.5-flash” or “Ollama/Mistral”_
- **`message_content`** (Text/Varchar 160) - _The exact SMS text that was sent_
- **`sent_at`** (Timestamp)
- **`status`** (Varchar) - _E.g., “Success” or “Failed”_


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
    farmer_id INTEGER NOT NULL,
    latitude DECIMAL(8, 2) NOT NULL,
    longitude DECIMAL(8, 2) NOT NULL,
    crop_type VARCHAR(255) NULL,
    installed_at TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL,

    FOREIGN KEY (farmer_id) REFERENCES farmers(id)
);

CREATE TABLE sensor_readings(
    id BIGINT PRIMARY KEY NOT NULL,
    node_id VARCHAR(255) NOT NULL,
    timestamp TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL,
    moisture_pct DECIMAL(8, 2) NOT NULL,
    ph DECIMAL(8, 2) NOT NULL,
    nitrogen_mg_kg INTEGER NOT NULL,
    phosphorus_mg_kg INTEGER NOT NULL,
    potassium_mg_kg INTEGER NOT NULL,
    soil_temp_c DECIMAL(8, 2) NOT NULL,
    air_temp_c DECIMAL(8, 2) NOT NULL,
    air_humid_pct DECIMAL(8, 2) NOT NULL,

    FOREIGN KEY (node_id) REFERENCES farm_nodes(node_id)
);

CREATE TABLE weather_logs(
    id BIGINT PRIMARY KEY NOT NULL,
    reading_id BIGINT NOT NULL,
    forecast_rain_7d_mm DECIMAL(8, 2) NOT NULL,
    forecast_avg_temp_c DECIMAL(8, 2) NOT NULL,

    FOREIGN KEY (reading_id) REFERENCES sensor_readings(id)
);

CREATE TABLE advisories(
    id BIGINT PRIMARY KEY NOT NULL,
    reading_id BIGINT NOT NULL,
    ai_model VARCHAR(255) NOT NULL,
    message_content TEXT NOT NULL,
    sent_at TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL,
    status VARCHAR(255) NOT NULL,

    FOREIGN KEY (reading_id) REFERENCES sensor_readings(id)
);
```
