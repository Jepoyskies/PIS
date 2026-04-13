# XJHS Prefect & Registrar Information System (XJHS-PIS)

This project is a modern web application built to replace the legacy Windows XP and MS Access-based system used by the Xavier University - Ateneo de Cagayan Junior High School's Prefect of Students Office. 

This "clean-room" reconstruction was developed using Python, Django, and MySQL. The system unifies the formerly separate **Prefect Information System (PIS)** and **Registrar Information System (RIS)** into a single, cohesive application.

## Core Features

*   **Unified System:** Combines RIS (Enrolment, Sections, Subjects, Teachers) and PIS (Discipline, Conduct, Absences) into one database.
*   **Legacy UI/UX Replication:** The interface is designed to be a 1-to-1 visual and functional match of the original 2002 software, built with modern HTML5 and Bootstrap 5.
*   **Strictly Offline & Local:** The system is hardcoded to run on `127.0.0.1`, ensuring student data privacy by preventing any network or internet access.
*   **Database Migration:** Includes a robust Excel (`.xlsx`) import tool to allow for a "clean slate" data migration from legacy student lists.
*   **Relational Data Management:** Full CRUD (Create, Read, Update, Delete) functionality for managing students, teachers, sections, subjects, and their relationships.

## Tech Stack

*   **Backend:** Python 3.10+, Django
-   **Language:** Python 3.12 (Required)
*   **Database:** MySQL 8.0
*   **Frontend:** HTML5, CSS3, Bootstrap 5, Vanilla JavaScript

---

## Getting Started

Follow these instructions to set up and run the project on your local machine for development and testing purposes.

### Prerequisites

You must have the following software installed on your machine:
*   [Python 3.12](https://www.python.org/downloads/release/python-3120/) (Do NOT use 3.14+ as it lacks library support)
*   [Git](https://git-scm.com/downloads/)
*   [XAMPP](https://www.apachefriends.org/index.html) (or another local MySQL server environment)

### Installation

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/your-username/your-repo-name.git
    cd your-repo-name
    ```

2.  **Create and Activate a Virtual Environment**
    ```bash
    # Create the virtual environment folder
    python -m venv venv

    # Activate it (for Windows)
    venv\Scripts\activate
    ```

3.  **Install Project Dependencies**
    This command reads the `requirements.txt` file and installs Django, PyWebView, Pandas, etc.
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set Up the Local MySQL Database**
    > **Important:** This application requires a local MySQL database to run.

    a. Open your XAMPP Control Panel and start the **MySQL** module.
    b. Open your web browser and navigate to `http://localhost/phpmyadmin/`.
    c. Create a new, empty database with the exact name: `xjhs_pis_db`

5.  **Configure Database Connection**
    a. Open the `xjhs_pis/settings.py` file.
    b. Scroll down to the `DATABASES` section.
    c. **Update the `PASSWORD` field** to match your local MySQL root password (for default XAMPP, this is usually blank: `''`).

6.  **Build the Database Tables**
    These commands will push the application's data structure into your new MySQL database.
    ```bash
    python manage.py makemigrations
    python manage.py migrate
    ```

7.  **Create Your Admin Account**
    This account is needed to get past the login screen.
    ```bash
    python manage.py createsuperuser
    ```
    Follow the prompts to create your username and password.

---

## Running the Application

You can run the system in two ways:

#### 1. Running the Local Server
This command starts the Django development server for local access.

---
## Running with Docker

Utilizing Docker ensures environment parity and simplifies the setup of the MySQL database and Python dependencies.

1.  **Build and Start the Containers**  
    This command builds the Django image and starts both the web and database services.
    ```bash
    docker-compose up --build
    ```

2.  **Create Your Admin Account**  
    Once the containers are running, execute this command in a separate terminal to create your login:
    ```bash
    docker-compose exec web python manage.py createsuperuser
    ```

3.  **Access the System**  
    Open your browser and navigate to `http://localhost:8000`.
```bash
python desktop.py