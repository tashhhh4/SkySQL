from sqlalchemy import create_engine, text

QUERY_FLIGHT_BY_ID = """
  SELECT
    flights.*,
    airlines.airline,
    flights.ID as FLIGHT_ID,
    flights.DEPARTURE_DELAY as DELAY
  FROM flights
    JOIN airlines ON flights.airline = airlines.id
  WHERE flights.ID = :id
"""

QUERY_FLIGHTS_BY_DATE = """
  SELECT
    flights.ID,
    flights.ORIGIN_AIRPORT,
    flights.DESTINATION_AIRPORT,
    airlines.AIRLINE,
    flights.DEPARTURE_DELAY AS DELAY
  FROM flights
    JOIN airlines ON flights.AIRLINE = airlines.ID
  WHERE
    YEAR = :year
    AND MONTH = :month
    AND DAY = :day
"""

QUERY_DELAYED_FLIGHTS_BY_AIRLINE = """
  SELECT
    flights.ID,
    flights.ORIGIN_AIRPORT,
    flights.DESTINATION_AIRPORT,
    airlines.AIRLINE,
    flights.DEPARTURE_DELAY AS DELAY
  FROM flights
    JOIN airlines ON flights.AIRLINE = airlines.ID
  WHERE
    airlines.AIRLINE = :airline
    AND flights.DEPARTURE_DELAY >= 20
"""

QUERY_DELAYED_FLIGHTS_BY_AIRPORT = """
  SELECT
    flights.ID,
    flights.ORIGIN_AIRPORT,
    flights.DESTINATION_AIRPORT,
    airlines.AIRLINE,
    flights.DEPARTURE_DELAY AS DELAY
  FROM flights
    JOIN airlines ON flights.AIRLINE = airlines.ID
  WHERE
    flights.ORIGIN_AIRPORT = :airport
    AND flights.DEPARTURE_DELAY >= 20
"""

QUERY_PCT_DELAYED_FLIGHTS_BY_AIRLINE = """
  SELECT
    AIRLINE,
    TOTAL_FLIGHTS,
    DELAYED_FLIGHTS,
    100.0 * DELAYED_FLIGHTS / TOTAL_FLIGHTS AS 'PCT_DELAYED'
  FROM (
    SELECT
      airlines.AIRLINE,
      COUNT(*) AS 'TOTAL_FLIGHTS',
      SUM(CASE WHEN flights.DEPARTURE_DELAY >= 20 THEN 1 ELSE 0 END) AS 'DELAYED_FLIGHTS'
    FROM flights
      JOIN airlines ON flights.AIRLINE = airlines.ID
    GROUP BY
      flights.AIRLINE
  )
"""

QUERY_PCT_DELAYED_FLIGHTS_BY_HOUR = """
  SELECT
    HOUR,
    TOTAL_FLIGHTS,
    DELAYED_FLIGHTS,
    100.0 * DELAYED_FLIGHTS / TOTAL_FLIGHTS AS 'PCT_DELAYED'
  FROM (
    SELECT
      SUBSTRING(flights.SCHEDULED_DEPARTURE, 1, 2) AS HOUR,
    COUNT(*) AS 'TOTAL_FLIGHTS',
    SUM(CASE WHEN DEPARTURE_DELAY >= 20 THEN 1 ELSE 0 END) AS 'DELAYED_FLIGHTS'
    FROM flights
    GROUP BY SUBSTRING(flights.SCHEDULED_DEPARTURE, 1, 2)
  )
"""

QUERY_PCT_DELAYED_FLIGHTS_BY_ROUTE = """
  SELECT
    ORIGIN,
    DESTINATION,
    TOTAL_FLIGHTS,
    DELAYED_FLIGHTS,
    100.0 * DELAYED_FLIGHTS / TOTAL_FLIGHTS AS 'PCT_DELAYED'
  FROM (
    SELECT
      ORIGIN_AIRPORT AS 'ORIGIN',
    DESTINATION_AIRPORT AS 'DESTINATION',
    COUNT(*) AS 'TOTAL_FLIGHTS',
    SUM(CASE WHEN DEPARTURE_DELAY >= 20 THEN 1 ELSE 0 END) AS 'DELAYED_FLIGHTS'
    FROM flights
    GROUP BY ORIGIN_AIRPORT, DESTINATION_AIRPORT
  )
"""


# Define the database URL
DATABASE_URL = "sqlite:///data/flights.sqlite3"

# Create the engine
engine = create_engine(DATABASE_URL)


def execute_query(query, params=None):
    """
    Execute an SQL query with the params provided in a dictionary,
    and returns a list of records (dictionary-like objects).
    If an exception was raised, print the error, and return an empty list.
    """
    try:
        with engine.connect() as conn:
            results = conn.execute(text(query), params)
            rows = results.fetchall()
            return rows
    except Exception as e:
        print("Query error:", e)
        return []


def get_flight_by_id(flight_id):
    """
    Searches for flight details using flight ID.
    If the flight was found, returns a list with a single record.
    """
    params = {'id': flight_id}
    return execute_query(QUERY_FLIGHT_BY_ID, params)

    
def get_flights_by_date(day, month, year):
    """
    Searches for flights matching the given day, month, and year.
    Returns a list of all records.
    """
    params = {'day': day, 'month': month, 'year': year}
    return execute_query(QUERY_FLIGHTS_BY_DATE, params)


def get_delayed_flights_by_airline(airline_name):
    """
    Searches for delayed flights run by an airline company.
    Returns a list of all matching flight records.
    """
    params = {'airline': airline_name}
    return execute_query(QUERY_DELAYED_FLIGHTS_BY_AIRLINE, params)


def get_delayed_flights_by_airport(origin_airport):
    """
    Searched for delayed flights originating from the specified 3-letter
    airport code.
    Returns a list of all matching flight records.
    """
    params = {'airport': origin_airport}
    return execute_query(QUERY_DELAYED_FLIGHTS_BY_AIRPORT, params)


def get_pct_delayed_flights_by_airline():
    """
    Returns an analysis result containing the airline name, total flights, delayed flights,
    and percentage of delayed / total flights for each airline.
    """
    return execute_query(QUERY_PCT_DELAYED_FLIGHTS_BY_AIRLINE)


def get_pct_delayed_flights_by_hour():
    """
    Returns an analysis result containing the hour as a 2-character string, total flights, delayed flights,
    and percentage of delayed / total flights for each 1-hour slice of the 24-hour day.
    """
    return execute_query(QUERY_PCT_DELAYED_FLIGHTS_BY_HOUR)


def get_pct_delayed_flights_by_route():
    """
    Returns an analysis result containing the origin and destination airports (by 3-letter airport codes),
    delayed flights, total flights, and percentage of delayed / total flights for each
    route (=distinct grouping of origin + destination airport).
    """
    return execute_query(QUERY_PCT_DELAYED_FLIGHTS_BY_ROUTE)