# =========================================================
# EXPERT SYSTEM
# Hospital and Medical Facilities
# =========================================================

# This expert system provides basic medical advice
# based on symptoms entered by the user.
#
# The system suggests:
# 1. Possible illness
# 2. Recommended action
#
# =========================================================
# HOW TO USE
# =========================================================
#
# 1. Run the program.
#
# 2. Enter symptoms like:
#    - fever
#    - cough
#    - headache
#    - stomach pain
#
# 3. The expert system will suggest
#    a possible condition.
#
# 4. Type 'exit' to stop the program.
#
# =========================================================


print("===================================")
print(" Hospital Expert System ")
print("===================================")

print("\nType 'exit' to stop.\n")


# Infinite loop for continuous interaction
while True:

    # Take symptom input from user
    symptom = input(
        "Enter your symptom: "
    ).lower()


    # =====================================================
    # EXIT CONDITION
    # =====================================================

    if symptom == "exit":

        print("\nSystem Closed.")
        break


    # =====================================================
    # FEVER RELATED CONDITION
    # =====================================================

    elif "fever" in symptom:

        print("\nPossible Condition: Viral Infection")

        print(
            "Advice: Drink fluids and "
            "consult a doctor if fever continues."
        )


    # =====================================================
    # COUGH RELATED CONDITION
    # =====================================================

    elif "cough" in symptom:

        print("\nPossible Condition: Cold or Flu")

        print(
            "Advice: Take rest and "
            "drink warm liquids."
        )


    # =====================================================
    # HEADACHE RELATED CONDITION
    # =====================================================

    elif "headache" in symptom:

        print("\nPossible Condition: Stress or Migraine")

        print(
            "Advice: Rest properly and "
            "avoid screen exposure."
        )


    # =====================================================
    # STOMACH PAIN RELATED CONDITION
    # =====================================================

    elif "stomach" in symptom:

        print("\nPossible Condition: Gastric Problem")

        print(
            "Advice: Avoid oily food and "
            "drink enough water."
        )


    # =====================================================
    # CHEST PAIN RELATED CONDITION
    # =====================================================

    elif "chest pain" in symptom:

        print("\nPossible Condition: Serious Issue")

        print(
            "Advice: Consult a doctor immediately."
        )


    # =====================================================
    # DEFAULT RESPONSE
    # =====================================================

    else:

        print(
            "\nSystem could not identify "
            "the condition."
        )

        print(
            "Advice: Please consult a doctor."
        )