import mysql.connector as db
from datetime import datetime, timedelta
from flight_optimizer import optimize_with_connection
from auth import get_connection

def create_flight(origin, dest, hubs, departure_time, passng=150):
    """Creates and saves a flight using optimizer results."""
    best = optimize_with_connection(origin, dest, hubs, departure_time, passng)
    flights = []
    if best[0] == "direct":
        flights.append(best[1])
    else:
        leg1, leg2 = best[1], best[2]
        flights.append(leg1)
        # Calculate first leg's arrival time
        dep_time = datetime.strptime(departure_time, "%Y-%m-%d %H:%M")
        leg1_duration = leg1.get("min_time_hours", 0)
        leg1_arrival = dep_time + timedelta(hours=leg1_duration)
        # Calculate second leg's departure time (first leg's arrival + layover)
        layover_hours = 1  # Configurable layover period
        leg2_departure = leg1_arrival + timedelta(hours=layover_hours)
        flights.append(leg2)
        # Save flights with appropriate departure times
        save_flight(leg2, leg2_departure.strftime("%Y-%m-%d %H:%M"), passng)
        save_flight(leg1, departure_time, passng)
        return
    for res in flights:
        save_flight(res, departure_time, passng)

def save_flight(res, departure_time, passng):
    try:
        con = get_connection()
        cur = con.cursor()
        query = """
        INSERT INTO flights_registered
        (flight_number, airline, origin_icao, destination_icao, departure_time, arrival_time, status, aircraft_type, passengers)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        # Parse departure_time and calculate arrival_time
        dep_time = datetime.strptime(departure_time, "%Y-%m-%d %H:%M")
        flight_duration_hours = res.get("min_time_hours", 0)  # Get flight duration from optimizer
        arrival_time = dep_time + timedelta(hours=flight_duration_hours)

        values = (
            f"{res['best_airplane_fuel']}_AUTO",
            "AutoAir",
            res["origin"],
            res["dest"],
            departure_time,
            arrival_time.strftime("%Y-%m-%d %H:%M:%S"),
            "Active",
            res["best_airplane_fuel"],
            passng,
        )
        cur.execute(query, values)
        con.commit()
        con.close()
        print("✅ Flight saved into database.")
    except Exception as e:
        print(f"❌ Error saving flight: {e}")

def delete_flight(flight_id):
    try:
        con = get_connection()
        cur = con.cursor()
        cur.execute("DELETE FROM flights_registered WHERE flight_id=%s", (flight_id,))
        con.commit()
        con.close()
        print("✅ Flight deleted.")
    except Exception as e:
        print(f"❌ Error deleting flight: {e}")

def delay_flight(flight_id, delay_minutes):
    try:
        con = get_connection()
        cur = con.cursor()
        cur.execute(
            "UPDATE flights_registered SET status='Delayed', "
            "departure_time = DATE_ADD(departure_time, INTERVAL %s MINUTE), "
            "arrival_time = DATE_ADD(arrival_time, INTERVAL %s MINUTE) "
            "WHERE flight_id=%s",
            (delay_minutes, delay_minutes, flight_id),
        )
        con.commit()
        con.close()
        print("✅ Flight delayed.")
    except Exception as e:
        print(f"❌ Error delaying flight: {e}")
