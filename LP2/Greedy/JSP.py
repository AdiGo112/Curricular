# JOB SCHEDULING PROBLEM USING GREEDY METHOD

# Each job has:
# (Job ID, Deadline, Profit)
jobs = [
    ('J1', 2, 100),
    ('J2', 1, 50),
    ('J3', 2, 10),
    ('J4', 1, 20),
    ('J5', 3, 30)
]

# JOB SCHEDULING FUNCTION
def job_scheduling(jobs):

    # Sort jobs in descending order of profit
    jobs.sort(key=lambda x: x[2], reverse=True)

    # Find maximum deadline
    max_deadline = max(job[1] for job in jobs)

    # Create slots for scheduling jobs
    slots = [None] * max_deadline

    # Store total profit
    total_profit = 0

    print("Selected Jobs:\n")

    # Traverse all jobs
    for job_id, deadline, profit in jobs:

        # Check slots from deadline-1 to 0
        for i in range(deadline - 1, -1, -1):

            # If slot is empty
            if slots[i] is None:

                # Assign job to slot
                slots[i] = job_id

                # Add profit
                total_profit += profit

                break

    # Print scheduled jobs
    for i in range(max_deadline):

        if slots[i]:

            print(
                "Time Slot",
                i + 1,
                ":",
                slots[i]
            )

    # Print total profit
    print("\nTotal Profit:", total_profit)


# DRIVER CODE
job_scheduling(jobs)

# time complexity: O(n log n) due to sorting
# space complexity: O(d) where d is the maximum deadline