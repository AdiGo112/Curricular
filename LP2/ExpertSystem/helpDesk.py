# =========================================================
# EXPERT SYSTEM
# Help Desk Management System
# =========================================================

# This expert system helps users solve
# common technical support problems.
#
# Features:
# 1. Internet issue support
# 2. Login issue support
# 3. Printer issue support
# 4. Software issue support
#
# =========================================================
# HOW TO USE
# =========================================================
#
# 1. Run the program.
#
# 2. Select an issue from menu.
#
# 3. The system will provide
#    troubleshooting suggestions.
#
# 4. Type 5 to exit.
#
# =========================================================


# Infinite loop for menu system
while True:

    print("\n===================================")
    print(" Help Desk Management System ")
    print("===================================")

    print("\n1. Internet Problem")
    print("2. Login Problem")
    print("3. Printer Problem")
    print("4. Software Installation Problem")
    print("5. Exit")

    # Take user choice
    choice = input("\nEnter your choice: ")


    # =====================================================
    # INTERNET RELATED ISSUES
    # =====================================================

    if choice == '1':

        print("\nPossible Solutions:")

        print("1. Check Wi-Fi connection")

        print("2. Restart the router")

        print("3. Check network cables")

        print("4. Contact Internet Provider if issue continues")


    # =====================================================
    # LOGIN RELATED ISSUES
    # =====================================================

    elif choice == '2':

        print("\nPossible Solutions:")

        print("1. Check username and password")

        print("2. Reset password")

        print("3. Ensure CAPS LOCK is OFF")

        print("4. Contact administrator if account is locked")


    # =====================================================
    # PRINTER RELATED ISSUES
    # =====================================================

    elif choice == '3':

        print("\nPossible Solutions:")

        print("1. Check printer power")

        print("2. Ensure printer is connected")

        print("3. Check paper availability")

        print("4. Reinstall printer drivers")


    # =====================================================
    # SOFTWARE INSTALLATION ISSUES
    # =====================================================

    elif choice == '4':

        print("\nPossible Solutions:")

        print("1. Check system requirements")

        print("2. Run installer as administrator")

        print("3. Disable antivirus temporarily")

        print("4. Restart system and try again")


    # =====================================================
    # EXIT SYSTEM
    # =====================================================

    elif choice == '5':

        print("\nExiting Help Desk System...")
        break


    # =====================================================
    # INVALID INPUT
    # =====================================================

    else:

        print("\nInvalid Choice!")