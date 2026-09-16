from flask import Blueprint, request, jsonify

from database.db import db
from database.models import User, Center

import jwt

from datetime import datetime, timedelta

from functools import wraps


auth = Blueprint(
    "auth",
    __name__,
    url_prefix="/api/auth"
)


SECRET_KEY = "konnectu-hackathon-secret"


def create_token(user):

    return jwt.encode(
        {
            "user_id": user.id,
            "center_id": user.center_id,
            "role": user.role,
            "exp": datetime.utcnow()
            + timedelta(hours=24)
        },
        SECRET_KEY,
        algorithm="HS256"
    )


def token_required(function):

    @wraps(function)
    def decorated(*args, **kwargs):

        header = request.headers.get("Authorization")

        if not header:

            return jsonify({
                "error": "Authentication required"
            }), 401

        try:

            token = header.split(" ")[1]

            data = jwt.decode(
                token,
                SECRET_KEY,
                algorithms=["HS256"]
            )

            user = User.query.get(
                data["user_id"]
            )

            if not user:

                return jsonify({
                    "error": "User not found"
                }), 401

        except Exception:

            return jsonify({
                "error": "Invalid or expired token"
            }), 401

        return function(user, *args, **kwargs)

    return decorated


def role_required(*roles):

    def decorator(function):

        @wraps(function)
        @token_required
        def wrapper(user, *args, **kwargs):

            if user.role not in roles:

                return jsonify({
                    "error": "Permission denied"
                }), 403

            return function(
                user,
                *args,
                **kwargs
            )

        return wrapper

    return decorator


@auth.route("/register", methods=["POST"])
def register():

    data = request.get_json() or {}

    required = [
        "name",
        "email",
        "password",
        "center_name"
    ]

    for field in required:

        if not data.get(field):

            return jsonify({
                "error": f"{field} is required"
            }), 400

    if User.query.filter_by(
        email=data["email"]
    ).first():

        return jsonify({
            "error": "Email already registered"
        }), 409

    center_name = data["center_name"]

    slug = center_name.lower()

    slug = slug.replace(" ", "-")

    center = Center(
        name=center_name,
        slug=slug,
        logo=data.get("logo"),
        primary_color=data.get(
            "primary_color",
            "#2563EB"
        ),
        secondary_color=data.get(
            "secondary_color",
            "#FFFFFF"
        ),
        language=data.get(
            "language",
            "English"
        )
    )

    db.session.add(center)

    db.session.flush()

    user = User(
        name=data["name"],
        email=data["email"],
        role="admin",
        center_id=center.id
    )

    user.set_password(
        data["password"]
    )

    db.session.add(user)

    db.session.commit()

    return jsonify({
        "message": "Center created successfully",
        "center": {
            "id": center.id,
            "name": center.name,
            "slug": center.slug
        },
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role
        }
    }), 201


@auth.route("/login", methods=["POST"])
def login():

    data = request.get_json() or {}

    user = User.query.filter_by(
        email=data.get("email")
    ).first()

    if not user:

        return jsonify({
            "error": "Invalid email or password"
        }), 401

    if not user.check_password(
        data.get("password", "")
    ):

        return jsonify({
            "error": "Invalid email or password"
        }), 401

    token = create_token(user)

    return jsonify({
        "message": "Login successful",
        "token": token,
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "center_id": user.center_id
        }
    })


@auth.route("/me")
@token_required
def me(user):

    return jsonify({
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "center_id": user.center_id
    })