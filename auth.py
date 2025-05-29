# academic_system_cli/auth.py
import bcrypt
from models import Administrator
from database_repository import DATABASE_NAME

def hash_password(password):
    """Hashes a plaintext password using bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(hashed_password, password):
    """Verifies a plaintext password against a bcrypt hashed password."""
    try:
        # --- FIX IS HERE ---
        # Change 'utf-255' to 'utf-8' for the plaintext password encoding
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    except ValueError:
        return False
    except Exception as e:
        print(f"Password check error: {e}")
        return False

def get_user_by_username(repository, username):
    """Retrieves a user object by username from the database via repository."""
    return repository.find_one("users", {"username": username})

def get_user_by_id(repository, user_id):
    """Retrieves a user object by ID from the database via repository."""
    return repository.find_one("users", {"id": user_id})

def seed_initial_admin_if_needed(repository):
    """Creates a default admin user if none exists in the database."""
    admin_exists = repository.find_one("users", {"role": "admin"})

    if not admin_exists:
        admin_id = None
        username = "admin.user"
        password = "user"
        hashed_pw = hash_password(password)

        admin_user = Administrator(admin_id, "Admin", "System", username, hashed_pw)
        success, msg, new_id = repository.insert_one("users", admin_user)
        if success:
            print(f"\n--- Initial Administrator created ---")
            print(f"Username: {username}")
            print(f"Password: {password}")
            print(f"This data is now stored in '{DATABASE_NAME}'.")
            print(f"-------------------------------------\n")
        else:
            print(f"\n--- Failed to seed initial admin: {msg} ---")
            print(f"-------------------------------------\n")