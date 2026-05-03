import os

import httpx

BASE_URL = os.getenv("LOADTEST_BASE_URL", "http://localhost:8000")
USERS_COUNT = int(os.getenv("LOADTEST_USERS_COUNT", "100"))
USER_PASSWORD = os.getenv("LOADTEST_USER_PASSWORD", "123456")


def create_users(count: int = USERS_COUNT):
    with httpx.Client(base_url=BASE_URL, timeout=15.0) as client:
        for i in range(count):
            email = f"loadtest_user_{i}@example.com"

            response = client.post(
                "/auth/register",
                json={"email": email, "password": USER_PASSWORD, "role": "user"},
            )

            if response.status_code in (200, 201):
                print(f"Created {email}")
            elif response.status_code == 400:
                print(f"User {email} already exists")
            else:
                print(f"Error creating {email}: {response.status_code} {response.text}")


if __name__ == "__main__":
    create_users()
