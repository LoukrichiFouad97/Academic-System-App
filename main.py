
import os 
import auth # I
from models import User, Administrator, Lecturer, Student, Course, Group, Grade
from database_repository import DatabaseRepository 


current_user = None

system_repo = None 

# --- Utility Functions ---
def clear_screen():
    """Clears the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def display_menu(options):
    """Displays a numbered menu."""
    for i, option in enumerate(options, 1):
        print(f"{i}. {option}")
    print("0. Back" if "Back" in options else "0. Exit")

def get_choice(max_choice):
    """Gets a valid integer choice from the user."""
    while True:
        try:
            choice = int(input("Enter your choice: "))
            if 0 <= choice <= max_choice:
                return choice
            else:
                print("Invalid choice. Please try again.")
        except ValueError:
            print("Invalid input. Please enter a number.")

def login():
    """Handles user login for the CLI."""
    global current_user, system_repo # Access the global repository
    while True:
        clear_screen()
        print("--- Login ---")
        username = input("Username: ").strip()
        password = input("Password: ").strip()

        user_obj = auth.get_user_by_username(system_repo, username) # Pass repository

        if user_obj and auth.check_password(user_obj.password_hash, password):
            current_user = user_obj
            print(f"\nLogged in successfully as {current_user.get_role().capitalize()}!")
            input("Press Enter to continue...")
            return True
        else:
            print("\nInvalid username or password.")
            choice = input("Try again? (y/n): ").lower()
            if choice != 'y':
                return False

def logout():
    """Logs out the current user."""
    global current_user
    current_user = None
    print("\nYou have been logged out.")
    input("Press Enter to continue...")

###################################################################

########################## SERVICES ###############################

###################################################################

# --- Admin services ---
def admin_manage_users():
    global system_repo
    while True:
        clear_screen()
        print("--- Admin: Manage Users ---")
        options = ["Add New User", "View All Users", "Delete User"]
        display_menu(options)
        choice = get_choice(len(options))

        if choice == 1: # Add New User
            name = input("Enter Name: ").strip()
            surname = input("Enter Surname: ").strip()
            while True:
                role = input("Enter Role (admin, lecturer, student): ").strip().lower()
                if role in ['admin', 'lecturer', 'student']:
                    break
                else:
                    print("Invalid role. Please choose admin, lecturer, or student.")

            user_id = None # Let SQLite handle ID (AUTOINCREMENT)
            username = f"{name.lower()}.{surname.lower()}"
            password = surname.lower() # Automatic password
            hashed_password = auth.hash_password(password)

            new_user = None
            if role == 'admin':
                new_user = Administrator(user_id, name, surname, username, hashed_password)
            elif role == 'lecturer':
                new_user = Lecturer(user_id, name, surname, username, hashed_password)
            elif role == 'student':
                new_user = Student(user_id, name, surname, username, hashed_password)

            if new_user:
                success, msg, _ = system_repo.insert_one("users", new_user) # Use repository
                if success:
                    print(f"\nSuccessfully added {role}: {name} {surname}.")
                    print(f"Username: {username}, Password: {password}")
                else:
                    print(f"\nError: {msg}")
            else:
                print("\nError: Could not create user object.")
            input("Press Enter to continue...")

        elif choice == 2: # View All Users
            print("\n--- All Users ---")
            users_to_display = system_repo.find_all("users") # Use repository
            if users_to_display:
                for user in users_to_display:
                    print(f"ID: {user.id}, Name: {user.get_full_name()}, Username: {user.username}, Role: {user.get_role().capitalize()}")
            else:
                print("No users found.")
            input("Press Enter to continue...")

        elif choice == 3: # Delete User
            user_id_input = input("Enter ID of user to delete: ").strip()
            try:
                user_id_to_delete = int(user_id_input)
            except ValueError:
                print("Invalid ID. Please enter a number.")
                input("Press Enter to continue...")
                continue

            user_obj = system_repo.find_one("users", {"id": user_id_to_delete}) # Use repository

            if not user_obj:
                print("User not found.")
            elif user_obj.get_role() == 'admin' and user_obj.username == 'admin.user':
                print("Cannot delete the primary administrator.")
            else:
                # Due to CASCADE DELETE rules in the DB, linked grades and group_students
                # records are handled automatically when a user (student) is deleted.
                # We only need to handle explicit unassignment for lecturers from courses.
                if user_obj.get_role() == 'lecturer':
                    lecturer_courses = system_repo.find_all("courses", {"lecturer_id": user_id_to_delete})
                    for course in lecturer_courses:
                        system_repo.update_one("courses", course.id, {"lecturer_id": None})

                if system_repo.delete_one("users", user_id_to_delete): # Use repository
                    print("User deleted successfully.")
                else:
                    print("Failed to delete user.")
            input("Press Enter to continue...")

        elif choice == 0:
            break

def admin_manage_courses():
    global system_repo
    while True:
        clear_screen()
        print("--- Admin: Manage Courses ---")
        options = ["Add New Course", "View All Courses", "Delete Course"]
        display_menu(options)
        choice = get_choice(len(options))

        if choice == 1: # Add New Course
            course_name = input("Enter Course Name: ").strip()
            course_id = None # Let SQLite handle ID
            new_course = Course(course_id, course_name)
            success, msg, _ = system_repo.insert_one("courses", new_course) # Use repository
            if success:
                print(f"Course '{course_name}' added successfully.")
            else:
                print(f"Error: {msg}")
            input("Press Enter to continue...")

        elif choice == 2: # View All Courses
            print("\n--- All Courses ---")
            courses_to_display = system_repo.find_all("courses") # Use repository
            if courses_to_display:
                for course in courses_to_display:
                    lecturer_name = "N/A"
                    if course.lecturer_id:
                        lecturer = system_repo.find_one("users", {"id": course.lecturer_id}) # Use repository
                        if lecturer:
                            lecturer_name = lecturer.get_full_name()
                    print(f"ID: {course.id}, Name: {course.name}, Lecturer: {lecturer_name}")
            else:
                print("No courses found.")
            input("Press Enter to continue...")

        elif choice == 3: # Delete Course
            course_id_input = input("Enter ID of course to delete: ").strip()
            try:
                course_id_to_delete = int(course_id_input)
            except ValueError:
                print("Invalid ID. Please enter a number.")
                input("Press Enter to continue...")
                continue

            # Due to CASCADE DELETE rules in the DB, linked grades and group_courses
            # records are handled automatically when a course is deleted.
            if system_repo.delete_one("courses", course_id_to_delete): # Use repository
                print("Course deleted successfully.")
            else:
                print("Failed to delete course or course not found.")
            input("Press Enter to continue...")

        elif choice == 0:
            break

def admin_manage_groups():
    global system_repo
    while True:
        clear_screen()
        print("--- Admin: Manage Groups ---")
        options = ["Add New Group", "View All Groups", "Delete Group"]
        display_menu(options)
        choice = get_choice(len(options))

        if choice == 1: # Add New Group
            group_name = input("Enter Group Name: ").strip()
            group_id = None # Let SQLite handle ID
            new_group = Group(group_id, group_name)
            success, msg, _ = system_repo.insert_one("groups", new_group) # Use repository
            if success:
                print(f"Group '{group_name}' added successfully.")
            else:
                print(f"Error: {msg}")
            input("Press Enter to continue...")

        elif choice == 2: # View All Groups
            print("\n--- All Groups ---")
            groups_to_display = system_repo.find_all("groups") # Use repository
            if groups_to_display:
                for group in groups_to_display:
                    # Dynamically get associated students and courses via repository
                    students_in_group = system_repo.find_all("users", {"role": "student"})
                    students_in_group_filtered = [s for s in students_in_group if system_repo.find_one("group_students", {"group_id": group.id, "student_id": s.id})] # Check linking table
                    student_names = [s.get_full_name() for s in students_in_group_filtered]

                    courses_in_group = system_repo.find_all("courses")
                    courses_in_group_filtered = [c for c in courses_in_group if system_repo.find_one("group_courses", {"group_id": group.id, "course_id": c.id})] # Check linking table
                    course_names = [c.name for c in courses_in_group_filtered]

                    print(f"ID: {group.id}, Name: {group.name}, Students: {', '.join(student_names) or 'None'}, Courses: {', '.join(course_names) or 'None'}")
            else:
                print("No groups found.")
            input("Press Enter to continue...")

        elif choice == 3: # Delete Group
            group_id_input = input("Enter ID of group to delete: ").strip()
            try:
                group_id_to_delete = int(group_id_input)
            except ValueError:
                print("Invalid ID. Please enter a number.")
                input("Press Enter to continue...")
                continue

            # Due to CASCADE DELETE rules in the DB, group_students and group_courses
            # linking records are handled automatically.
            if system_repo.delete_one("groups", group_id_to_delete): # Use repository
                print("Group deleted successfully.")
            else:
                print("Failed to delete group or group not found.")
            input("Press Enter to continue...")

        elif choice == 0:
            break

def admin_assign_lecturer():
    global system_repo
    while True:
        clear_screen()
        print("--- Admin: Assign Lecturer to Course ---")
        courses = system_repo.find_all("courses") # Use repository
        lecturers = system_repo.find_all("users", {"role": "lecturer"}) # Use repository

        if not courses:
            print("No courses available to assign lecturers to.")
            input("Press Enter to continue...")
            break
        if not lecturers:
            print("No lecturers available to assign.")
            input("Press Enter to continue...")
            break

        print("\nAvailable Courses:")
        for i, course in enumerate(courses, 1):
            current_lecturer = system_repo.find_one("users", {"id": course.lecturer_id}) # Use repository
            lecturer_info = current_lecturer.get_full_name() if current_lecturer else "Unassigned"
            print(f"{i}. {course.name} (Current Lecturer: {lecturer_info})")

        course_choice = get_choice(len(courses))
        if course_choice == 0:
            break
        selected_course = courses[course_choice - 1]

        print("\nAvailable Lecturers:")
        print("0. Unassign Lecturer") # Option to remove lecturer
        for i, lecturer in enumerate(lecturers, 1):
            print(f"{i}. {lecturer.get_full_name()}")

        lecturer_choice = get_choice(len(lecturers))

        if lecturer_choice == 0:
            if system_repo.update_one("courses", selected_course.id, {"lecturer_id": None}):
                print(f"Lecturer unassigned from '{selected_course.name}'.")
            else:
                print("Failed to unassign lecturer.")
        else:
            selected_lecturer = lecturers[lecturer_choice - 1]
            if system_repo.update_one("courses", selected_course.id, {"lecturer_id": selected_lecturer.id}):
                print(f"'{selected_lecturer.get_full_name()}' assigned to '{selected_course.name}'.")
            else:
                print("Failed to assign lecturer.")

        input("Press Enter to continue...")

def admin_assign_student_to_group():
    global system_repo
    while True:
        clear_screen()
        print("--- Admin: Assign Student to Group ---")
        students = system_repo.find_all("users", {"role": "student"}) # Use repository
        groups = system_repo.find_all("groups") # Use repository

        if not students:
            print("No students available.")
            input("Press Enter to continue...")
            break
        if not groups:
            print("No groups available.")
            input("Press Enter to continue...")
            break

        print("\nAvailable Students:")
        for i, student in enumerate(students, 1):
            # Check if student is already in a group for clearer UI
            student_groups = [g for g in groups if system_repo.find_one("group_students", {"group_id": g.id, "student_id": student.id})]
            group_names = ', '.join([g.name for g in student_groups])
            print(f"{i}. {student.get_full_name()} (Currently in: {group_names or 'None'})")
        student_choice = get_choice(len(students))
        if student_choice == 0:
            break
        selected_student = students[student_choice - 1]

        print("\nAvailable Groups:")
        for i, group in enumerate(groups, 1):
            print(f"{i}. {group.name}")
        group_choice = get_choice(len(groups))
        if group_choice == 0:
            break
        selected_group = groups[group_choice - 1]

        success, msg = system_repo.add_student_to_group(selected_group.id, selected_student.id)
        if success:
            print(f"'{selected_student.get_full_name()}' assigned to '{selected_group.name}'.")
        else:
            print(f"Error: {msg}")
        input("Press Enter to continue...")

def admin_assign_course_to_group():
    global system_repo
    while True:
        clear_screen()
        print("--- Admin: Assign Course to Group ---")
        courses = system_repo.find_all("courses") # Use repository
        groups = system_repo.find_all("groups") # Use repository

        if not courses:
            print("No courses available.")
            input("Press Enter to continue...")
            break
        if not groups:
            print("No groups available.")
            input("Press Enter to continue...")
            break

        print("\nAvailable Courses:")
        for i, course in enumerate(courses, 1):
            # Check if course is already assigned to a group for clearer UI
            course_groups = [g for g in groups if system_repo.find_one("group_courses", {"group_id": g.id, "course_id": course.id})]
            group_names = ', '.join([g.name for g in course_groups])
            print(f"{i}. {course.name} (Currently assigned to: {group_names or 'None'})")
        course_choice = get_choice(len(courses))
        if course_choice == 0:
            break
        selected_course = courses[course_choice - 1]

        print("\nAvailable Groups:")
        for i, group in enumerate(groups, 1):
            print(f"{i}. {group.name}")
        group_choice = get_choice(len(groups))
        if group_choice == 0:
            break
        selected_group = groups[group_choice - 1]

        success, msg = system_repo.add_course_to_group(selected_group.id, selected_course.id)
        if success:
            print(f"Course '{selected_course.name}' assigned to group '{selected_group.name}'.")
        else:
            print(f"Error: {msg}")
        input("Press Enter to continue...")

def admin_menu():
    while True:
        clear_screen()
        print("--- Administrator Dashboard ---")
        print(f"Welcome, {current_user.get_full_name()}!")
        options = [
            "Manage Users", "Manage Courses", "Manage Groups",
            "Assign Lecturers to Courses", "Assign Students to Groups", "Assign Courses to Groups"
        ]
        display_menu(options)
        choice = get_choice(len(options))

        if choice == 1:
            admin_manage_users()
        elif choice == 2:
            admin_manage_courses()
        elif choice == 3:
            admin_manage_groups()
        elif choice == 4:
            admin_assign_lecturer()
        elif choice == 5:
            admin_assign_student_to_group()
        elif choice == 6:
            admin_assign_course_to_group()
        elif choice == 0:
            break

# --- Lecturer services ---
def lecturer_enter_grade():
    global system_repo
    while True:
        clear_screen()
        print("--- Lecturer: Enter/Edit Grade ---")

        # Get courses assigned to this lecturer
        lecturer_courses = system_repo.find_all("courses", {"lecturer_id": current_user.id})

        if not lecturer_courses:
            print("You are not assigned to any courses.")
            input("Press Enter to continue...")
            return

        print("\nSelect a course:")
        for i, course in enumerate(lecturer_courses, 1):
            print(f"{i}. {course.name}")

        course_choice = get_choice(len(lecturer_courses))
        if course_choice == 0:
            break
        selected_course = lecturer_courses[course_choice - 1]

        # Find students enrolled in groups linked to this course
        students_in_course_ids = set()
        for group in system_repo.find_all("groups"): # Iterate all groups
            if system_repo.find_one("group_courses", {"group_id": group.id, "course_id": selected_course.id}): # Check if course is in this group
                # If course is in group, get students from that group
                group_students_links = system_repo.find_all("group_students", {"group_id": group.id})
                for link in group_students_links:
                    students_in_course_ids.add(link.get('student_id') or link.student_id) # Access by attribute or dict key

        students_in_course = []
        for student_id in students_in_course_ids:
            student_obj = system_repo.find_one("users", {"id": student_id, "role": "student"})
            if student_obj:
                students_in_course.append(student_obj)

        if not students_in_course:
            print(f"No students found for course '{selected_course.name}'.")
            input("Press Enter to continue...")
            continue

        print(f"\nStudents in '{selected_course.name}':")
        for i, student in enumerate(students_in_course, 1):
            grade_obj = system_repo.find_one("grades", {"student_id": student.id, "course_id": selected_course.id})
            current_grade = grade_obj.value if grade_obj else "N/A"
            print(f"{i}. {student.get_full_name()} (Current Grade: {current_grade})")

        student_choice = get_choice(len(students_in_course))
        if student_choice == 0:
            break
        selected_student = students_in_course[student_choice - 1]

        while True:
            try:
                grade_input = input(f"Enter grade for {selected_student.get_full_name()} in {selected_course.name} (0-100): ").strip()
                grade_value = float(grade_input)
                if not (0 <= grade_value <= 100):
                    print("Grade must be between 0 and 100.")
                else:
                    existing_grade = system_repo.find_one("grades", {"student_id": selected_student.id, "course_id": selected_course.id})
                    if existing_grade:
                        # Update existing grade
                        if system_repo.update_one("grades", existing_grade.id, {"value": grade_value}):
                            print("Grade updated successfully.")
                        else:
                            print("Failed to update grade.")
                    else:
                        # Insert new grade
                        new_grade = Grade(None, selected_student.id, selected_course.id, grade_value) # ID is None for new insert
                        success, msg, _ = system_repo.insert_one("grades", new_grade) # Use repository
                        if success:
                            print("Grade entered successfully.")
                        else:
                            print(f"Error: {msg}")
                    break
            except ValueError:
                print("Invalid input. Please enter a number for the grade.")
        input("Press Enter to continue...")

def lecturer_view_courses_and_students():
    global system_repo
    clear_screen()
    print("--- Lecturer: View My Courses and Students ---")

    lecturer_courses = system_repo.find_all("courses", {"lecturer_id": current_user.id})

    if not lecturer_courses:
        print("You are not assigned to any courses.")
        input("Press Enter to continue...")
        return

    for course_obj in lecturer_courses:
        print(f"\n--- Course: {course_obj.name} ---")

        student_ids_in_course = set()
        # Find all groups that this course is assigned to
        groups_for_this_course_links = system_repo.find_all("group_courses", {"course_id": course_obj.id})
        for link in groups_for_this_course_links:
            # Find all students in each of those groups
            students_in_group_links = system_repo.find_all("group_students", {"group_id": link.get('group_id') or link.group_id})
            for student_link in students_in_group_links:
                student_ids_in_course.add(student_link.get('student_id') or student_link.student_id)


        if not student_ids_in_course:
            print("No students enrolled in this course yet.")
            continue

        print("Enrolled Students:")
        students_found = False
        for student_id in student_ids_in_course:
            student_obj = system_repo.find_one("users", {"id": student_id, "role": "student"})
            if student_obj:
                grade_obj = system_repo.find_one("grades", {"student_id": student_id, "course_id": course_obj.id})
                grade_value = grade_obj.value if grade_obj else "N/A"
                print(f"  - {student_obj.get_full_name()} (Grade: {grade_value})")
                students_found = True

        if not students_found:
            print("No students associated with this course.")

    input("Press Enter to continue...")


def lecturer_menu():
    while True:
        clear_screen()
        print("--- Lecturer Dashboard ---")
        print(f"Welcome, {current_user.get_full_name()}!")
        options = ["Enter/Edit Grades", "View My Courses and Students"]
        display_menu(options)
        choice = get_choice(len(options))

        if choice == 1:
            lecturer_enter_grade()
        elif choice == 2:
            lecturer_view_courses_and_students()
        elif choice == 0:
            break

# --- Student services ---
def student_view_grades():
    global system_repo
    clear_screen()
    print("--- Student: View My Grades ---")

    my_grades = system_repo.find_all("grades", {"student_id": current_user.id})

    if not my_grades:
        print("No grades recorded for you yet.")
    else:
        print("\nYour Grades:")
        for grade_obj in my_grades:
            course = system_repo.find_one("courses", {"id": grade_obj.course_id})
            course_name = course.name if course else "Unknown Course"
            print(f"  - {course_name}: {grade_obj.value}")

    input("Press Enter to continue...")

def student_view_my_courses():
    global system_repo
    clear_screen()
    print("--- Student: View My Enrolled Courses ---")

    # Find all group_students links for the current student
    my_group_links = system_repo.find_all("group_students", {"student_id": current_user.id})

    if not my_group_links:
        print("You are not assigned to any groups, and therefore no courses.")
        input("Press Enter to continue...")
        return

    my_course_ids = set()
    for link in my_group_links:
        # For each group the student is in, find all courses assigned to that group
        group_id = link.get('group_id') or link.group_id
        course_links_in_group = system_repo.find_all("group_courses", {"group_id": group_id})
        for course_link in course_links_in_group:
            my_course_ids.add(course_link.get('course_id') or course_link.course_id)

    if not my_course_ids:
        print("You are not enrolled in any courses through your groups.")
        input("Press Enter to continue...")
        return

    print("\nYour Enrolled Courses:")
    for course_id in my_course_ids:
        course_obj = system_repo.find_one("courses", {"id": course_id})
        if course_obj:
            lecturer_info = "N/A"
            if course_obj.lecturer_id:
                lecturer_obj = system_repo.find_one("users", {"id": course_obj.lecturer_id, "role": "lecturer"})
                if lecturer_obj:
                    lecturer_info = lecturer_obj.get_full_name()
            print(f"- {course_obj.name} (Lecturer: {lecturer_info})")

    input("Press Enter to continue...")


def student_menu():
    while True:
        clear_screen()
        print("--- Student Dashboard ---")
        print(f"Welcome, {current_user.get_full_name()}!")
        options = ["View My Grades", "View My Enrolled Courses"]
        display_menu(options)
        choice = get_choice(len(options))

        if choice == 1:
            student_view_grades()
        elif choice == 2:
            student_view_my_courses()
        elif choice == 0:
            break

# --- Main Application Loop ---
def main():
    global system_repo # Declare that we're using the global system_repo
    system_repo = DatabaseRepository() # Instantiate the DatabaseRepository here

    # Pass the repository instance to the auth module's functions for setup
    auth.seed_initial_admin_if_needed(system_repo) # Pass repository for seeding

    while True:
        clear_screen()
        print("--- Academic System CLI ---")
        if current_user:
            print(f"Logged in as: {current_user.get_full_name()} ({current_user.get_role().capitalize()})")
            print("1. Go to Dashboard")
            print("2. Logout")
            print("0. Exit")
            choice = get_choice(2)

            if choice == 1:
                if current_user.get_role() == 'admin':
                    admin_menu()
                elif current_user.get_role() == 'lecturer':
                    lecturer_menu()
                elif current_user.get_role() == 'student':
                    student_menu()
            elif choice == 2:
                logout()
            elif choice == 0:
                print("Exiting Academic System. All data is saved in 'academic_system.db'.")
                break
        else:
            print("1. Login")
            print("0. Exit")
            choice = get_choice(1)

            if choice == 1:
                login()
            elif choice == 0:
                print("Exiting Academic System. All data is saved in 'academic_system.db'.")
                break

if __name__ == "__main__":
    main()