from quart import Blueprint, jsonify, g, request, current_app
from app.permissions import roles_permissions
from functools import wraps
import jwt
from app.config import Config
from app.controllers import account_controller

api = Blueprint('api', __name__)

def require_access(roles=None, permissions=None):
    """
    Decorator to check if a user has either an allowed role or the required permissions.
    
    :param roles: List of allowed roles (e.g., ["app_admin", "teacher"])
    :param permissions: List of required permissions (e.g., ["create_events", "edit_attendance"])
    """
    if roles is None:
        roles = []
    if permissions is None:
        permissions = []

    def decorator(f):
        @wraps(f)
        async def decorated_function(*args, **kwargs):
            # Check if the user is logged in
            if not g.user:
                current_app.logger.warning("Unauthorized access attempt to protected route")
                return jsonify({"error": "You must be logged in to access this route"}), 401

            # Get the user's role from the token data
            user_role = g.user.get("role")

            # Get the user's permissions based on their role
            user_permissions = roles_permissions.get(user_role, {}).get("permissions", {}) 

            # Check if the user's role is in the allowed roles list
            role_allowed = user_role in roles

            # Get a list of permissions that the user is missing
            missing_permissions = [perm for perm in permissions if not user_permissions.get(perm)]

            # If no permissions are required, then the user has all the required permissions
            permission_allowed = not missing_permissions

            # Logging for debugging if access is denied
            if not (role_allowed or permission_allowed):
                # Log the missing roles and permissions
                missing_info = {
                    "missing_roles": [] if role_allowed else roles,
                    "missing_permissions": missing_permissions,
                }
                current_app.logger.info(
                    f"Access denied for user {g.user.get('user_id')}. "
                    f"Role: {user_role}. Required roles: {roles}. "
                    f"Required permissions: {permissions}. Missing: {missing_info}"
                )
                return jsonify({
                    "error": "Access denied",
                    "details": missing_info
                }), 403

            # Access granted if either role or permission requirements are met
            current_app.logger.info(f"Access granted for user {g.user.get('user_id')} with role {user_role}")
            return await f(*args, **kwargs)
        return decorated_function
    return decorator

@api.errorhandler(Exception)
async def handle_exception(e):
    # Log the exception (optional)
    current_app.logger.error(f"Unhandled exception: {e}")
    # Return a JSON response with a default error message and a 500 status code
    return jsonify({"error": "An unexpected error occurred. Please report this immediately!"}), 500

# A middleware that runs before each request to authenticate the user
@api.before_request
def authenticate_user():
    # Get the token from the Authorization header
    auth_header = request.headers.get("Authorization")
    # Check if the token is a Bearer token
    if auth_header and auth_header.startswith("Bearer "):
        # Extract the token from the header
        token = auth_header.split(" ")[1]
        try:
            # Decode the token and set g.user based on the token data
            decoded_token = jwt.decode(token, Config.JWT_SECRET, algorithms=["HS256"])
            # Set g.user to the token data
            g.user = decoded_token
            current_app.logger.info(f"User {g.user.get('user_id')} authenticated successfully")
        except jwt.InvalidTokenError:
            # Set g.user to None if token is invalid
            g.user = None
            current_app.logger.warning("Invalid token provided for authentication")
    else:
        # No user if no token provided
        g.user = None 
        current_app.logger.warning("No token provided for authentication")

# Register user account
@api.route("/register", methods=["POST"])
async def register():
    # Receive and log registration data
    data = await request.get_json()
    current_app.logger.info(f"Registering new user with data: {data.get('username', 'unknown')}")
    # Process registration and return result
    result = await account_controller.register_user(data)
    if "error" in result:
        current_app.logger.error(f"Failed to register user: {result['error']}")
    else:
        current_app.logger.info("User registered successfully")
    return jsonify(result), result.get("status", 200)

# Login user
@api.route("/login", methods=["POST"])
async def login():
    # Receive and log login data
    data = await request.get_json()
    current_app.logger.info(f"Attempting to log in user with data: {data.get('username', 'unknown')}")
    # Process login and return result
    result = await account_controller.login_user(data)
    if "error" in result:
        current_app.logger.error(f"Failed login attempt for user: {data.get('username', 'unknown')}")
    else:
        current_app.logger.info("User logged in successfully")
    return jsonify(result), result.get("status", 200)

@api.route("/test_auth")
@require_access(roles=["admin"])
def protected_route():
    # Protected route example requiring user to be logged in
    if not g.user:
        current_app.logger.warning("Unauthorized access attempt to protected route")
        return jsonify({"error": "Unauthorized"}), 401
    current_app.logger.info(f"Protected route accessed by user {g.user['user_id']}")
    return jsonify({"message": f"Hello, user {g.user['user_id']}"}), 200

def register_routes(app):
    # Register API routes
    app.register_blueprint(api, url_prefix="/api")