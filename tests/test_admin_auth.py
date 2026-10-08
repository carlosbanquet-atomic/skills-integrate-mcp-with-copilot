import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import app


class AdminAuthTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.credentials_path = Path(self.temp_dir.name) / "teachers.json"
        self.path_patcher = patch.object(app, "TEACHER_CREDENTIALS_PATH", self.credentials_path)
        self.path_patcher.start()
        self.addCleanup(self.path_patcher.stop)
        self.addCleanup(self.temp_dir.cleanup)
        self.original_participants = {
            name: activity["participants"][:]
            for name, activity in app.activities.items()
        }
        self.addCleanup(self.restore_activities)
        app.teacher_sessions.clear()
        self.addCleanup(app.teacher_sessions.clear)

        salt = b"unit-test-salt"
        password_hash = hashlib.pbkdf2_hmac(
            "sha256", b"teacher-secret", salt, app.PASSWORD_HASH_ITERATIONS
        ).hex()
        self.credentials_path.write_text(
            json.dumps({
                "teachers": [{
                    "username": "teacher@example.edu",
                    "salt": salt.hex(),
                    "password_hash": password_hash,
                }]
            }),
            encoding="utf-8",
        )

    def restore_activities(self):
        for name, participants in self.original_participants.items():
            app.activities[name]["participants"] = participants

    def test_login_returns_a_bearer_token_for_valid_credentials(self):
        response = app.login_teacher(app.TeacherLoginRequest(
            username="teacher@example.edu",
            password="teacher-secret",
        ))

        self.assertEqual(response["token_type"], "bearer")
        self.assertEqual(
            app.require_teacher(f"Bearer {response['access_token']}"),
            "teacher@example.edu",
        )

    def test_login_rejects_invalid_credentials(self):
        with self.assertRaises(HTTPException) as error:
            app.login_teacher(app.TeacherLoginRequest(
                username="teacher@example.edu",
                password="wrong-password",
            ))

        self.assertEqual(error.exception.status_code, 401)

    def test_activities_remain_public_but_mutations_require_a_teacher(self):
        self.assertIn("Chess Club", app.get_activities())

        with self.assertRaises(HTTPException) as signup_error:
            app.signup_for_activity("Chess Club", "new-student@example.edu", None)
        self.assertEqual(signup_error.exception.status_code, 401)

        with self.assertRaises(HTTPException) as unregister_error:
            app.unregister_from_activity(
                "Chess Club", "michael@mergington.edu", None
            )
        self.assertEqual(unregister_error.exception.status_code, 401)

    def test_teacher_can_register_and_unregister_students(self):
        login = app.login_teacher(app.TeacherLoginRequest(
            username="teacher@example.edu",
            password="teacher-secret",
        ))
        authorization = f"Bearer {login['access_token']}"

        app.signup_for_activity(
            "Chess Club", "new-student@example.edu", authorization
        )
        self.assertIn(
            "new-student@example.edu", app.activities["Chess Club"]["participants"]
        )

        app.unregister_from_activity(
            "Chess Club", "new-student@example.edu", authorization
        )
        self.assertNotIn(
            "new-student@example.edu", app.activities["Chess Club"]["participants"]
        )

    def test_logout_revokes_the_session(self):
        login = app.login_teacher(app.TeacherLoginRequest(
            username="teacher@example.edu",
            password="teacher-secret",
        ))
        authorization = f"Bearer {login['access_token']}"

        app.logout_teacher(authorization)

        with self.assertRaises(HTTPException):
            app.require_teacher(authorization)


if __name__ == "__main__":
    unittest.main()