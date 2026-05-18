#include <iostream>
#include <string>

using namespace std;

int main() {

    string input;

    cout << "Simple Chatbot\n";
    cout << "Type 'bye' to exit\n\n";

    while (true) {

        cout << "You: ";
        getline(cin, input);

        // Exit condition
        if (input == "bye") {

            cout << "Bot: Goodbye!\n";
            break;
        }

        else if (input == "hello" ||
                 input == "hi") {

            cout << "Bot: Hello there!\n";
        }

        else if (input == "how are you") {

            cout << "Bot: I am fine. Existing digitally.\n";
        }

        else if (input == "what is your name") {

            cout << "Bot: I am a simple C++ chatbot.\n";
        }

        else if (input == "help") {

            cout << "Bot: Try saying hello, hi, or ask my name.\n";
        }

        else {

            cout << "Bot: I don't understand that.\n";
        }
    }

    return 0;
}
