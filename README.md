Steps to Run the application (on Windows OS)
    1. Create a virtual environment in root folder(where app.py file is present). (python -m venv env_name)
    2. Activate the virtual environment. (env_name\Scripts\activate)
    3. Install all dependencies from requirements.txt file. (pip install -r requirements.txt)
    Note: Step 4,5&6 are not required for this project the database has already been created for this project.
    4. Open python shell. (python)
    5. Run below two commands in sequence to create the database.
        from app import *
        db.create_all()
    6. Exit the python shell. (exit())
    7. Run the application. (python app.py)