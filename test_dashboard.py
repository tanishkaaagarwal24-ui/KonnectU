import requests


login_url = "http://127.0.0.1:5000/api/auth/login"


login = requests.post(
    login_url,
    json={
        "email": "admin@demo.com",
        "password": "password123"
    }
)


token = login.json()["token"]


headers = {
    "Authorization": f"Bearer {token}"
}


response = requests.get(
    "http://127.0.0.1:5000/api/dashboard",
    headers=headers
)


print("STATUS:", response.status_code)

print(response.json())