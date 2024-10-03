from flask import Blueprint, request, jsonify, make_response
from app.main import db
from psycopg2 import sql
from app.main.models.users import User
from app.main.config import Config
import uuid
import jwt
import datetime
import os
import logging
import moment
from app.main.utils.middleware import auth_token_required

auth_blueprint = Blueprint("auth", __name__)


@auth_blueprint.route("/users", methods=["GET"])
def get_users():
    users = User.query.all()
    return jsonify([user.username for user in users])


@auth_blueprint.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    try:
        new_user = User(
            username=data["username"],
            email=data["email"],
            user_id=data["userId"],
            firstname=data["firstName"],
            lastname=data["lastName"],
            password=data["password"],
            fullname=data["fullname"],
            role="Admin",
            feature=["epdm"],
            tools=["epdm"],
        )
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"message": "User registered successfully"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "An error occurred"}), 500


@auth_blueprint.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    conn = Config.get_db_connection()
    cursor = conn.cursor()
    try:
        schema_query = sql.SQL(
            "SELECT organization FROM mercury.email_organization_lookup WHERE email=%s"
        )
        cursor.execute(schema_query, (email,))
        schema_result = cursor.fetchone()

        if not schema_result:
            return make_response(
                jsonify({"message": "User does not exist in the organization"}), 404
            )

        org_schema_name = schema_result[0].lower()

        login_query = sql.SQL(
            "SELECT * FROM mercury.mdxusers WHERE username=%s AND mercury.decrypt(password)=%s"
        )
        cursor.execute(login_query, (email, password))
        user = cursor.fetchone()

        if not user:
            return make_response(
                jsonify({"message": "Invalid Username or Password"}), 401
            )

        session_id = str(uuid.uuid4())
        now = datetime.datetime.utcnow()
        formatted_date = moment.now().format("YYYY-MM-DD")
        log_filename = f"session_{formatted_date}_{session_id}.log"
        log_file_path = os.path.join(Config.LOGS_PATH, log_filename)

        print(log_file_path)

        # Generate JWT token
        token = jwt.encode(
            {
                "userId": user[0],
                "role": user[8],
                "organisation": "mercury",
                "user": user[3],
                "tool": user[9],
                "email": email,
                "serverlog": log_file_path,
                "feature": user[9],
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
                f"[{moment.now().format('YYYY-MM-DD hh:mm:ss A')}] User: {user[4]}, IP: {request.remote_addr}, User-Agent: {request.headers.get('User-Agent')} logged in\n"
            )
            log_file.write(
                f"[{moment.now().format('YYYY-MM-DD hh:mm:ss A')}] session id allocated is :: {session_id}\n"
            )

        # Insert session data into the database
        session_query = sql.SQL(
            "INSERT INTO mercury.mdxsessions (session_id, user_id, ip_address, user_agent, status) VALUES (%s, %s, %s, %s, %s)"
        )
        cursor.execute(
            session_query,
            (
                session_id,
                user[7],
                request.remote_addr,
                request.headers.get("User-Agent"),
                "Active",
            ),
        )
        conn.commit()

        # Set cookies with the token and session ID
        response = make_response(
            jsonify(
                {
                    "message": "Login successful",
                    "role": user[8],
                    "username": user[3],
                    "tool": user[9],
                    "organisation": org_schema_name,
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
    organisation = data.get("organisation")
    conn = Config.get_db_connection()
    cursor = conn.cursor()

    try:
        schema_query = sql.SQL(
            "SELECT organization FROM mercury.email_organization_lookup WHERE email=%s"
        )
        cursor.execute(schema_query, (email,))
        schema_result = cursor.fetchone()

        if not schema_result:
            return make_response(
                jsonify({"message": "User does not exist in the organization"}), 404
            )

        org_schema_name = schema_result[0].lower()

        validate_query = sql.SQL("SELECT * FROM mercury.mdxusers WHERE username = %s")
        cursor.execute(validate_query, (email,))
        user = cursor.fetchone()

        if not user:
            return make_response(
                jsonify({"message": "Invalid Username or Password"}), 401
            )

        response = make_response(
            jsonify(
                {
                    "message": "User is logged in",
                    "user": {
                        "role": role,
                        "username": user[3],
                        "tool": user[9],
                        "organisation": organisation,
                        "userId": userId,
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
    organisation = data.get("organisation")
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

        # Insert session data into the database
        session_query = sql.SQL(
            "UPDATE mercury.mdxsessions "
            "SET logout_time = CURRENT_TIMESTAMP, ip_address = %s, user_agent = %s, status = %s "
            "WHERE session_id = %s AND user_id = %s"
        )
        cursor.execute(
            session_query,
            (
                request.remote_addr,
                request.headers.get("User-Agent"),
                "In Active",
                session_id,
                user[7],
            ),
        )
        conn.commit()
        response = make_response(
            jsonify(
                {
                    "message": "Logged out successful",
                }
            ),
            200,
        )
        response.delete_cookie(
            "token", httponly=True, secure=True, samesite="None"
        )
        response.delete_cookie(
            "sessionId", httponly=True, secure=True, samesite="None"
        )
        return response

    except Exception as e:
        logging.error(f"UserLogoutError: {e}")
        return make_response(jsonify({"message": "Internal Server Error"}), 500)

    finally:
        cursor.close()
        conn.close()
    # return jsonify({'message': 'User validated successfully','user':{'role':'Admin','organisation':'mavenberg','userId':1}}), 200
