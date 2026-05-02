"""
Two roles:
    - admin: full access (all pages)
    - receptionist: limited access (no Reports, no user management)

For the demo, two hardcoded users are provided as a fallback.
replace with users stored in MongoDB
by completing get_user_by_username() in queries.py.
"""

import streamlit as st
import bcrypt
import queries

# Fallback hardcoded users (used if MongoDB users collection is empty)
# Passwords: admin123 / recep123
_FALLBACK_USERS = {
    "admin": {
        "password_hash": bcrypt.hashpw(b"admin123", bcrypt.gensalt()),
        "role": "admin",
        "full_name": "System Administrator",
    },
    "receptionist": {
        "password_hash": bcrypt.hashpw(b"recep123", bcrypt.gensalt()),
        "role": "receptionist",
        "full_name": "Front Desk Staff",
    },
}


def verify_login(username, password):
    """
    Check credentials. Returns user dict if valid, None otherwise.
    Tries MongoDB first; falls back to hardcoded users if not found.
    """
    # First try MongoDB (if groupmate has implemented get_user_by_username)
    user = queries.get_user_by_username(username)
    if user and "password_hash" in user:
        if bcrypt.checkpw(password.encode(), user["password_hash"]):
            return user

    # Fallback to hardcoded
    user = _FALLBACK_USERS.get(username)
    if user and bcrypt.checkpw(password.encode(), user["password_hash"]):
        return {"username": username, **user}

    return None


def is_authenticated():
    """Check if user is logged in."""
    return st.session_state.get("authenticated", False)


def get_current_user():
    """Get current logged-in user dict."""
    return st.session_state.get("user")


def get_current_role():
    """Return 'admin', 'receptionist', or None."""
    user = get_current_user()
    return user.get("role") if user else None


def login(user):
    """Set session as logged in."""
    st.session_state.authenticated = True
    st.session_state.user = user


def logout():
    """Clear session."""
    st.session_state.authenticated = False
    st.session_state.user = None


def require_role(*allowed_roles):
    """
    Helper: returns True if current user has any of the allowed roles.
    """
    return get_current_role() in allowed_roles