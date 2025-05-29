# academic_system_cli/database_repository.py
import sqlite3
import bcrypt
from models import User, Administrator, Lecturer, Student, Course, Group, Grade

# Define the database file name
DATABASE_NAME = "academic_system.db"

def get_db_connection():
    """Establishes and returns a connection to the SQLite database."""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn

class DatabaseRepository:
    """
    Manages all database interactions for the academic system using SQLite.
    Provides methods for creating tables and performing CRUD operations for all entities.
    """
    def __init__(self):
        self._create_tables()

    def _create_tables(self):
        """Creates database tables if they don't exist."""
        conn = get_db_connection()
        cursor = conn.cursor()

        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                surname TEXT NOT NULL,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL
            )
        ''')

        # Courses table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                lecturer_id INTEGER,
                FOREIGN KEY (lecturer_id) REFERENCES users(id) ON DELETE SET NULL
            )
        ''')

        # Groups table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        ''')

        # Grades table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS grades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                course_id INTEGER NOT NULL,
                value REAL,
                FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
                UNIQUE (student_id, course_id)
            )
        ''')

        # Linking table: group_students (Many-to-Many between Groups and Students)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS group_students (
                group_id INTEGER NOT NULL,
                student_id INTEGER NOT NULL,
                PRIMARY KEY (group_id, student_id),
                FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE CASCADE,
                FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')

        # Linking table: group_courses (Many-to-Many between Groups and Courses)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS group_courses (
                group_id INTEGER NOT NULL,
                course_id INTEGER NOT NULL,
                PRIMARY KEY (group_id, course_id),
                FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE CASCADE,
                FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
            )
        ''')

        conn.commit()
        conn.close()

    def _map_row_to_object(self, row, obj_type):
        """Helper to map a database row (sqlite3.Row) to a corresponding Python object."""
        if row is None:
            return None

        if obj_type == "users":
            role_map = {
                "admin": Administrator,
                "lecturer": Lecturer,
                "student": Student
            }
            user_class = role_map.get(row['role'], User) # Default to User if role is unexpected

            # --- CRITICAL FIX HERE ---
            # If it's a specific role class (Admin, Lecturer, Student),
            # don't pass the 'role' argument again, as it's hardcoded in their __init__.
            if user_class in [Administrator, Lecturer, Student]:
                return user_class(row['id'], row['name'], row['surname'],
                                  row['username'], row['password_hash'])
            else: # For the base User class, or if role is unexpected, pass all args
                return User(row['id'], row['name'], row['surname'],
                            row['username'], row['password_hash'], row['role'])
            # --- END CRITICAL FIX ---

        elif obj_type == "courses":
            return Course(row['id'], row['name'], row['lecturer_id'])
        elif obj_type == "groups":
            group = Group(row['id'], row['name'])
            
            # Populate linked student and course IDs
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT student_id FROM group_students WHERE group_id = ?', (group.id,))
            group.student_ids = [s_row['student_id'] for s_row in cursor.fetchall()]

            cursor.execute('SELECT course_id FROM group_courses WHERE group_id = ?', (group.id,))
            group.course_ids = [c_row['course_id'] for c_row in cursor.fetchall()]
            
            conn.close()
            return group
        elif obj_type == "grades":
            return Grade(row['id'], row['student_id'], row['course_id'], row['value'])
        else:
            raise ValueError(f"Unknown object type: {obj_type}")

    def find_one(self, collection_name, query):
        """
        Finds a single object in the database based on query.
        Example: find_one("users", {"username": "testuser"})
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        table_name = collection_name # Table names match collection names for simplicity
        
        # Build WHERE clause dynamically
        where_clause = " AND ".join([f"{key} = ?" for key in query.keys()])
        values = tuple(query.values())

        try:
            cursor.execute(f"SELECT * FROM {table_name} WHERE {where_clause}", values)
            row = cursor.fetchone()
            return self._map_row_to_object(row, collection_name)
        except sqlite3.Error as e:
            print(f"Database error during find_one: {e}")
            return None
        finally:
            conn.close()

    def find_all(self, collection_name, query={}):
        """
        Finds multiple objects in the database based on query.
        Example: find_all("users", {"role": "student"})
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        table_name = collection_name
        
        where_clause = ""
        values = ()
        if query:
            where_clause = " WHERE " + " AND ".join([f"{key} = ?" for key in query.keys()])
            values = tuple(query.values())

        try:
            cursor.execute(f"SELECT * FROM {table_name}{where_clause}", values)
            rows = cursor.fetchall()
            return [self._map_row_to_object(row, collection_name) for row in rows]
        except sqlite3.Error as e:
            print(f"Database error during find_all: {e}")
            return []
        finally:
            conn.close()

    def insert_one(self, collection_name, obj):
        """
        Inserts a single object into the database.
        Returns (True, "Success", new_id) on success, (False, "Error message", None) on failure.
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        table_name = collection_name

        try:
            if collection_name == "users":
                cursor.execute(
                    "INSERT INTO users (name, surname, username, password_hash, role) VALUES (?, ?, ?, ?, ?)",
                    (obj.name, obj.surname, obj.username, obj.password_hash, obj.role)
                )
            elif collection_name == "courses":
                cursor.execute(
                    "INSERT INTO courses (name, lecturer_id) VALUES (?, ?)",
                    (obj.name, obj.lecturer_id)
                )
            elif collection_name == "groups":
                cursor.execute("INSERT INTO groups (name) VALUES (?)", (obj.name,))
            elif collection_name == "grades":
                # Ensure unique student_id, course_id pair before inserting
                existing_grade = self.find_one("grades", {"student_id": obj.student_id, "course_id": obj.course_id})
                if existing_grade:
                    return False, "A grade for this student in this course already exists.", None
                cursor.execute(
                    "INSERT INTO grades (student_id, course_id, value) VALUES (?, ?, ?)",
                    (obj.student_id, obj.course_id, obj.value)
                )
            else:
                return False, f"Cannot insert into unknown collection: {collection_name}", None
            
            conn.commit()
            return True, "Success", cursor.lastrowid # Return the ID of the newly inserted row
        except sqlite3.IntegrityError as e:
            # This catches UNIQUE constraint failures (e.g., duplicate username, course name, group name)
            conn.rollback()
            return False, f"Integrity error: {e}", None
        except sqlite3.Error as e:
            conn.rollback()
            return False, f"Database error during insert: {e}", None
        finally:
            conn.close()

    def update_one(self, collection_name, obj_id, updates):
        """
        Updates a single object in the database.
        `updates` is a dictionary of columns to update and their new values.
        Example: update_one("grades", grade_id, {"value": 95.0})
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        table_name = collection_name
        
        set_clause = ", ".join([f"{key} = ?" for key in updates.keys()])
        values = tuple(updates.values()) + (obj_id,) # Add the ID for the WHERE clause

        try:
            cursor.execute(f"UPDATE {table_name} SET {set_clause} WHERE id = ?", values)
            conn.commit()
            return cursor.rowcount > 0 # True if at least one row was updated
        except sqlite3.Error as e:
            print(f"Database error during update: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def delete_one(self, collection_name, obj_id):
        """Deletes a single object from the database by its ID."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        table_name = collection_name
        
        try:
            cursor.execute(f"DELETE FROM {table_name} WHERE id = ?", (obj_id,))
            conn.commit()
            return cursor.rowcount > 0 # True if a row was deleted
        except sqlite3.Error as e:
            print(f"Database error during delete: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    # --- Linking Table Management Methods ---

    def add_student_to_group(self, group_id, student_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO group_students (group_id, student_id) VALUES (?, ?)",
                (group_id, student_id)
            )
            conn.commit()
            return True, "Student added to group successfully."
        except sqlite3.IntegrityError:
            conn.rollback()
            return False, "Student is already in this group."
        except sqlite3.Error as e:
            conn.rollback()
            return False, f"Database error: {e}"
        finally:
            conn.close()

    def remove_student_from_group(self, group_id, student_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "DELETE FROM group_students WHERE group_id = ? AND student_id = ?",
                (group_id, student_id)
            )
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            conn.rollback()
            print(f"Database error: {e}")
            return False
        finally:
            conn.close()

    def add_course_to_group(self, group_id, course_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO group_courses (group_id, course_id) VALUES (?, ?)",
                (group_id, course_id)
            )
            conn.commit()
            return True, "Course added to group successfully."
        except sqlite3.IntegrityError:
            conn.rollback()
            return False, "Course is already assigned to this group."
        except sqlite3.Error as e:
            conn.rollback()
            return False, f"Database error: {e}"
        finally:
            conn.close()

    def remove_course_from_group(self, group_id, course_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "DELETE FROM group_courses WHERE group_id = ? AND course_id = ?",
                (group_id, course_id)
            )
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            conn.rollback()
            print(f"Database error: {e}")
            return False
        finally:
            conn.close()