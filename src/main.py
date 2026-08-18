from auth import login, register
from user_actions import view_active_flights, book_flight, cancel_booking, view_my_bookings
from admin_actions import create_flight, delete_flight, delay_flight
from datetime import datetime

def print_welcome_banner():
    now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    banner = f"""
╔════════════════════════════════════════
║
║     ✈ FLIGHT OPTIMIZER PRO – Intelligent Air Travel System                          
║
╚════════════════════════════════════════

   Optimize Fuel • Minimize Time • Maximize Efficiency

   • Real-time wind-adjusted great-circle routing
   • Smart aircraft selection (150+ pax capacity)
   • Direct vs. Hub-connected path analysis
   • Live traffic awareness & congestion scoring
   • Stunning dark-mode global route visualization

   Powered by:
   → AeroDataBox API → OpenWeatherMap → MySQL → Cartopy

   ───────────────────────────────
   Login or Register to Begin
   ───────────────────────────────

   Current UTC Time: {now}
   Active Routes Plotted: 12 | Optimized Today: 47

   "Fly smarter, not harder."
"""
    print(banner)

def user_menu(user):
    while True:
        print("\n--- User Menu ---")
        print("1. View Active Flights")
        print("2. Book Flight")
        print("3. Cancel Booking")
        print("4. My Bookings")
        print("5. Logout")
        choice = input("Enter choice: ")

        if choice == "1":
            flights = view_active_flights()
            for f in flights:
                print(f)
        elif choice == "2":
            flight_id = int(input("Enter Flight ID: "))
            book_flight(user["user_id"], flight_id)
        elif choice == "3":
            booking_id = int(input("Enter Booking ID: "))
            cancel_booking(user["user_id"], booking_id)
        elif choice == "4":
            bookings = view_my_bookings(user["user_id"])
            for b in bookings:
                print(b)
        elif choice == "5":
            break

def admin_menu(user):
    while True:
        print("\n--- Admin Menu ---")
        print("1. Create Flight (Optimized)")
        print("2. Delete Flight")
        print("3. Delay Flight")
        print("4. View Active Flights")
        print("5. Logout")
        choice = input("Enter choice: ")

        if choice == "1":
            ori = input("Origin ICAO: ")
            dest = input("Destination ICAO: ")
            hubs_input = input("Hubs (comma-separated, blank if none): ")
            hubs = [h.strip().upper() for h in hubs_input.split(",")] if hubs_input else []
            dep = input("Departure Time (YYYY-MM-DD HH:MM): ")
            pax = int(input("Passengers: "))
            create_flight(ori, dest, hubs, dep, pax)
        elif choice == "2":
            fid = int(input("Flight ID: "))
            delete_flight(fid)
        elif choice == "3":
            fid = int(input("Flight ID: "))
            delay_mins = int(input("Delay in minutes: "))
            delay_flight(fid, delay_mins)
        elif choice == "4":
            flights = view_active_flights()
            if flights:
                print("\n--- Active Flights ---")
                for f in flights:
                    print(f)
            else:
                print("No active flights found.")
        elif choice == "5":
            break
        else:
            print("❌ Invalid choice. Please enter 1, 2, 3, 4, or 5.")

if __name__ == "__main__":
    print_welcome_banner()
    while True:
        print("\n=== Flight System ===")
        print("1. Login")
        print("2. Register")
        print("3. Exit")
        choice = input("Enter choice (1, 2, or 3): ")

        if choice == "1":
            print("\n=== Login ===")
            username = input("Username: ")
            password = input("Password: ")
            user = login(username, password)
            if user:
                if user["role"] == "admin":
                    admin_menu(user)
                else:
                    user_menu(user)
        elif choice == "2":
            print("\n=== Register ===")
            username = input("Username: ")
            password = input("Password: ")
            role = input("Role (user/admin, default is user): ") or "user"
            # Validate role
            if role not in ["user", "admin"]:
                print("❌ Invalid role. Please choose 'user' or 'admin'.")
                continue
            try:
                register(username, password, role)
            except Exception as e:
                print(f"❌ Error registering user: {e}")
        elif choice == "3":
            print("Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please enter 1, 2, or 3.")
