import os
from dotenv import load_dotenv
from google import genai

# Load the .env file
load_dotenv()

# Check that the API key was found
print("API key loaded:", bool(os.getenv("GEMINI_API_KEY")))

# Connect to Gemini
client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

# Send a test message
response = client.models.generate_content(
    model="gemini-3.6-flash",
    contents="Reply with exactly: KONNECTU WORKS"
)

# Display the response
print("Gemini response:")
print(response.text)