# app/utils/middleware.py
import jwt
import logging
from flask import request, jsonify, make_response
from functools import wraps
from app.main.config import Config  # Import your JWT secret from your config


# Middleware to check auth token
def auth_token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get the token and sessionId from cookies
        token = request.cookies.get("token")
        # print(token)
        session_id = request.cookies.get("sessionId")

        # Check if token is present
        if not token:
            res = make_response(jsonify({"message": "Auth Token not found"}), 403)
            res.delete_cookie("token", httponly=True, secure=True, samesite="None")
            res.delete_cookie("sessionId", httponly=True, secure=True, samesite="None")
            return res

        try:
            user = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=["HS256"])
            request.user = user  # Attach user info to request object

            # Log the request
            logger = logging.getLogger("serverLogger")
            logger.info(
                f"[user:{user['user']}] {request.method} {request.url} Triggered"
            )

        except jwt.ExpiredSignatureError:
            res = make_response(jsonify({"message": "Token Expired"}), 403)
            res.delete_cookie("token", httponly=True, secure=True, samesite="None")
            res.delete_cookie("sessionId", httponly=True, secure=True, samesite="None")
            return res
        except jwt.InvalidTokenError:
            res = make_response(jsonify({"message": "Invalid Token"}), 403)
            res.delete_cookie("token", httponly=True, secure=True, samesite="None")
            res.delete_cookie("sessionId", httponly=True, secure=True, samesite="None")
            return res

        return f(*args, **kwargs)

    return decorated_function
