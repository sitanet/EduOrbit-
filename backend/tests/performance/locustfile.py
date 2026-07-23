from locust import HttpUser, task, between

class EduOrbitLoadTestUser(HttpUser):
    # Simulate user wait time between 1 and 3 seconds
    wait_time = between(1, 3)

    def on_start(self):
        """
        Executed when a simulated user starts.
        Handles authentication to obtain JWT tokens.
        """
        # Uncomment and adjust based on actual auth endpoint
        # response = self.client.post("/api/auth/token/", json={"username": "testuser", "password": "password123"})
        # self.token = response.json().get("access")
        self.token = "dummy_token"

    def get_headers(self):
        return {"Authorization": f"Bearer {self.token}"}

    @task(3)
    def load_dashboard(self):
        """
        Simulates loading the main dashboard, which typically requires data aggregation.
        """
        # self.client.get("/api/dashboard/", headers=self.get_headers())
        pass

    @task(1)
    def bulk_attendance_submission(self):
        """
        Simulates a heavy write operation: bulk attendance.
        """
        payload = {
            "date": "2026-07-19",
            "class_id": 101,
            "attendance": [
                {"student_id": i, "status": "present"} for i in range(1, 31)
            ]
        }
        # self.client.post("/api/attendance/bulk/", json=payload, headers=self.get_headers())
        pass

    @task(2)
    def view_student_roster(self):
        """
        Simulates querying paginated student data.
        """
        # self.client.get("/api/students/?page=1&limit=50", headers=self.get_headers())
        pass
