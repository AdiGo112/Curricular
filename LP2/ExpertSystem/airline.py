# =========================================================
# EXPERT SYSTEM
# Airline Scheduling and Cargo Management System
# =========================================================

# This expert system helps manage:
#
# 1. Passenger flight schedules
# 2. Cargo shipment schedules
#
# The system provides flight and cargo
# information based on user choice.
#
# =========================================================
# HOW TO USE
# =========================================================
#
# 1. Run the program.
#
# 2. Choose:
#    1 -> Flight Schedule
#    2 -> Cargo Schedule
#    3 -> Exit
#
# 3. Enter required details.
#
# =========================================================


# =========================================================
# FLIGHT SCHEDULE DATA
# =========================================================

flight_schedule = {

    "AI101": {
        "Destination": "Delhi",
        "Time": "10:00 AM"
    },

    "AI202": {
        "Destination": "Mumbai",
        "Time": "1:30 PM"
    },

    "AI303": {
        "Destination": "Bangalore",
        "Time": "6:45 PM"
    }
}


# =========================================================
# CARGO SCHEDULE DATA
# =========================================================

cargo_schedule = {

    "CG101": {
        "Cargo": "Electronics",
        "Departure": "9:00 AM"
    },

    "CG202": {
        "Cargo": "Medical Supplies",
        "Departure": "2:15 PM"
    },

    "CG303": {
        "Cargo": "Food Products",
        "Departure": "7:00 PM"
    }
}


# =========================================================
# MAIN MENU LOOP
# =========================================================

while True:

    print("\n===================================")
    print(" Airline Scheduling Expert System ")
    print("===================================")

    print("\n1. View Flight Schedule")

    print("2. View Cargo Schedule")

    print("3. Exit")


    # Take user choice
    choice = input("\nEnter your choice: ")


    # =====================================================
    # VIEW FLIGHT SCHEDULE
    # =====================================================

    if choice == '1':

        # Take flight number
        flight_no = input(
            "\nEnter Flight Number: "
        ).upper()

        # Check if flight exists
        if flight_no in flight_schedule:

            print("\nFlight Details:\n")

            print("Flight Number:", flight_no)

            print(
                "Destination:",
                flight_schedule[flight_no]
                ["Destination"]
            )

            print(
                "Departure Time:",
                flight_schedule[flight_no]
                ["Time"]
            )

        else:

            print("\nFlight Not Found!")


    # =====================================================
    # VIEW CARGO SCHEDULE
    # =====================================================

    elif choice == '2':

        # Take cargo ID
        cargo_id = input(
            "\nEnter Cargo ID: "
        ).upper()

        # Check if cargo exists
        if cargo_id in cargo_schedule:

            print("\nCargo Details:\n")

            print("Cargo ID:", cargo_id)

            print(
                "Cargo Type:",
                cargo_schedule[cargo_id]
                ["Cargo"]
            )

            print(
                "Departure Time:",
                cargo_schedule[cargo_id]
                ["Departure"]
            )

        else:

            print("\nCargo Schedule Not Found!")


    # =====================================================
    # EXIT SYSTEM
    # =====================================================

    elif choice == '3':

        print("\nExiting System...")
        break


    # =====================================================
    # INVALID INPUT
    # =====================================================

    else:

        print("\nInvalid Choice!")