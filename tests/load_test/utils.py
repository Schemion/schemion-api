import httpx

BASE_URL = "http://localhost:8000"


def create_users(count=100):
    with httpx.Client() as client:
        for i in range(count):
            email = f"loadtest_user_{i}@example.com"
            password = "123456"

            response = client.post(url=f"{BASE_URL}/auth/register", json={
                "email": email,
                "password": password,
                "role": "user" # да тут должен быть енумчик но по факту по дефолту и так будет user
            })

            if response.status_code == 200 or response.status_code == 201:
                print(f"Created {email}")
            elif response.status_code == 400:
                print(f"User {email} already exists")
            else:
                print(f"Error creating {email}: {response.text}")


if __name__ == "__main__":
    create_users()