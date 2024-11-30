from functools import wraps
from typing import Callable, List, Optional, Union
from quart import current_app, g, jsonify
from nautilus_api.config import Config

def require_access(minimum_role: Optional[str] = None, specific_roles: Optional[List[str]] = None) -> Callable:
    """
    Decorator to enforce role-based access control on an endpoint. Checks if the user has the required minimum role 
    or a specific role, as defined by ROLE_HIERARCHY.

    :param minimum_role: The minimum role required for access based on the role hierarchy.
    :param specific_roles: List of specific roles with exclusive access to the endpoint (overrides minimum role).
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        async def decorated_function(*args, **kwargs) -> Union[dict, tuple]:
            # Verify user is logged in by checking g.user
            if not g.user:
                current_app.logger.warning("Unauthorized access attempt to protected route")
                return jsonify({"error": "You must be logged in to access this route"}), 401

            user_role = g.user.get("role")
            user_id = g.user.get("user_id")

            # Enforce specific roles if defined
            if specific_roles:
                if user_role not in specific_roles:
                    current_app.logger.info(
                        f"Access denied for user {user_id}. Role: {user_role}. Allowed roles: {specific_roles}."
                    )
                    return jsonify({
                        "error": "Access denied. You do not have the required role to access this route.",
                        "allowed_roles": specific_roles,
                        "user_role": user_role
                    }), 403

            # Enforce minimum role based on ROLE_HIERARCHY if specific roles are not defined
            elif minimum_role:
                try:
                    # Get indices of user role and minimum role in ROLE_HIERARCHY to compare hierarchy levels
                    user_role_index = Config.ROLE_HIERARCHY.index(user_role)
                    minimum_role_index = Config.ROLE_HIERARCHY.index(minimum_role)
                except ValueError:
                    current_app.logger.warning(
                        f"Invalid role encountered: {user_role} or {minimum_role} not found in ROLE_HIERARCHY."
                    )
                    return jsonify({"error": "Invalid role in role hierarchy."}), 403

                # Deny access if user role rank is lower than the minimum required rank
                if user_role_index < minimum_role_index:
                    current_app.logger.info(
                        f"Access denied for user {user_id}. Role: {user_role}. Minimum required role: {minimum_role}."
                    )
                    return jsonify({
                        "error": "Access denied. You do not have the required minimum role to access this route.",
                        "minimum_role": minimum_role,
                        "user_role": user_role
                    }), 403

            # Access granted logging
            current_app.logger.info(f"Access granted for user {user_id} with role {user_role}")
            return await f(*args, **kwargs)

        return decorated_function
    return decorator