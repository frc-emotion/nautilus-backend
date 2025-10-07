# Nautilus Backend

> [!WARNING]
> Nautilus is currently in early stage development. Features may be missing and backwards compatibility is not guaranteed in future versions.

Nautilus is a mobile native scouting and attendance solution for FIRST Robotics Competition teams. This backend is built using Python and Quart, with MongoDB as the database. Dependency management is handled by Poetry.

## Getting Started

> [!NOTE]
> Temporary section, replace later in proper documentation

Important note before we begin: Ensure you have a proper understanding of Git and its development pipeline before contributing to any repository. [This](https://www.youtube.com/watch?v=hwP7WQkmECE) is a great introductory video.

**Install these:**

Main dependencies: 
- Python 3.13
- Quart, Quart Schema, Quart Rate Limiter, Quart Mongo
- Poetry (NOT PIP)
- Visual Studio Code
- Git

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/frc-emotion/nautilus-backend.git
   cd nautilus-backend
   ```
   
You may be prompted to enter authentication details. For this, you may need to generate a Personal Access Token to use as your GitHub Password. See [here](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#creating-a-personal-access-token-classic) if you need instructions.

2. Once the repository is successfully cloned onto your machine, install all necessary dependencies by running:
   `poetry install`
   
3. Set up your environment variables in a `.env` file. Refer to `config.py` for the required variables.

### Running the Application

Start the backend server with:
`poetry run py main.py`

The server should now be running locally.

## Project Structure

- **app/**  
  Contains all the main code for the backend.

  - **controllers/**  
    Manages requests and responses for different features.
    - **attendance.py**: Routes and logic for attendance.
    - **scouting.py**: Routes and logic for scouting.

  - **schemas/**  
    Defines data structures and validation.
    - **attendance_schema.py**: Structure for attendance data.

  - **services/**  
    Contains the business logic.
    - **attendance_service.py**: Functions for managing attendance.
    - **scouting_service.py**: Functions for managing scouting.
    - **pitscouting_service.py**: Functions for managing pit scouting.

  - **config.py**  
    Stores app configuration settings.

  - **routes.py**  
    Main file for defining routes and organizing controllers.

- **tests/**  
  Folder for all test files (add your tests here).

- **.env**  
  Stores environment variables (do not share this file publicly).

- **.gitignore**  
  Lists files and folders to ignore in Git (like `.env` and `__pycache__`).

- **main.py**  
  Entry point to run the backend server.

- **poetry.lock**  
  Locks dependencies for consistent installs.

- **pyproject.toml**  
  Poetry configuration file listing project dependencies.
