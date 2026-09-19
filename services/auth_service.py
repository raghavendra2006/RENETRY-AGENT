import functools
from flask import session, redirect, url_for, flash, g, request
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db_connection

def hash_password(password: str) -> str:
    return generate_password_hash(password)

def verify_password(stored_hash: str, password: str) -> bool:
    return check_password_hash(stored_hash, password)

def get_current_user():
    """Retrieves current logged-in user with profile and recruiter details."""
    user_id = session.get('user_id')
    if not user_id:
        return None

    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if not user:
        conn.close()
        return None

    profile = conn.execute("SELECT * FROM profiles WHERE user_id = ?", (user_id,)).fetchone()
    career_selection = conn.execute("SELECT * FROM career_selections WHERE user_id = ?", (user_id,)).fetchone()
    recruiter = None
    if user['role'] == 'RECRUITER':
        recruiter = conn.execute("SELECT * FROM recruiters WHERE user_id = ?", (user_id,)).fetchone()

    conn.close()
    return {
        'user': user,
        'profile': profile,
        'career_selection': career_selection,
        'recruiter': recruiter
    }

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if 'user_id' not in session:
            flash("Please sign in to access this page.", "warning")
            return redirect(url_for('auth_login', next=request.path))
        return view(**kwargs)
    return wrapped_view

def role_required(allowed_roles):
    """Decorator to enforce role-based access control."""
    def decorator(view):
        @functools.wraps(view)
        def wrapped_view(**kwargs):
            if 'user_id' not in session:
                flash("Please sign in to access this page.", "warning")
                return redirect(url_for('auth_login', next=request.path))
            
            user_role = session.get('user_role')
            if user_role not in allowed_roles:
                flash("You do not have permission to access that resource.", "danger")
                if user_role == 'RECRUITER':
                    return redirect(url_for('recruiter_dashboard'))
                elif user_role == 'ADMIN':
                    return redirect(url_for('admin_dashboard'))
                else:
                    return redirect(url_for('user_dashboard'))
            return view(**kwargs)
        return wrapped_view
    return decorator
