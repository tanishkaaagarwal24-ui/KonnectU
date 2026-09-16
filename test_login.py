import requests


url = "http://127.0.0.1:5000/api/auth/login"


data = {
    "email": "admin@demo.com",
    "password": "password123"
}


response = requests.post(
    url,
    json=data
)


print("STATUS:", response.status_code)

result = response.json()

print(result)