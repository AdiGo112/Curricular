# Assignment 6: Software Requirements Specification (SRS)
## TaskTrack: Web-based Personal Task Manager

*Format: IEEE Std 830-1998. Version 1.0, 03-11-2026.*

---

## 1. Introduction

### 1.1 Purpose
This document describes the functional and non-functional requirements of **TaskTrack**. It is meant for developers, testers and evaluators, and it is the basis for the test plan in `9_MiniProject_TestIntegration/test_plan.md`.

### 1.2 Scope
TaskTrack is a small web application. Users register, log in, and manage a personal to-do list (add, complete and delete tasks). It runs in any modern browser. Online collaboration, reminders and mobile apps are out of scope.

### 1.3 Definitions, Acronyms and Abbreviations

| Term | Meaning |
| --- | --- |
| SRS | Software Requirements Specification |
| User | A person with a registered account |
| Task | A to-do item with a title and a status (pending / done) |
| Session | Period between login and logout |
| FR / NFR | Functional / Non-Functional Requirement |

### 1.4 References
- IEEE Std 830-1998, Recommended Practice for SRS
- Flask documentation, https://flask.palletsprojects.com

### 1.5 Overview
Section 2 describes the product in general. Section 3 lists the detailed requirements.

---

## 2. Overall Description

### 2.1 Product Perspective
TaskTrack is a new, self-contained web application with a browser front-end and a Python Flask back-end.

```
 Browser (HTML forms) <──HTTP──> Flask server (routes + validation) <──> In-memory data store
```

### 2.2 Product Functions
- User registration
- User login and logout
- Add a task
- Mark a task as done
- Delete a task
- View the task list with a count

### 2.3 User Classes and Characteristics

| User Class | Description |
| --- | --- |
| Guest | Can only view the Login and Register pages |
| Registered User | Can manage only their own tasks |

### 2.4 Operating Environment
- **Server:** any OS with Python 3.10+ and Flask
- **Client:** Chrome, Edge or Firefox (latest versions), on desktop or mobile

### 2.5 Design and Implementation Constraints
- Written in Python using the Flask framework
- Data is stored in memory and lost when the server restarts (lab version)
- Must work without JavaScript

### 2.6 Assumptions and Dependencies
- Users have a browser and network access to the server
- Flask is installed on the server

---

## 3. Specific Requirements

### 3.1 Functional Requirements

| ID | Requirement | Priority |
| --- | --- | --- |
| **FR1** | **Registration** | |
| FR1.1 | The system shall let a guest register with a username, password and confirm password. | High |
| FR1.2 | Username shall be 3–15 characters long and contain only letters, digits or `_`. | High |
| FR1.3 | Password shall be at least 6 characters long and contain at least one digit. | High |
| FR1.4 | Password and confirm password shall match. | High |
| FR1.5 | Username shall be unique, ignoring upper/lower case. | High |
| FR1.6 | On success the system shall show "Registration successful, please login". | Medium |
| **FR2** | **Login / Logout** | |
| FR2.1 | The system shall let a registered user log in with their username and password. | High |
| FR2.2 | Blank fields shall show "Enter username and password". | Medium |
| FR2.3 | Wrong credentials shall show "Invalid username or password" without saying which field is wrong. | High |
| FR2.4 | Logout shall end the session and redirect to the Login page. | High |
| FR2.5 | The Tasks page shall be accessible only to logged-in users. | High |
| **FR3** | **Task Management** | |
| FR3.1 | A user shall be able to add a task with a title of 1–50 characters. Leading/trailing spaces are removed. | High |
| FR3.2 | A blank title shall show "Task title cannot be empty". | Medium |
| FR3.3 | A user shall be able to mark a task as done; done tasks appear struck through. | Medium |
| FR3.4 | A user shall be able to delete a task. | Medium |
| FR3.5 | The page shall show the number of tasks. | Low |
| FR3.6 | A user shall see only their own tasks. | High |

### 3.2 External Interface Requirements
- **User Interface:** simple HTML pages (Login, Register, My Tasks). Errors are shown in red and success messages in green.
- **Hardware Interface:** none.
- **Software Interface:** Python 3, Flask, a web browser.
- **Communication Interface:** HTTP (HTTPS in production).

### 3.3 Non-Functional Requirements

| ID | Category | Requirement |
| --- | --- | --- |
| NFR1 | Performance | Each page shall load within 2 seconds on a local network. |
| NFR2 | Security | Password fields shall be masked; user input shall be HTML-escaped to prevent XSS. |
| NFR3 | Security | Pages shall be protected by a server-side session. |
| NFR4 | Usability | A new user shall be able to register and add a task within 2 minutes without help. |
| NFR5 | Reliability | Invalid URLs or task numbers shall not crash the server. |
| NFR6 | Portability | Shall work on Chrome, Edge and Firefox on Windows, Linux and Android. |
| NFR7 | Maintainability | Validation rules shall be in separate functions so they can be unit tested. |

### 3.4 Use Case: Add Task

| Item | Description |
| --- | --- |
| Actor | Registered User |
| Pre-condition | User is logged in |
| Main Flow | 1. User types a title. 2. User clicks Add. 3. System validates the title. 4. System adds the task and shows the updated list. |
| Alternate Flow | 3a. Title is blank or longer than 50 characters: the system shows an error and the list stays unchanged. |
| Post-condition | Task count increases by 1 |

---

## 4. Requirement Traceability (Requirement → Test)

| Requirement | Tests (RT = Selenium WebDriver, IDE = Selenium IDE, ET = exploratory, in `9_MiniProject_TestIntegration/test_plan.md`) |
| --- | --- |
| FR1.2 | RT-02; ET-01 (v1.1) |
| FR1.3 | RT-03, IDE-3 |
| FR1.4 | not covered by a script (gap) |
| FR1.5 | ET-02 (v1.1) |
| FR2.2, FR2.3 | RT-04, IDE-2 |
| FR2.1 | RT-05, IDE-1 |
| FR3.1, FR3.2 | RT-06, RT-07, RT-12 |
| FR3.3, FR3.4 | RT-08, RT-09, IDE-4 |
| FR2.4, FR2.5 | RT-10, IDE-1 |
| NFR5 | RT-11, IDE-4 |
