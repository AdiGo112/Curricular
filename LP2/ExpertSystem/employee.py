# =========================================================
# EXPERT SYSTEM
# Employee Performance Evaluation System
# =========================================================

# This expert system evaluates employee
# performance based on:
#
# 1. Attendance
# 2. Project Completion
# 3. Teamwork
#
# The system provides:
# - Excellent Performance
# - Good Performance
# - Average Performance
# - Poor Performance
#
# =========================================================
# HOW TO USE
# =========================================================
#
# 1. Run the program.
#
# 2. Enter employee details.
#
# 3. Provide scores out of 100 for:
#    - Attendance
#    - Project Work
#    - Teamwork
#
# 4. The system calculates average score
#    and displays performance evaluation.
#
# =========================================================


print("===================================")
print(" Employee Performance Expert System ")
print("===================================")


# Take employee name
name = input("\nEnter Employee Name: ")


# =========================================================
# TAKE PERFORMANCE SCORES
# =========================================================

attendance = int(
    input("Enter Attendance Score: ")
)

project = int(
    input("Enter Project Score: ")
)

teamwork = int(
    input("Enter Teamwork Score: ")
)


# =========================================================
# CALCULATE AVERAGE SCORE
# =========================================================

average = (
    attendance +
    project +
    teamwork
) / 3


# =========================================================
# DISPLAY PERFORMANCE RESULT
# =========================================================

print("\n===================================")

print("Employee Name:", name)

print("Average Score:", average)


# =====================================================
# PERFORMANCE EVALUATION
# =====================================================

if average >= 85:

    print("\nPerformance: Excellent")

    print(
        "Suggestion: Eligible for promotion."
    )


elif average >= 70:

    print("\nPerformance: Good")

    print(
        "Suggestion: Consistent performer."
    )


elif average >= 50:

    print("\nPerformance: Average")

    print(
        "Suggestion: Needs improvement."
    )


else:

    print("\nPerformance: Poor")

    print(
        "Suggestion: Requires training."
    )