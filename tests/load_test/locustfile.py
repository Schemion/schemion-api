from locust import HttpUser, task, between
import queue

USERS_DATA = [
    {"email": f"loadtest_user_{i}@example.com", "password": "123456"}
    for i in range(100)
]

user_queue = queue.Queue()
for u in USERS_DATA:
    user_queue.put(u)


class APIUser(HttpUser):
    wait_time = between(0.5, 2.0)
    token = None

    def on_start(self):
        try:
            creds = user_queue.get(block=False)
            self.email = creds["email"]
            self.password = creds["password"]

            response = self.client.post("/auth/login", data={
                "username": self.email,
                "password": self.password
            })

            if response.status_code == 200:
                self.token = response.json()["access_token"]
            else:
                print(f"Login failed: {self.email}: {response.text}")
                self.stop()
        except queue.Empty:
            self.stop()

    @task
    def get_tasks(self):
        if not self.token:
            return

        headers = {"Authorization": f"Bearer {self.token}"}
        self.client.get("/tasks/", headers=headers)