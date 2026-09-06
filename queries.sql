-- 1. Fleet Performance Metrics
-- Aggregates flight count, average speed, and altitude per airline.

SELECT 
airline_code,
COUNT(DISTINCT flights.flight_id) AS total_flights,
ROUND(AVG(baro_alt * 3.28084),0) AS avg_altitude_ft,
ROUND(AVG(velocity_knots),1) AS avg_speed_knots,
MAX(vertical_rate_fpm) AS max_climb_rate_fpm
FROM flights
INNER JOIN telemetry_logs ON telemetry_logs.flight_id = flights.flight_id
WHERE airline_code IS NOT NULL
GROUP BY airline_code
ORDER BY total_flights DESC;

2. Flight Phase Distribution
-- Categorizes flight phases and counts distribution per airline via window functions.

WITH state AS (
SELECT
f.flight_id,
callsign, 
airline_code, 
ROUND(baro_alt * 3.28084) AS altitude_ft,
velocity_knots,
vertical_rate_fpm,
CASE
    WHEN vertical_rate_fpm > 500 THEN 'Climb'
    WHEN vertical_rate_fpm < -500 THEN 'Descent'
    WHEN vertical_rate_fpm BETWEEN -500 AND +500 THEN 'Cruise' END AS 'flight_phase'
FROM telemetry_logs t
JOIN flights f ON f.flight_id = t.flight_id
)

SELECT callsign, 
airline_code, 
velocity_knots, 
vertical_rate_fpm, 
flight_phase, 
COUNT(*) OVER (PARTITION BY airline_code, flight_phase) AS airline_phase_count
FROM state
WHERE callsign IS NOT NULL AND airline_code IS NOT NULL
ORDER BY airline_code, airline_phase_count;


-- 3. Airspace Density Grid
-- Groups coordinates into 1-degree grids to identify high-traffic sectors.

SELECT 
ROUND(latitude,0) AS grid_lat,
ROUND(longitude,0) AS grid_lon,
COUNT(DISTINCT flight_id) AS total_flights,
ROUND(AVG(baro_alt * 3.28084)) AS avg_altitude_ft,
ROUND(AVG(velocity_knots)) AS avg_speed_knots
FROM telemetry_logs
WHERE latitude IS NOT NULL AND longitude IS NOT NULL
GROUP BY grid_lat, grid_lon
ORDER BY total_flights DESC;


-- 4. Critical Anomaly Detection
-- Flags aircraft with extreme vertical rates (>= 2500 fpm).

SELECT 
callsign,
airline_code,
origin_country,
ROUND(baro_alt * 3.28084) AS altitude_ft,
ROUND(velocity_knots, 1) AS velocity_knots,
vertical_rate_fpm,
CASE
    WHEN vertical_rate_fpm >= 2500 THEN 'Steep Climb'
    WHEN vertical_rate_fpm <= -2500 THEN 'Rapid Descent'
    END AS anomaly_type
FROM flights f
JOIN aircraft a ON a.icao24 = f.icao24
JOIN telemetry_logs t ON t.flight_id = f.flight_id
WHERE ABS(vertical_rate_fpm) >= 2500
ORDER BY ABS(vertical_rate_fpm) DESC;