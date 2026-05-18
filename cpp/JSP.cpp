#include <iostream>
#include <vector>
#include <algorithm>

using namespace std;

struct Job {
    char id;
    int deadline;
    int profit;
};

// Compare by profit descending
bool compare(Job a, Job b) {
    return a.profit > b.profit;
}

int main() {

    vector<Job> jobs = {

        {'A', 2, 100},
        {'B', 1, 19},
        {'C', 2, 27},
        {'D', 1, 25},
        {'E', 3, 15}
    };

    // Sort by maximum profit
    sort(jobs.begin(), jobs.end(), compare);

    int n = jobs.size();

    vector<int> slot(n, -1);

    int totalProfit = 0;

    cout << "Selected Jobs:\n";

    for (auto job : jobs) {

        // Find free slot before deadline
        for (int j = job.deadline - 1; j >= 0; j--) {

            if (slot[j] == -1) {

                slot[j] = job.id;

                totalProfit += job.profit;

                cout << job.id << " ";

                break;
            }
        }
    }

    cout << "\n\nMaximum Profit = "
         << totalProfit << endl;

    return 0;
}