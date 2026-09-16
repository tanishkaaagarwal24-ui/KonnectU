import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)
from flask import Flask, jsonify

from flask_cors import CORS

from database.db import db

from database.models import *

from routes.auth import auth

from routes.main import main


app = Flask(__name__)


app.config[
    "SQLALCHEMY_DATABASE_URI"
] = "sqlite:///konnectu.db"


app.config[
    "SQLALCHEMY_TRACK_MODIFICATIONS"
] = False


CORS(app)


db.init_app(app)


app.register_blueprint(auth)

app.register_blueprint(main)


with app.app_context():

    db.create_all()


@app.route("/")
def home():

    return jsonify({
        "name": "KonnectU",
        "status": "Backend is running!",
        "version": "1.0"
    })


@app.route("/api/health")
def health():

    return jsonify({
        "application": "KonnectU",
        "status": "healthy"
    })


if __name__ == "__main__":

    app.run(
        debug=True,
        host="0.0.0.0",
        port=5000
    )