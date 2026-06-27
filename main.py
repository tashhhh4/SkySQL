import csv
import sqlalchemy
from datetime import datetime
import flights_data
import graphs

IATA_LENGTH = 3


def save_fig(fig):
    """
    Prompts the user for a filename and executes fig.savefig,
    creating a new png image in the local filesystem.
    `fig` must be a figure created from the matplotlib library.
    """
    filename = input("Enter filename (e.g., chart.png): ")
    fig.savefig(filename, pad_inches=0, bbox_inches='tight')


def save_csv(results):
    y_n = input("Would you like to export this data to a CSV file? (y/n) ")
    if y_n.lower() == 'y':
        try:
            filename = input("Enter filename (e.g., results.csv): ")
            with open(filename, 'w', newline='') as file:
                writer = csv.DictWriter(
                    file,
                    fieldnames=[
                        'ID',
                        'ORIGIN_AIRPORT',
                        'DESTINATION_AIRPORT',
                        'AIRLINE',
                        'DELAY'
                    ],
                    extrasaction='ignore')
                writer.writeheader()
                for result in results:
                    data = result._mapping
                    writer.writerow(data)
        except FileNotFoundError:
            print('Failed to save results due to invalid filename.')


def print_results(results):
    """
    Get a list of flight results (List of dictionary-like objects from SQLAachemy).
    Even if there is one result, it should be provided in a list.
    Each object *has* to contain the columns:
    FLIGHT_ID, ORIGIN_AIRPORT, DESTINATION_AIRPORT, AIRLINE, and DELAY.
    """
    for result in results:
        # turn result into dictionary
        result = result._mapping

        # Check that all required columns are in place
        try:
            delay = int(result['DELAY']) if result['DELAY'] else 0  # If delay columns is NULL, set it to 0
            origin = result['ORIGIN_AIRPORT']
            dest = result['DESTINATION_AIRPORT']
            airline = result['AIRLINE']
        except (ValueError, sqlalchemy.exc.SQLAlchemyError) as e:
            print("Error showing results: ", e)
            return

        # Different prints for delayed and non-delayed flights
        if delay and delay > 0:
            print(f"{result['ID']}. {origin} -> {dest} by {airline}, Delay: {delay} Minutes")
        else:
            print(f"{result['ID']}. {origin} -> {dest} by {airline}")

    print(f"Got {len(results)} results.")

    save_csv(results)


def delayed_flights_by_airline():
    """
    Asks the user for a textual airline name (any string will work here).
    Then runs the query using the data object method "get_delayed_flights_by_airline".
    When results are back, calls "print_results" to show them to on the screen.
    """
    airline_input = input("Enter airline name: ")
    results = flights_data.get_delayed_flights_by_airline(airline_input)
    print_results(results)


def delayed_flights_by_airport():
    """
    Asks the user for a textual IATA 3-letter airport code (loops until input is valid).
    Then runs the query using the data object method "get_delayed_flights_by_airport".
    When results are back, calls "print_results" to show them to on the screen.
    """
    valid = False
    while not valid:
        airport_input = input("Enter origin airport IATA code: ")
        # Valide input
        if airport_input.isalpha() and len(airport_input) == IATA_LENGTH:
            valid = True
    results = flights_data.get_delayed_flights_by_airport(airport_input)
    print_results(results)


def flight_by_id():
    """
    Asks the user for a numeric flight ID,
    Then runs the query using the data object method "get_flight_by_id".
    When results are back, calls "print_results" to show them to on the screen.
    """
    valid = False
    while not valid:
        try:
            id_input = int(input("Enter flight ID: "))
        except Exception as e:
            print("Try again...")
        else:
            valid = True
    results = flights_data.get_flight_by_id(id_input)
    print_results(results)


def flights_by_date():
    """
    Asks the user for date input (and loops until it's valid),
    Then runs the query using the data object method "get_flights_by_date".
    When results are back, calls "print_results" to show them to on the screen.
    """
    valid = False
    while not valid:
        try:
            date_input = input("Enter date in DD/MM/YYYY format: ")
            date = datetime.strptime(date_input, '%d/%m/%Y')
        except ValueError as e:
            print("Try again...", e)
        else:
            valid = True
    results = flights_data.get_flights_by_date(date.day, date.month, date.year)
    print_results(results)


def pct_delays_by_airline_bar_graph():
    """
    Creates a bar graph visualizing delayed flights for each airline.
    Saves the figure to the local filesystem after prompting the user for a filename.
    """
    results = flights_data.get_pct_delayed_flights_by_airline()
    airlines = [r[0] for r in results]
    percentages = [r[3] for r in results]

    fig = graphs.draw_pct_delay_by_airline({"airlines": airlines, "percentages": percentages})
    save_fig(fig)


def pct_delays_by_hour_bar_graph():
    """
    Creates a colorful bar graph visualizing delayed flights by hour of the day.
    Prompts the user for a filename and saves the image to the local filesystem.
    """
    results = flights_data.get_pct_delayed_flights_by_hour()
    hours = [r[0] for r in results]
    percentages = [r[3] for r in results]

    fig = graphs.draw_pct_delay_by_hour({"hours": hours, "percentages": percentages})
    save_fig(fig)


def pct_delays_by_route_heat_grid():
    """
    Creates a grid of flight routes represented by origin airport along the y-axis, and
    destination along the x-axis, with darker colors representing more delays.
    """
    results = flights_data.get_pct_delayed_flights_by_route()
    routes = [(r[0], r[1]) for r in results]
    origins = [r[0] for r in results]
    destinations = [r[1] for r in results]
    percentages = [r[4] for r in results]

    fig = graphs.draw_pct_delay_by_route_heat({
        "origins": origins,
        "destinations": destinations,
        "percentages": percentages,
    })
    save_fig(fig)


def pct_delays_by_route_map():
    """
    Creates a map of flight routes drawn over the continental USA, indicating the
    percentage of flight delays on a scale from green indicating the lowest to red
    indicating the highest.
    """
    results = flights_data.get_pct_delayed_flights_by_route()
    #  origin  dest  total del   pct               origin  lat, lon          destination lat, lon
    # ('ATL', 'AUS', 775, 117, 15.096774193548388, '33.64044', '-84.42694', '30.19453', '-97.66987')
    #  0      1      2    3    4                    5            6           7            8
    origin_codes = []

    fig = graphs.draw_pct_delay_by_route_map(None)
    save_fig(fig)


def show_menu_and_get_input():
    """
    Show the menu and get user input.
    If it's a valid option, return a pointer to the function to execute.
    Otherwise, keep asking the user for input.
    """
    print("Menu:")
    for key, value in FUNCTIONS.items():
        print(f"{key}. {value[1]}")

    # Input loop
    while True:
        try:
            choice = int(input())
            if choice in FUNCTIONS:
                return FUNCTIONS[choice][0]
        except ValueError as e:
            pass
        print("Try again...")

"""
Function Dispatch Dictionary
"""
FUNCTIONS = { 1: (flight_by_id, "Show flight by ID"),
              2: (flights_by_date, "Show flights by date"),
              3: (delayed_flights_by_airline, "Delayed flights by airline"),
              4: (delayed_flights_by_airport, "Delayed flights by origin airport"),
              5: (pct_delays_by_airline_bar_graph, "Visualize delayed flights by airline"),
              6: (pct_delays_by_hour_bar_graph, "Visualize delayed flights over 24 hours"),
              7: (pct_delays_by_route_heat_grid, "Visualize delays by route as heatmap"),
              8: (pct_delays_by_route_map, "See routes drawn over a map of the US"),
              9: (quit, "Exit"),
             }


def main():

    # The Main Menu loop
    while True:
        choice_func = show_menu_and_get_input()
        choice_func()


if __name__ == "__main__":
    main()