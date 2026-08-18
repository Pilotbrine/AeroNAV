import mysql.connector as db
from flight_optimizer import plot_route

def get_connection():
    return db.connect(host="localhost", user="root", passwd="mysql", database="flights")

def view_active_flights():
    con = get_connection()
    cur = con.cursor(dictionary=True)
    cur.execute("SELECT * FROM flights_registered WHERE status='Active'")
    flights = cur.fetchall()
    con.close()

    if not flights:
        print("No active flights found.")
        return []

    # Display all active flights for selection
    print("\n--- Active Flights ---")
    for f in flights:
        print(f"Flight ID: {f['flight_id']}, Flight Number: {f['flight_number']}, "
              f"Origin: {f['origin_icao']}, Destination: {f['destination_icao']}, "
              f"Departure: {f['departure_time']}, Status: {f['status']}")

    # Prompt user to select flights by flight_id
    selected_ids = input("\nEnter Flight IDs to view (comma-separated, or 'all' for all flights): ").strip()
    
    if selected_ids.lower() == 'all':
        selected_flights = flights
    else:
        try:
            selected_ids = [int(fid.strip()) for fid in selected_ids.split(",") if fid.strip()]
            selected_flights = [f for f in flights if f['flight_id'] in selected_ids]
            if not selected_flights:
                print("❌ No valid flights selected or invalid Flight IDs provided.")
                return []
        except ValueError:
            print("❌ Invalid input. Please enter valid Flight IDs or 'all'.")
            return []

    # Prepare routes with flight metadata for selected flights
    routes = []
    from flight_optimizer import get_airport_coords
    for f in selected_flights:
        try:
            lat1, lon1 = get_airport_coords(f["origin_icao"])
            lat2, lon2 = get_airport_coords(f["destination_icao"])
            routes.append({
                "coords": ((lat1, lon1), (lat2, lon2)),
                "origin_icao": f["origin_icao"],
                "destination_icao": f["destination_icao"],
                "flight_number": f["flight_number"]
            })
        except Exception as e:
            print(f"❌ Error fetching coordinates for flight {f['flight_number']}: {e}")

    if routes:
        plot_route(routes)
    else:
        print("No routes to display.")

    return selected_flights

def book_flight(user_id, flight_id):
    con = get_connection()
    cur = con.cursor()
    cur.execute("INSERT INTO flight_bookings (user_id, flight_id) VALUES (%s, %s)", (user_id, flight_id))
    con.commit()
    con.close()
    print("✈️ Flight booked successfully!")

def cancel_booking(user_id, booking_id):
    con = get_connection()
    cur = con.cursor()
    cur.execute("DELETE FROM flight_bookings WHERE booking_id=%s AND user_id=%s", (booking_id, user_id))
    con.commit()
    con.close()
    print("🛑 Booking cancelled.")

def view_my_bookings(user_id):
    con = get_connection()
    cur = con.cursor(dictionary=True)
    cur.execute("""
        SELECT b.booking_id, f.flight_number, f.origin_icao, f.destination_icao, f.status
        FROM flight_bookings b
        JOIN flights_registered f ON b.flight_id = f.flight_id
        WHERE b.user_id=%s
    """, (user_id,))
    bookings = cur.fetchall()
    con.close()
    return bookings