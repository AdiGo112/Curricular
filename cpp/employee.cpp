#include <iostream>
#include <string>

using namespace std;

int main() {

    cout << "===================================\n";
    cout << " Employee Performance Expert System \n";
    cout << "===================================\n";

    string name;

    int attendance;
    int project;
    int teamwork;

    // Employee Name
    cout << "\nEnter Employee Name: ";
    getline(cin, name);

    // Input Scores
    cout << "Enter Attendance Score: ";
    cin >> attendance;

    cout << "Enter Project Score: ";
    cin >> project;

    cout << "Enter Teamwork Score: ";
    cin >> teamwork;

    // Calculate Average
    double average =
        (attendance + project + teamwork) / 3.0;

    // Display Result
    cout << "\n===================================\n";

    cout << "Employee Name: "
         << name << endl;

    cout << "Average Score: "
         << average << endl;

    // Performance Evaluation
    if (average >= 85) {

        cout << "\nPerformance: Excellent\n";

        cout << "Suggestion: Eligible for promotion.\n";
    }

    else if (average >= 70) {

        cout << "\nPerformance: Good\n";

        cout << "Suggestion: Consistent performer.\n";
    }

    else if (average >= 50) {

        cout << "\nPerformance: Average\n";

        cout << "Suggestion: Needs improvement.\n";
    }

    else {

        cout << "\nPerformance: Poor\n";

        cout << "Suggestion: Requires training.\n";
    }

    return 0;
}
