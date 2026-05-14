# =========================================================
# EXPERT SYSTEM
# Information Management System
# =========================================================

# This expert system helps users manage
# and retrieve basic information.
#
# Features:
# 1. Store employee records
# 2. Search employee details
# 3. Display all records
#
# =========================================================
# HOW TO USE
# =========================================================
#
# 1. Run the program.
#
# 2. Choose options from menu:
#    1 -> Add Record
#    2 -> Search Record
#    3 -> Display All Records
#    4 -> Exit
#
# 3. Enter required information.
#
# =========================================================


# Dictionary to store employee records
records = {}


# Infinite loop for menu system
while True:

    print("\n===================================")
    print(" Information Management System ")
    print("===================================")

    print("\n1. Add Record")
    print("2. Search Record")
    print("3. Display All Records")
    print("4. Exit")

    # Take user choice
    choice = input("\nEnter your choice: ")


    # =====================================================
    # ADD RECORD
    # =====================================================

    if choice == '1':

        # Take employee details
        emp_id = input("Enter Employee ID: ")

        name = input("Enter Employee Name: ")

        department = input("Enter Department: ")

        # Store details in dictionary
        records[emp_id] = {
            "Name": name,
            "Department": department
        }

        print("\nRecord Added Successfully!")


    # =====================================================
    # SEARCH RECORD
    # =====================================================

    elif choice == '2':

        # Take employee ID
        emp_id = input("Enter Employee ID: ")

        # Check if record exists
        if emp_id in records:

            print("\nEmployee Details:")

            print(
                "Name:",
                records[emp_id]["Name"]
            )

            print(
                "Department:",
                records[emp_id]["Department"]
            )

        else:

            print("\nRecord Not Found!")


    # =====================================================
    # DISPLAY ALL RECORDS
    # =====================================================

    elif choice == '3':

        # Check if records exist
        if len(records) == 0:

            print("\nNo Records Available!")

        else:

            print("\nAll Employee Records:\n")

            # Traverse all records
            for emp_id, details in records.items():

                print("Employee ID:", emp_id)

                print("Name:", details["Name"])

                print(
                    "Department:",
                    details["Department"]
                )

                print()


    # =====================================================
    # EXIT PROGRAM
    # =====================================================

    elif choice == '4':

        print("\nExiting System...")
        break


    # =====================================================
    # INVALID INPUT
    # =====================================================

    else:

        print("\nInvalid Choice!")