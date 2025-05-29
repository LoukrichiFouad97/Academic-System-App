# academic_system_cli/models.py

class User:
    def __init__(self, user_id, name, surname, username, password_hash, role):
        self.id = user_id
        self.name = name
        self.surname = surname
        self.username = username
        self.password_hash = password_hash
        self.role = role

    def get_full_name(self):
        return f"{self.name} {self.surname}"

    def get_role(self):
        return self.role

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "surname": self.surname,
            "username": self.username,
            "role": self.role
        }

class Administrator(User):
    # Removed 'role' from the __init__ signature here
    def __init__(self, user_id, name, surname, username, password_hash):
        super().__init__(user_id, name, surname, username, password_hash, "admin")

class Lecturer(User):
    # Removed 'role' from the __init__ signature here
    def __init__(self, user_id, name, surname, username, password_hash):
        super().__init__(user_id, name, surname, username, password_hash, "lecturer")

class Student(User):
    # Removed 'role' from the __init__ signature here
    def __init__(self, user_id, name, surname, username, password_hash):
        super().__init__(user_id, name, surname, username, password_hash, "student")

class Course:
    def __init__(self, course_id, name, lecturer_id=None):
        self.id = course_id
        self.name = name
        self.lecturer_id = lecturer_id

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "lecturer_id": self.lecturer_id
        }

class Group:
    def __init__(self, group_id, name):
        self.id = group_id
        self.name = name
        self.student_ids = []
        self.course_ids = []

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "student_ids": self.student_ids,
            "course_ids": self.course_ids
        }

class Grade:
    def __init__(self, grade_id, student_id, course_id, value):
        self.id = grade_id
        self.student_id = student_id
        self.course_id = course_id
        self.value = value

    def to_dict(self):
        return {
            "id": self.id,
            "student_id": self.student_id,
            "course_id": self.course_id,
            "value": self.value
        }