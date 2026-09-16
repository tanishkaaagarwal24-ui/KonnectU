import requests


url = "http://127.0.0.1:5000/api/auth/register"


data = {
    "name": "Demo Admin",
    "email": "admin@demo.com",
    "password": "password123",

    "center_name": "Demo Academy",

    "primary_color": "#2563EB",
    "secondary_color": "#FFFFFF",

    "language": "Hindi"
}


response = requests.post(
    url,
    json=data
)


print("STATUS:", response.status_code)

print(response.json())