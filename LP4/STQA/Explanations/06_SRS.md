# Assignment 6: Software Requirements Specification (SRS)

## Aim
Prepare a Software Requirements Specification for any project or problem statement.

## Theory and Fundamentals

### What is an SRS?
A Software Requirements Specification is a document that describes **what** the software must do (functions) and **how well** it must do it (quality), without describing how it is built. It is the agreement between the client, developers and testers.

### Why testers need the SRS
- Test cases are derived from requirements. If a requirement is vague, it cannot be tested.
- **Traceability**: every requirement should map to at least one test case, so nothing is left untested.
- Testers also review the SRS itself (static testing) to find missing or unclear requirements early. Defects found here are the cheapest to fix.

### IEEE 830
IEEE Std 830-1998 is a recommended practice for writing an SRS. The standard layout is:

1. **Introduction**: purpose, scope, definitions, references, overview
2. **Overall description**: product perspective, functions, user classes, operating environment, constraints, assumptions
3. **Specific requirements**: functional, external interface, non-functional
4. Appendices / traceability

### Characteristics of a good requirement
| Quality | Meaning |
| --- | --- |
| Correct | States a real need |
| Unambiguous | One meaning only |
| Complete | Nothing missing |
| Consistent | Does not contradict another |
| Verifiable / testable | A test can prove it is met (for example "within 2 seconds", not "fast") |
| Traceable | Has an ID (FR1.2) |
| Prioritised | High, Medium, Low |

Use "shall" for mandatory requirements.

### Functional vs non-functional requirements
- **Functional (FR)**: what the system does (register, login, add task).
- **Non-functional (NFR)**: quality attributes such as performance, security, usability, reliability, portability, maintainability.

### Use case
A description of how an **actor** interacts with the system to reach a goal: actor, pre-condition, main flow, alternate flow, post-condition.

### Requirement traceability matrix (RTM)
A table linking each requirement to its test cases. It shows coverage and the impact of a change.

## How the Code / Document Works

`6_SRS_TaskTrack.md` is the SRS for **TaskTrack**, a web-based personal task manager (the application of Assignment 9). It is written in IEEE 830 format, version 1.0, dated 03-11-2026.

### Section 1: Introduction
- **Purpose**: for developers, testers and evaluators, and the basis of the test plan in `9_MiniProject_TestIntegration/test_plan.md`.
- **Scope**: users register, log in and manage a personal to-do list (add, complete, delete). Collaboration, reminders and mobile apps are **out of scope**.
- A definitions table (SRS, User, Task, Session, FR/NFR), references (IEEE 830, Flask docs) and an overview of the document.

### Section 2: Overall description
- **Perspective**: a self-contained web app, drawn as `Browser (HTML forms) <-HTTP-> Flask server (routes + validation) <-> In-memory data store`.
- **Product functions**: register, login/logout, add task, mark done, delete task, view list with count.
- **User classes**: Guest (only Login and Register pages) and Registered User (only their own tasks).
- **Environment**: server with Python 3.10+ and Flask; client Chrome, Edge or Firefox.
- **Constraints**: Python with Flask, data kept in memory and lost on restart, must work without JavaScript.
- **Assumptions**: users have a browser and network access, Flask is installed.

### Section 3: Specific requirements
**3.1 Functional requirements** are numbered and prioritised.

| Group | IDs | Examples |
| --- | --- | --- |
| FR1 Registration | FR1.1 to FR1.6 | username 3 to 15 characters of letters, digits or `_`; password at least 6 characters with a digit; passwords match; username unique ignoring case |
| FR2 Login/Logout | FR2.1 to FR2.5 | blank fields show "Enter username and password"; wrong credentials show "Invalid username or password" without saying which field is wrong; Tasks page only for logged-in users |
| FR3 Tasks | FR3.1 to FR3.6 | title 1 to 50 characters (trimmed); blank shows "Task title cannot be empty"; done tasks struck through; user sees only own tasks |

Sample requirement text:

```
| FR1.3 | Password shall be at least 6 characters long and contain at least one digit. | High |
```

**3.2 External interfaces**: simple HTML pages with errors in red and success in green, no hardware interface, Python/Flask/browser software interface, HTTP communication.

**3.3 Non-functional requirements** NFR1 to NFR7:

| ID | Category | Requirement (short) |
| --- | --- | --- |
| NFR1 | Performance | each page loads within 2 seconds on a local network |
| NFR2 | Security | masked password fields; user input HTML-escaped to prevent XSS |
| NFR3 | Security | server-side session protects pages |
| NFR4 | Usability | new user registers and adds a task within 2 minutes |
| NFR5 | Reliability | invalid URLs or task numbers do not crash the server |
| NFR6 | Portability | Chrome, Edge, Firefox on Windows, Linux, Android |
| NFR7 | Maintainability | validation in separate functions so it can be unit tested |

**3.4 Use case "Add Task"**: actor Registered User, pre-condition logged in. Main flow: type title, click Add, system validates, system adds and shows the list. Alternate flow 3a: blank or longer than 50 characters shows an error and the list is unchanged. Post-condition: task count increases by 1.

### Section 4: Requirement traceability
A table from requirements to test cases TC02 to TC17 in the Assignment 9 test plan, for example FR1.2 to TC02, TC03, TC04; FR1.3 to TC05; FR2.4 and FR2.5 to TC16 and TC17; NFR5 to TC15.

This links the documents: SRS requirement -> test plan test case -> automated test (`test_unit_integration.py` and `test_selenium_regression.py`).

### How the SRS matches the code
The validation rules in the SRS appear in `app.py`, for example FR1.2 is `re.fullmatch(r"[A-Za-z0-9_]{3,15}", username)`, and FR3.1 is `len(title) > 50` after `strip()`. The SRS (NFR7) asks for separate validation functions, and `app.py` has `validate_username`, `validate_password` and `validate_task`.

## How to Run and Expected Output

Nothing to run. Open the Markdown file. To use it:

1. Read the requirements and write test cases for each ID (see `9_MiniProject_TestIntegration/test_plan.md`).
2. Check the Section 4 table to confirm each requirement has at least one test.
3. Run the TaskTrack tests:
   ```bash
   cd 9_MiniProject_TestIntegration
   python test_unit_integration.py
   ```
   Expected result: 19 tests, all PASS, verdict ACCEPTED.

To write your own SRS use the same skeleton: Introduction, Overall Description, Specific Requirements (FR and NFR), Use cases, Traceability.

## Related Concepts and Real-World Tools

- **Requirement management tools**: JIRA, Azure DevOps, IBM DOORS, Confluence.
- **Agile alternatives**: user stories ("As a user I want ... so that ...") with acceptance criteria, product backlog.
- **BDD**: acceptance criteria in Given / When / Then format (Cucumber, behave).
- **UML diagrams**: use case, activity and sequence diagrams for modelling. Tools: draw.io, Lucidchart, PlantUML.
- **Standards**: IEEE 830 was replaced by **ISO/IEC/IEEE 29148**, but 830 is still taught.
- **Reviews and inspections**: peer review and walkthrough of the SRS (static testing).
- **MoSCoW** (Must, Should, Could, Won't) is a popular way to set priority.

## Viva Questions

1. **What is an SRS and who uses it?**
   A document that states the functional and non-functional requirements of the software. Clients, developers, testers and managers use it.

2. **Which standard did you follow?**
   IEEE Std 830-1998. It gives Introduction, Overall Description and Specific Requirements sections.

3. **Difference between functional and non-functional requirements?**
   Functional says what the system does (login). Non-functional says how well (loads within 2 seconds, secure, portable).

4. **What makes a requirement testable?**
   It is specific and measurable. "Each page shall load within 2 seconds" is testable. "The system shall be fast" is not.

5. **What is the use of a traceability matrix?**
   It maps each requirement to its test cases, so we can confirm full coverage and see which tests to repeat when a requirement changes.

6. **What is out of scope in your SRS and why state it?**
   Online collaboration, reminders and mobile apps. Stating it avoids misunderstanding and keeps the project limited.

7. **Why does FR2.3 say "without saying which field is wrong"?**
   It is a security measure. A message like "wrong password" tells an attacker that the username exists.

8. **What is a use case? Name its parts.**
   A story of an actor reaching a goal with the system: actor, pre-condition, main flow, alternate flow, post-condition.

9. **What are the user classes in TaskTrack?**
   Guest (can only see Login and Register) and Registered User (manages only their own tasks).

10. **Why should testers read the SRS before coding is finished?**
    They can find unclear or missing requirements early (static testing), which is cheaper than finding defects later, and can start writing test cases at once.
