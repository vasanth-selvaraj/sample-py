from flask import Blueprint, request, jsonify, make_response
from app.main import db
from psycopg2 import sql
from app.main.models.users import User
from app.main.config import config_by_name,Config
import uuid
import jwt
import datetime
import os
import logging
import moment
from app.main.utils.middleware import auth_token_required

auth_blueprint = Blueprint("auth", __name__)

env = os.getenv('FLASK_CONFIG')

@auth_blueprint.route("/users", methods=["GET"])
def get_users():
    users = User.query.all()
    return jsonify([user.username for user in users])


@auth_blueprint.route("/register-user", methods=["POST"])
def register():
    data = request.get_json()
    conn = config_by_name.get(env).get_db_connection()
    cursor = conn.cursor()
    try:
        validateDuplicate = sql.SQL("SELECT COUNT(*) FROM users WHERE email=%s")
        cursor.execute(validateDuplicate, (data["email"],))
        count = cursor.fetchone()[0]
        if count>0:
            return make_response(
                jsonify({"message": "User already exists"}), 400
            )
        signupQuery = sql.SQL(
            "INSERT INTO users (username,email,password_hash,role_id,status) VALUES (%s,%s,encrypt_password(%s),%s,%s)"
        )
        cursor.execute(
            signupQuery,
            (data["username"], data["email"], data["password"], 1, "active"),
        )
        cursor.connection.commit()
        response = make_response(
            jsonify(
                {
                    "message": "Registration successful",
                    "role": "Admin",
                    "username": data["username"],
                }
            ),
            200,
        )
        return response
    except Exception as e:
        print(e)
        error_message = str(e)
        logging.error(f"User Registration Error: {e}")
        return jsonify({"error": "An error occurred","message":error_message}), 500


@auth_blueprint.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")
    print(env)
    conn = config_by_name.get(env).get_db_connection()
    cursor = conn.cursor()
    print(conn)
    try:

        login_query = sql.SQL(
            "SELECT * FROM users WHERE email=%s"
        )
        cursor.execute(login_query, (email,))
        user = cursor.fetchone()
        print(user)
        if not user:
            return make_response(
                jsonify({"message": "User not found"}), 404
            )
        validation_query = """
            SELECT decrypt_password(%s, %s)
        """
        cursor.execute(validation_query, (password, user[3]))
        is_valid = cursor.fetchone()[0]
        print(is_valid)
        session_id = str(uuid.uuid4())
        now = datetime.datetime.utcnow()
        formatted_date = moment.now().format("YYYY-MM-DD")
        log_filename = f"session_{formatted_date}_{session_id}.log"
        log_file_path = os.path.join(Config.LOGS_PATH, log_filename)

        print(log_file_path)
        print(user)
        # Generate JWT token
        token = jwt.encode(
            {
                "userId": user[0],
                "role": "Admin",
                "user": user[1],
                "email": email,
                "serverlog": log_file_path,
                "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24),
            },
            Config.JWT_SECRET_KEY,
            algorithm="HS256",
        )

        # Log login details
        if not os.path.exists(Config.LOGS_PATH):
            os.makedirs(Config.LOGS_PATH)
        with open(log_file_path, "w") as log_file:
            log_file.write(
                f"[{moment.now().format('YYYY-MM-DD hh:mm:ss A')}] User: {user[1]}, IP: {request.remote_addr}, User-Agent: {request.headers.get('User-Agent')} logged in\n"
            )
            log_file.write(
                f"[{moment.now().format('YYYY-MM-DD hh:mm:ss A')}] session id allocated is :: {session_id}\n"
            )

        # Set cookies with the token and session ID
        response = make_response(
            jsonify(
                {
                    "message": "Login successful",
                    "role": "Admin",
                    "username": user[1],
                    "userId": user[0],
                }
            ),
            200,
        )
        response.set_cookie("token", token, httponly=True, secure=True, samesite="None")
        response.set_cookie(
            "sessionId", session_id, httponly=True, secure=True, samesite="None"
        )

        return response

    except Exception as e:
        logging.error(f"UserLoginError: {e}")
        return make_response(jsonify({"message": "Internal Server Error"}), 500)

    finally:
        cursor.close()
        conn.close()


@auth_blueprint.route("/validate-user", methods=["GET"])
@auth_token_required
def validateUser():
    data = request.user
    email = data.get("email")
    role = data.get("role")
    userId = data.get("userId")
    user = data.get("user")
    conn = Config.get_db_connection()
    cursor = conn.cursor()

    try:
        user_query = sql.SQL(
            "SELECT * FROM users WHERE email=%s"
        )
        cursor.execute(user_query, (email,))
        user = cursor.fetchone()

        if not user:
            return make_response(
                jsonify({"message": "User does not exist"}), 404
            )

        if not user:
            return make_response(
                jsonify({"message": "Invalid Username or Password"}), 401
            )

        response = make_response(
            jsonify(
                {
                    "message": "User is logged in",
                    "user": {
                        "role": "Admin",
                        "username": user[1],
                        "userId": user[0],
                    },
                }
            ),
            200,
        )

        return response

    except Exception as e:
        logging.error(f"UserLoginError: {e}")
        return make_response(jsonify({"message": "Internal Server Error"}), 500)

    finally:
        cursor.close()
        conn.close()
    # return jsonify({'message': 'User validated successfully','user':{'role':'Admin','organisation':'mavenberg','userId':1}}), 200


@auth_blueprint.route("/logout", methods=["GET"])
@auth_token_required
def logoutUser():
    data = request.user
    session_id = request.cookies.get("sessionId")
    userId = data.get("userId")
    user = data.get("user")
    conn = Config.get_db_connection()
    cursor = conn.cursor()

    try:
        now = datetime.datetime.utcnow()
        formatted_date = moment.now().format("YYYY-MM-DD")
        log_filename = f"session_{formatted_date}_{session_id}.log"
        log_file_path = os.path.join(Config.LOGS_PATH, log_filename)
        if not os.path.exists(Config.LOGS_PATH):
            os.makedirs(Config.LOGS_PATH)
        with open(log_file_path, "a") as log_file:
            log_file.write(
                f"[{moment.now().format('YYYY-MM-DD hh:mm:ss A')}] User: {data.get('email')}, Logged out {request.headers.get('User-Agent')} on IP: {request.remote_addr}\n"
            )

        response = make_response(
            jsonify(
                {
                    "message": "Logged out successful",
                }
            ),
            200,
        )
        response.delete_cookie("token", httponly=True, secure=True, samesite="None")
        response.delete_cookie("sessionId", httponly=True, secure=True, samesite="None")
        return response

    except Exception as e:
        logging.error(f"UserLogoutError: {e}")
        return make_response(jsonify({"message": "Internal Server Error"}), 500)

    finally:
        cursor.close()
        conn.close()
    # return jsonify({'message': 'User validated successfully','user':{'role':'Admin','organisation':'mavenberg','userId':1}}), 200

# @auth_blueprint.route("/forget-password", methods=["POST"])
# def forgetPassword():
    