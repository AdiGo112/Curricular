# =========================================================
# EXPERT SYSTEM
# Stock Market Trading System
# =========================================================

# This expert system provides basic
# stock market trading suggestions
# based on market conditions.
#
# Features:
# 1. Buy suggestion
# 2. Sell suggestion
# 3. Hold suggestion
#
# =========================================================
# HOW TO USE
# =========================================================
#
# 1. Run the program.
#
# 2. Enter market condition:
#    - rising
#    - falling
#    - stable
#
# 3. The system will provide
#    trading advice.
#
# 4. Type 'exit' to stop the program.
#
# =========================================================


print("===================================")
print(" Stock Market Trading Expert System ")
print("===================================")

print("\nType 'exit' to stop.\n")


# Infinite loop for continuous interaction
while True:

    # Take market condition input
    market = input(
        "Enter Market Condition: "
    ).lower()


    # =====================================================
    # EXIT CONDITION
    # =====================================================

    if market == "exit":

        print("\nExiting System...")
        break


    # =====================================================
    # RISING MARKET
    # =====================================================

    elif market == "rising":

        print("\nMarket Trend: Positive")

        print("Suggestion: BUY stocks")

        print(
            "Reason: Market prices are increasing."
        )


    # =====================================================
    # FALLING MARKET
    # =====================================================

    elif market == "falling":

        print("\nMarket Trend: Negative")

        print("Suggestion: SELL stocks")

        print(
            "Reason: Market prices are decreasing."
        )


    # =====================================================
    # STABLE MARKET
    # =====================================================

    elif market == "stable":

        print("\nMarket Trend: Neutral")

        print("Suggestion: HOLD current stocks")

        print(
            "Reason: Market movement is stable."
        )


    # =====================================================
    # INVALID INPUT
    # =====================================================

    else:

        print("\nInvalid Market Condition!")

        print(
            "Please enter: rising, falling, or stable."
        )