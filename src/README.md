# Mergington High School Activities API

A super simple FastAPI application that allows students to view and sign up for extracurricular activities.

## Features

- View all available extracurricular activities
- Teachers can sign up or unregister students after logging in
- Students can view activities and participant rosters without an account

## Teacher accounts

Teacher credentials are assigned outside the application and stored in `src/teachers.json`. Passwords must be PBKDF2-HMAC-SHA256 hashes; do not store plaintext passwords or commit real teacher passwords.

Generate the salt and password hash for a teacher with:

```sh
python3 -c 'import getpass, hashlib, json, secrets; p=getpass.getpass("Password: "); s=secrets.token_bytes(16); print(json.dumps({"username":"teacher@mergington.edu","salt":s.hex(),"password_hash":hashlib.pbkdf2_hmac("sha256",p.encode(),s,600000).hex()}))'
```

Add the printed object to the `teachers` array in `src/teachers.json`. Teacher sessions expire after eight hours and are cleared when the server restarts.

## Getting Started

1. Install the dependencies:

   ```
   pip install fastapi uvicorn
   ```

2. Run the application:

   ```
   python app.py
   ```

3. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## API Endpoints

| Method | Endpoint                                                          | Description                                                         |
| ------ | ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| GET    | `/activities`                                                     | Get all activities with their details and current participant count |
| POST   | `/auth/login`                                                      | Create a teacher session                                            |
| POST   | `/auth/logout`                                                     | Revoke a teacher session                                            |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu` | Teacher signs up a student for an activity                          |
| DELETE | `/activities/{activity_name}/unregister?email=student@mergington.edu` | Teacher removes a student from an activity                       |

## Data Model

The application uses a simple data model with meaningful identifiers:

1. **Activities** - Uses activity name as identifier:

   - Description
   - Schedule
   - Maximum number of participants allowed
   - List of student emails who are signed up

2. **Students** - Uses email as identifier:
   - Name
   - Grade level

All data is stored in memory, which means data will be reset when the server restarts.
