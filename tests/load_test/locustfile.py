import os
import queue

from locust import HttpUser, between, task
from locust.exception import StopUser

USERS_COUNT = int(os.getenv("LOADTEST_USERS_COUNT", "100"))
USER_PASSWORD = os.getenv("LOADTEST_USER_PASSWORD", "123456")

USERS_DATA = [
    {"email": f"loadtest_user_{i}@example.com", "password": USER_PASSWORD}
    for i in range(USERS_COUNT)
]

user_queue = queue.Queue()
for user in USERS_DATA:
    user_queue.put(user)


class APIUser(HttpUser):
    wait_time = between(0.5, 2.0)

    def on_start(self):
        try:
            creds = user_queue.get(block=False)
        except queue.Empty as exc:
            raise StopUser("No credentials available for this virtual user") from exc

        self.email = creds["email"]
        self.password = creds["password"]

        with self.client.post(
            "/auth/login",
            json={"email": self.email, "password": self.password},
            catch_response=True,
            name="auth_login",
        ) as response:
            if response.status_code != 200:
                response.failure(f"Login failed for {self.email}: {response.status_code} {response.text}")
                raise StopUser(f"Login failed for {self.email}")

            data = response.json()
            access_token = data.get("access_token")
            if not access_token:
                response.failure(f"Missing access_token for {self.email}")
                raise StopUser(f"Login token missing for {self.email}")

            self.token = access_token
            self.auth_headers = {"Authorization": f"Bearer {self.token}"}
            response.success()

    @task(3)
    def get_tasks(self):
        with self.client.get(
            "/tasks/?skip=0&limit=20",
            headers=self.auth_headers,
            catch_response=True,
            name="tasks_list",
        ) as response:
            if response.status_code != 200:
                response.failure(f"Get tasks failed: {response.status_code} {response.text}")
                return
            response.success()

    @task(1)
    def get_models(self):
        with self.client.get(
            "/models/?skip=0&limit=20",
            headers=self.auth_headers,
            catch_response=True,
            name="models_list",
        ) as response:
            if response.status_code != 200:
                response.failure(f"Get models failed: {response.status_code} {response.text}")
                return
            response.success()

    @task(1)
    def get_datasets(self):
        with self.client.get(
            "/datasets/?skip=0&limit=20",
            headers=self.auth_headers,
            catch_response=True,
            name="datasets_list",
        ) as response:
            if response.status_code != 200:
                response.failure(f"Get datasets failed: {response.status_code} {response.text}")
                return
            response.success()
