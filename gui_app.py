import tkinter as tk
from tkinter import messagebox, simpledialog
from database_repository import DatabaseRepository
from auth import hash_password, check_password, get_user_by_username
from models import Administrator, Lecturer, Student, User, Course, Group, Grade # Import User, Course, Group, Grade for general mapping

class AcademicSystemGUI:
    def __init__(self, master):
        self.master = master
        master.title("Academic System")
        master.geometry("400x300") # Set initial window size

        self.repo = DatabaseRepository()
        self.current_user = None

        self._create_login_widgets()

    def _clear_widgets(self):
        """Clears all widgets from the current window."""
        for widget in self.master.winfo_children():
            widget.destroy()

    def _create_login_widgets(self):
        """Creates the login screen widgets."""
        self._clear_widgets()

        self.login_frame = tk.Frame(self.master, padx=20, pady=20)
        self.login_frame.pack(expand=True)

        tk.Label(self.login_frame, text="Username:").grid(row=0, column=0, pady=5, sticky="w")
        self.username_entry = tk.Entry(self.login_frame, width=30)
        self.username_entry.grid(row=0, column=1, pady=5, padx=5)

        tk.Label(self.login_frame, text="Password:").grid(row=1, column=0, pady=5, sticky="w")
        self.password_entry = tk.Entry(self.login_frame, show="*", width=30)
        self.password_entry.grid(row=1, column=1, pady=5, padx=5)

        tk.Button(self.login_frame, text="Login", command=self._attempt_login).grid(row=2, column=1, pady=10, sticky="e")

        # Seed initial admin if needed (should only run once on first app launch)
        # This is here so that when you first run the GUI, the admin is created.
        # In a real app, you might have a separate setup script for this.
        self._seed_initial_admin_if_needed_gui()

    def _seed_initial_admin_if_needed_gui(self):
        """Seeds an initial admin user if the database is empty of admins."""
        admin_exists = self.repo.find_one("users", {"role": "admin"})
        if not admin_exists:
            username = "admin.user"
            password = "user"
            hashed_pw = hash_password(password)
            admin_user = Administrator(None, "Admin", "System", username, hashed_pw)
            success, msg, _ = self.repo.insert_one("users", admin_user)
            if success:
                messagebox.showinfo("Admin Created",
                                     f"Initial Administrator created:\nUsername: {username}\nPassword: {password}")
            else:
                messagebox.showerror("Admin Creation Failed", f"Could not create initial admin: {msg}")

    def _attempt_login(self):
        """Handles the login attempt."""
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        user_obj = get_user_by_username(self.repo, username)

        if user_obj and check_password(user_obj.password_hash, password):
            self.current_user = user_obj
            messagebox.showinfo("Login Success", f"Welcome, {self.current_user.get_full_name()}!")
            self._show_dashboard()
        else:
            messagebox.showerror("Login Failed", "Invalid username or password.")
            self.password_entry.delete(0, tk.END) # Clear password field

    def _show_dashboard(self):
        """Displays the appropriate dashboard based on the user's role."""
        self._clear_widgets()

        dashboard_frame = tk.Frame(self.master, padx=20, pady=20)
        dashboard_frame.pack(expand=True)

        tk.Label(dashboard_frame, text=f"Welcome, {self.current_user.get_full_name()} ({self.current_user.get_role().capitalize()})!", font=("Arial", 14, "bold")).pack(pady=10)

        if self.current_user.get_role() == "admin":
            self._create_admin_dashboard(dashboard_frame)
        elif self.current_user.get_role() == "lecturer":
            self._create_lecturer_dashboard(dashboard_frame)
        elif self.current_user.get_role() == "student":
            self._create_student_dashboard(dashboard_frame)
        
        tk.Button(dashboard_frame, text="Logout", command=self._logout).pack(pady=10)

    def _logout(self):
        """Logs out the current user and returns to the login screen."""
        self.current_user = None
        messagebox.showinfo("Logout", "You have been logged out.")
        self._create_login_widgets()

    # --- Admin Dashboard Functions ---
    def _create_admin_dashboard(self, parent_frame):
        tk.Button(parent_frame, text="Manage Users", command=self._admin_manage_users).pack(pady=5)
        tk.Button(parent_frame, text="Manage Courses", command=self._admin_manage_courses).pack(pady=5)
        tk.Button(parent_frame, text="Manage Groups", command=self._admin_manage_groups).pack(pady=5)
        # Add more admin buttons as you implement more features

    def _admin_manage_users(self):
        self._clear_widgets()
        manage_users_frame = tk.Frame(self.master, padx=20, pady=20)
        manage_users_frame.pack(expand=True, fill="both")

        tk.Label(manage_users_frame, text="Admin: Manage Users", font=("Arial", 12, "bold")).pack(pady=10)

        tk.Button(manage_users_frame, text="Add New User", command=self._admin_add_user_dialog).pack(pady=5)
        tk.Button(manage_users_frame, text="View All Users", command=self._admin_view_users).pack(pady=5)
        tk.Button(manage_users_frame, text="Delete User (by ID)", command=self._admin_delete_user_dialog).pack(pady=5)
        tk.Button(manage_users_frame, text="Back to Dashboard", command=self._show_dashboard).pack(pady=20) # Added

    def _admin_add_user_dialog(self):
        """Dialog to add a new user."""
        dialog = tk.Toplevel(self.master)
        dialog.title("Add New User")
        dialog.geometry("300x250")

        tk.Label(dialog, text="Name:").grid(row=0, column=0, pady=5, sticky="w")
        name_entry = tk.Entry(dialog)
        name_entry.grid(row=0, column=1, pady=5, padx=5)

        tk.Label(dialog, text="Surname:").grid(row=1, column=0, pady=5, sticky="w")
        surname_entry = tk.Entry(dialog)
        surname_entry.grid(row=1, column=1, pady=5, padx=5)

        tk.Label(dialog, text="Role:").grid(row=2, column=0, pady=5, sticky="w")
        role_var = tk.StringVar(dialog)
        role_var.set("student") # default value
        role_options = ["admin", "lecturer", "student"]
        role_menu = tk.OptionMenu(dialog, role_var, *role_options)
        role_menu.grid(row=2, column=1, pady=5, padx=5, sticky="ew")

        def save_user():
            name = name_entry.get().strip()
            surname = surname_entry.get().strip()
            role = role_var.get()

            if not name or not surname:
                messagebox.showerror("Input Error", "Name and Surname cannot be empty.", parent=dialog)
                return

            username = f"{name.lower()}.{surname.lower()}"
            password = surname.lower() # Automatic password
            hashed_password = hash_password(password)

            new_user = None
            if role == 'admin':
                new_user = Administrator(None, name, surname, username, hashed_password)
            elif role == 'lecturer':
                new_user = Lecturer(None, name, surname, username, hashed_password)
            elif role == 'student':
                new_user = Student(None, name, surname, username, hashed_password)
            else:
                messagebox.showerror("Error", "Invalid role selected.", parent=dialog)
                return

            success, msg, _ = self.repo.insert_one("users", new_user)
            if success:
                messagebox.showinfo("Success", f"Added {role}: {name} {surname}.\nUsername: {username}\nPassword: {password}", parent=dialog)
                dialog.destroy()
                self._admin_view_users() # Refresh user list
            else:
                messagebox.showerror("Error", f"Failed to add user: {msg}", parent=dialog)

        tk.Button(dialog, text="Add User", command=save_user).grid(row=3, column=1, pady=10, sticky="e")
        tk.Button(dialog, text="Cancel", command=dialog.destroy).grid(row=3, column=0, pady=10, sticky="w")


    def _admin_view_users(self):
        self._clear_widgets()
        view_users_frame = tk.Frame(self.master, padx=20, pady=20)
        view_users_frame.pack(expand=True, fill="both")

        tk.Label(view_users_frame, text="Admin: All Users", font=("Arial", 12, "bold")).pack(pady=10)

        # Create a Text widget to display users
        user_list_text = tk.Text(view_users_frame, wrap=tk.WORD, height=15, width=60)
        user_list_text.pack(pady=10)
        user_list_text.config(state=tk.DISABLED) # Make it read-only

        users = self.repo.find_all("users")
        if users:
            display_text = ""
            for user in users:
                display_text += f"ID: {user.id}, Name: {user.get_full_name()}, Username: {user.username}, Role: {user.get_role().capitalize()}\n"
            user_list_text.config(state=tk.NORMAL)
            user_list_text.delete(1.0, tk.END)
            user_list_text.insert(tk.END, display_text)
            user_list_text.config(state=tk.DISABLED)
        else:
            user_list_text.config(state=tk.NORMAL)
            user_list_text.delete(1.0, tk.END)
            user_list_text.insert(tk.END, "No users found.")
            user_list_text.config(state=tk.DISABLED)

        tk.Button(view_users_frame, text="Back to Manage Users", command=self._admin_manage_users).pack(pady=20)
        tk.Button(view_users_frame, text="Back to Dashboard", command=self._show_dashboard).pack(pady=5) # Added


    def _admin_delete_user_dialog(self):
        """Dialog to delete a user by ID."""
        user_id_str = simpledialog.askstring("Delete User", "Enter ID of user to delete:")
        if user_id_str:
            try:
                user_id_to_delete = int(user_id_str)
                user_obj = self.repo.find_one("users", {"id": user_id_to_delete})

                if not user_obj:
                    messagebox.showerror("Error", "User not found.")
                elif user_obj.get_role() == 'admin' and user_obj.username == 'admin.user':
                    messagebox.showerror("Error", "Cannot delete the primary administrator.")
                else:
                    if self.repo.delete_one("users", user_id_to_delete):
                        messagebox.showinfo("Success", "User deleted successfully.")
                        self._admin_view_users() # Refresh the list
                    else:
                        messagebox.showerror("Error", "Failed to delete user.")
            except ValueError:
                messagebox.showerror("Input Error", "Invalid ID. Please enter a number.")
            except Exception as e:
                messagebox.showerror("Error", f"An unexpected error occurred: {e}")

    def _admin_manage_courses(self):
        self._clear_widgets()
        manage_courses_frame = tk.Frame(self.master, padx=20, pady=20)
        manage_courses_frame.pack(expand=True, fill="both")

        tk.Label(manage_courses_frame, text="Admin: Manage Courses", font=("Arial", 12, "bold")).pack(pady=10)

        tk.Button(manage_courses_frame, text="Add New Course", command=self._admin_add_course_dialog).pack(pady=5)
        tk.Button(manage_courses_frame, text="View All Courses", command=self._admin_view_courses).pack(pady=5)
        tk.Button(manage_courses_frame, text="Delete Course (by ID)", command=self._admin_delete_course_dialog).pack(pady=5)
        tk.Button(manage_courses_frame, text="Assign Lecturer to Course", command=self._admin_assign_lecturer_dialog).pack(pady=5)
        tk.Button(manage_courses_frame, text="Back to Dashboard", command=self._show_dashboard).pack(pady=20) # Added

    def _admin_add_course_dialog(self):
        course_name = simpledialog.askstring("Add New Course", "Enter Course Name:")
        if course_name:
            course_name = course_name.strip()
            if not course_name:
                messagebox.showerror("Input Error", "Course name cannot be empty.")
                return

            new_course = Course(None, course_name)
            success, msg, _ = self.repo.insert_one("courses", new_course)
            if success:
                messagebox.showinfo("Success", f"Course '{course_name}' added successfully.")
                self._admin_view_courses() # Refresh course list
            else:
                messagebox.showerror("Error", f"Failed to add course: {msg}")

    def _admin_view_courses(self):
        self._clear_widgets()
        view_courses_frame = tk.Frame(self.master, padx=20, pady=20)
        view_courses_frame.pack(expand=True, fill="both")

        tk.Label(view_courses_frame, text="Admin: All Courses", font=("Arial", 12, "bold")).pack(pady=10)

        course_list_text = tk.Text(view_courses_frame, wrap=tk.WORD, height=15, width=60)
        course_list_text.pack(pady=10)
        course_list_text.config(state=tk.DISABLED)

        courses = self.repo.find_all("courses")
        if courses:
            display_text = ""
            for course in courses:
                lecturer_name = "N/A"
                if course.lecturer_id:
                    lecturer = self.repo.find_one("users", {"id": course.lecturer_id})
                    if lecturer:
                        lecturer_name = lecturer.get_full_name()
                display_text += f"ID: {course.id}, Name: {course.name}, Lecturer: {lecturer_name}\n"
            course_list_text.config(state=tk.NORMAL)
            course_list_text.delete(1.0, tk.END)
            course_list_text.insert(tk.END, display_text)
            course_list_text.config(state=tk.DISABLED)
        else:
            course_list_text.config(state=tk.NORMAL)
            course_list_text.delete(1.0, tk.END)
            course_list_text.insert(tk.END, "No courses found.")
            course_list_text.config(state=tk.DISABLED)

        tk.Button(view_courses_frame, text="Back to Manage Courses", command=self._admin_manage_courses).pack(pady=20)
        tk.Button(view_courses_frame, text="Back to Dashboard", command=self._show_dashboard).pack(pady=5) # Added

    def _admin_delete_course_dialog(self):
        course_id_str = simpledialog.askstring("Delete Course", "Enter ID of course to delete:")
        if course_id_str:
            try:
                course_id_to_delete = int(course_id_str)
                if self.repo.delete_one("courses", course_id_to_delete):
                    messagebox.showinfo("Success", "Course deleted successfully.")
                    self._admin_view_courses()
                else:
                    messagebox.showerror("Error", "Failed to delete course or course not found.")
            except ValueError:
                messagebox.showerror("Input Error", "Invalid ID. Please enter a number.")
            except Exception as e:
                messagebox.showerror("Error", f"An unexpected error occurred: {e}")

    def _admin_assign_lecturer_dialog(self):
        dialog = tk.Toplevel(self.master)
        dialog.title("Assign Lecturer to Course")
        dialog.geometry("400x300")

        courses = self.repo.find_all("courses")
        lecturers = self.repo.find_all("users", {"role": "lecturer"})

        if not courses:
            messagebox.showerror("Error", "No courses available to assign lecturers.", parent=dialog)
            dialog.destroy()
            return
        if not lecturers:
            messagebox.showerror("Error", "No lecturers available to assign.", parent=dialog)
            dialog.destroy()
            return

        tk.Label(dialog, text="Select Course:").pack(pady=5)
        course_names = [f"ID: {c.id} - {c.name}" for c in courses]
        course_var = tk.StringVar(dialog)
        course_var.set(course_names[0])
        course_menu = tk.OptionMenu(dialog, course_var, *course_names)
        course_menu.pack(pady=5, fill="x", padx=10)

        tk.Label(dialog, text="Select Lecturer:").pack(pady=5)
        lecturer_names = [f"ID: {l.id} - {l.get_full_name()}" for l in lecturers]
        lecturer_names.insert(0, "Unassign Lecturer (ID: 0)") # Option to unassign
        lecturer_var = tk.StringVar(dialog)
        lecturer_var.set(lecturer_names[0])
        lecturer_menu = tk.OptionMenu(dialog, lecturer_var, *lecturer_names)
        lecturer_menu.pack(pady=5, fill="x", padx=10)

        def assign():
            selected_course_str = course_var.get()
            selected_lecturer_str = lecturer_var.get()

            course_id = int(selected_course_str.split(" - ")[0].replace("ID: ", ""))
            
            if "Unassign" in selected_lecturer_str:
                lecturer_id = None # Special value for unassigning
            else:
                lecturer_id = int(selected_lecturer_str.split(" - ")[0].replace("ID: ", ""))

            success = self.repo.update_one("courses", course_id, {"lecturer_id": lecturer_id})
            if success:
                messagebox.showinfo("Success", "Assignment updated successfully.", parent=dialog)
                dialog.destroy()
                self._admin_view_courses() # Refresh view
            else:
                messagebox.showerror("Error", "Failed to update assignment.", parent=dialog)

        tk.Button(dialog, text="Assign", command=assign).pack(pady=10)
        tk.Button(dialog, text="Cancel", command=dialog.destroy).pack(pady=5)


    def _admin_manage_groups(self):
        self._clear_widgets()
        manage_groups_frame = tk.Frame(self.master, padx=20, pady=20)
        manage_groups_frame.pack(expand=True, fill="both")

        tk.Label(manage_groups_frame, text="Admin: Manage Groups", font=("Arial", 12, "bold")).pack(pady=10)

        tk.Button(manage_groups_frame, text="Add New Group", command=self._admin_add_group_dialog).pack(pady=5)
        tk.Button(manage_groups_frame, text="View All Groups", command=self._admin_view_groups).pack(pady=5)
        tk.Button(manage_groups_frame, text="Delete Group (by ID)", command=self._admin_delete_group_dialog).pack(pady=5)
        tk.Button(manage_groups_frame, text="Assign Student to Group", command=self._admin_assign_student_to_group_dialog).pack(pady=5)
        tk.Button(manage_groups_frame, text="Assign Course to Group", command=self._admin_assign_course_to_group_dialog).pack(pady=5)
        tk.Button(manage_groups_frame, text="Back to Dashboard", command=self._show_dashboard).pack(pady=20) # Added

    def _admin_add_group_dialog(self):
        group_name = simpledialog.askstring("Add New Group", "Enter Group Name:")
        if group_name:
            group_name = group_name.strip()
            if not group_name:
                messagebox.showerror("Input Error", "Group name cannot be empty.")
                return
            new_group = Group(None, group_name)
            success, msg, _ = self.repo.insert_one("groups", new_group)
            if success:
                messagebox.showinfo("Success", f"Group '{group_name}' added successfully.")
                self._admin_view_groups()
            else:
                messagebox.showerror("Error", f"Failed to add group: {msg}")

    def _admin_view_groups(self):
        self._clear_widgets()
        view_groups_frame = tk.Frame(self.master, padx=20, pady=20)
        view_groups_frame.pack(expand=True, fill="both")

        tk.Label(view_groups_frame, text="Admin: All Groups", font=("Arial", 12, "bold")).pack(pady=10)

        group_list_text = tk.Text(view_groups_frame, wrap=tk.WORD, height=15, width=60)
        group_list_text.pack(pady=10)
        group_list_text.config(state=tk.DISABLED)

        groups = self.repo.find_all("groups")
        if groups:
            display_text = ""
            for group in groups:
                # Need to refresh group object from repo to get updated student/course lists
                full_group = self.repo.find_one("groups", {"id": group.id}) # Re-fetch to get linked IDs
                student_names = []
                for s_id in full_group.student_ids:
                    s = self.repo.find_one("users", {"id": s_id})
                    if s: student_names.append(s.get_full_name())
                
                course_names = []
                for c_id in full_group.course_ids:
                    c = self.repo.find_one("courses", {"id": c_id})
                    if c: course_names.append(c.name)

                display_text += f"ID: {group.id}, Name: {group.name}\n" \
                                f"   Students: {', '.join(student_names) or 'None'}\n" \
                                f"   Courses: {', '.join(course_names) or 'None'}\n\n"
            group_list_text.config(state=tk.NORMAL)
            group_list_text.delete(1.0, tk.END)
            group_list_text.insert(tk.END, display_text)
            group_list_text.config(state=tk.DISABLED)
        else:
            group_list_text.config(state=tk.NORMAL)
            group_list_text.delete(1.0, tk.END)
            group_list_text.insert(tk.END, "No groups found.")
            group_list_text.config(state=tk.DISABLED)

        tk.Button(view_groups_frame, text="Back to Manage Groups", command=self._admin_manage_groups).pack(pady=20)
        tk.Button(view_groups_frame, text="Back to Dashboard", command=self._show_dashboard).pack(pady=5) # Added


    def _admin_delete_group_dialog(self):
        group_id_str = simpledialog.askstring("Delete Group", "Enter ID of group to delete:")
        if group_id_str:
            try:
                group_id_to_delete = int(group_id_str)
                if self.repo.delete_one("groups", group_id_to_delete):
                    messagebox.showinfo("Success", "Group deleted successfully.")
                    self._admin_view_groups()
                else:
                    messagebox.showerror("Error", "Failed to delete group or group not found.")
            except ValueError:
                messagebox.showerror("Input Error", "Invalid ID. Please enter a number.")
            except Exception as e:
                messagebox.showerror("Error", f"An unexpected error occurred: {e}")

    def _admin_assign_student_to_group_dialog(self):
        dialog = tk.Toplevel(self.master)
        dialog.title("Assign Student to Group")
        dialog.geometry("400x300")

        students = self.repo.find_all("users", {"role": "student"})
        groups = self.repo.find_all("groups")

        if not students:
            messagebox.showerror("Error", "No students available.", parent=dialog)
            dialog.destroy()
            return
        if not groups:
            messagebox.showerror("Error", "No groups available.", parent=dialog)
            dialog.destroy()
            return
        
        tk.Label(dialog, text="Select Student:").pack(pady=5)
        student_names = [f"ID: {s.id} - {s.get_full_name()}" for s in students]
        student_var = tk.StringVar(dialog)
        student_var.set(student_names[0])
        student_menu = tk.OptionMenu(dialog, student_var, *student_names)
        student_menu.pack(pady=5, fill="x", padx=10)

        tk.Label(dialog, text="Select Group:").pack(pady=5)
        group_names = [f"ID: {g.id} - {g.name}" for g in groups]
        group_var = tk.StringVar(dialog)
        group_var.set(group_names[0])
        group_menu = tk.OptionMenu(dialog, group_var, *group_names)
        group_menu.pack(pady=5, fill="x", padx=10)

        def assign():
            selected_student_str = student_var.get()
            selected_group_str = group_var.get()

            student_id = int(selected_student_str.split(" - ")[0].replace("ID: ", ""))
            group_id = int(selected_group_str.split(" - ")[0].replace("ID: ", ""))

            success, msg = self.repo.add_student_to_group(group_id, student_id)
            if success:
                messagebox.showinfo("Success", f"Student assigned to group: {msg}", parent=dialog)
                dialog.destroy()
                self._admin_view_groups() # Refresh view
            else:
                messagebox.showerror("Error", f"Failed to assign student: {msg}", parent=dialog)

        tk.Button(dialog, text="Assign", command=assign).pack(pady=10)
        tk.Button(dialog, text="Cancel", command=dialog.destroy).pack(pady=5)

    def _admin_assign_course_to_group_dialog(self):
        dialog = tk.Toplevel(self.master)
        dialog.title("Assign Course to Group")
        dialog.geometry("400x300")

        courses = self.repo.find_all("courses")
        groups = self.repo.find_all("groups")

        if not courses:
            messagebox.showerror("Error", "No courses available.", parent=dialog)
            dialog.destroy()
            return
        if not groups:
            messagebox.showerror("Error", "No groups available.", parent=dialog)
            dialog.destroy()
            return
        
        tk.Label(dialog, text="Select Course:").pack(pady=5)
        course_names = [f"ID: {c.id} - {c.name}" for c in courses]
        course_var = tk.StringVar(dialog)
        course_var.set(course_names[0])
        course_menu = tk.OptionMenu(dialog, course_var, *course_names)
        course_menu.pack(pady=5, fill="x", padx=10)

        tk.Label(dialog, text="Select Group:").pack(pady=5)
        group_names = [f"ID: {g.id} - {g.name}" for g in groups]
        group_var = tk.StringVar(dialog)
        group_var.set(group_names[0])
        group_menu = tk.OptionMenu(dialog, group_var, *group_names)
        group_menu.pack(pady=5, fill="x", padx=10)

        def assign():
            selected_course_str = course_var.get()
            selected_group_str = group_var.get()

            course_id = int(selected_course_str.split(" - ")[0].replace("ID: ", ""))
            group_id = int(selected_group_str.split(" - ")[0].replace("ID: ", ""))

            success, msg = self.repo.add_course_to_group(group_id, course_id)
            if success:
                messagebox.showinfo("Success", f"Course assigned to group: {msg}", parent=dialog)
                dialog.destroy()
                self._admin_view_groups() # Refresh view
            else:
                messagebox.showerror("Error", f"Failed to assign course: {msg}", parent=dialog)

        tk.Button(dialog, text="Assign", command=assign).pack(pady=10)
        tk.Button(dialog, text="Cancel", command=dialog.destroy).pack(pady=5)

    # --- Lecturer Dashboard Functions ---
    def _create_lecturer_dashboard(self, parent_frame):
        tk.Button(parent_frame, text="Enter/Edit Grades", command=self._lecturer_enter_grade_dialog).pack(pady=5)
        tk.Button(parent_frame, text="View My Courses & Students", command=self._lecturer_view_courses_and_students).pack(pady=5)
        # Add more lecturer buttons

    def _lecturer_enter_grade_dialog(self):
        dialog = tk.Toplevel(self.master)
        dialog.title("Enter/Edit Grade")
        dialog.geometry("400x350")

        lecturer_courses = self.repo.find_all("courses", {"lecturer_id": self.current_user.id})
        if not lecturer_courses:
            messagebox.showerror("Error", "You are not assigned to any courses.", parent=dialog)
            dialog.destroy()
            return

        tk.Label(dialog, text="Select Course:").pack(pady=5)
        course_display_names = [f"ID: {c.id} - {c.name}" for c in lecturer_courses]
        course_var = tk.StringVar(dialog)
        course_var.set(course_display_names[0])
        course_menu = tk.OptionMenu(dialog, course_var, *course_display_names)
        course_menu.pack(pady=5, fill="x", padx=10)

        students_for_selected_course = [] # Will be populated dynamically

        tk.Label(dialog, text="Select Student:").pack(pady=5)
        student_var = tk.StringVar(dialog)
        student_menu = tk.OptionMenu(dialog, student_var, "") # Empty initially
        student_menu.pack(pady=5, fill="x", padx=10)

        tk.Label(dialog, text="Grade (0-100):").pack(pady=5)
        grade_entry = tk.Entry(dialog)
        grade_entry.pack(pady=5, fill="x", padx=10)

        def update_students_dropdown(*args):
            selected_course_id = int(course_var.get().split(" - ")[0].replace("ID: ", ""))
            
            # Find students for this course via groups
            students_in_course_ids = set()
            for group in self.repo.find_all("groups"):
                # Check if this group is associated with the selected course
                group_course_link = self.repo.find_one("group_courses", {"group_id": group.id, "course_id": selected_course_id})
                if group_course_link:
                    # If the group is linked to the course, find all students in that group
                    group_students_links = self.repo.find_all("group_students", {"group_id": group.id})
                    for link in group_students_links:
                        # Ensure 'student_id' attribute exists, if not, try direct dict key
                        students_in_course_ids.add(link.get('student_id') if isinstance(link, dict) else link.student_id)
            
            nonlocal students_for_selected_course
            students_for_selected_course = []
            for student_id in students_in_course_ids:
                student_obj = self.repo.find_one("users", {"id": student_id, "role": "student"})
                if student_obj:
                    students_for_selected_course.append(student_obj)

            student_display_names = []
            if students_for_selected_course:
                for student in students_for_selected_course:
                    grade_obj = self.repo.find_one("grades", {"student_id": student.id, "course_id": selected_course_id})
                    current_grade = grade_obj.value if grade_obj else "N/A"
                    student_display_names.append(f"ID: {student.id} - {student.get_full_name()} (Current: {current_grade})")
                student_var.set(student_display_names[0])
            else:
                student_var.set("No students for this course")
            
            student_menu['menu'].delete(0, 'end')
            for name in student_display_names:
                student_menu['menu'].add_command(label=name, command=tk._set_menu_value(student_var, name))
            
            if not students_for_selected_course:
                grade_entry.delete(0, tk.END) # Clear grade entry if no students
                grade_entry.config(state=tk.DISABLED) # Disable grade entry
            else:
                grade_entry.config(state=tk.NORMAL)


        course_var.trace("w", update_students_dropdown)
        update_students_dropdown() # Initial call to populate students dropdown

        def save_grade():
            if not students_for_selected_course or student_var.get() == "No students for this course":
                messagebox.showerror("Error", "No student selected or available.", parent=dialog)
                return

            selected_course_id = int(course_var.get().split(" - ")[0].replace("ID: ", ""))
            selected_student_id = int(student_var.get().split(" - ")[0].replace("ID: ", ""))
            
            try:
                grade_value = float(grade_entry.get().strip())
                if not (0 <= grade_value <= 100):
                    messagebox.showerror("Input Error", "Grade must be between 0 and 100.", parent=dialog)
                    return
            except ValueError:
                messagebox.showerror("Input Error", "Please enter a valid number for the grade.", parent=dialog)
                return
            
            existing_grade = self.repo.find_one("grades", {"student_id": selected_student_id, "course_id": selected_course_id})
            if existing_grade:
                success = self.repo.update_one("grades", existing_grade.id, {"value": grade_value})
                if success:
                    messagebox.showinfo("Success", "Grade updated successfully.", parent=dialog)
                    update_students_dropdown() # Refresh current grades in dropdown
                else:
                    messagebox.showerror("Error", "Failed to update grade.", parent=dialog)
            else:
                new_grade = Grade(None, selected_student_id, selected_course_id, grade_value)
                success, msg, _ = self.repo.insert_one("grades", new_grade)
                if success:
                    messagebox.showinfo("Success", "Grade entered successfully.", parent=dialog)
                    update_students_dropdown() # Refresh current grades in dropdown
                else:
                    messagebox.showerror("Error", f"Failed to enter grade: {msg}", parent=dialog)

        tk.Button(dialog, text="Save Grade", command=save_grade).pack(pady=10)
        tk.Button(dialog, text="Back to Dashboard", command=lambda: [dialog.destroy(), self._show_dashboard()]).pack(pady=5) # Added

    def _lecturer_view_courses_and_students(self):
        self._clear_widgets()
        view_frame = tk.Frame(self.master, padx=20, pady=20)
        view_frame.pack(expand=True, fill="both")

        tk.Label(view_frame, text=f"Lecturer: My Courses and Students", font=("Arial", 12, "bold")).pack(pady=10)

        info_text = tk.Text(view_frame, wrap=tk.WORD, height=20, width=80)
        info_text.pack(pady=10)
        info_text.config(state=tk.DISABLED)

        lecturer_courses = self.repo.find_all("courses", {"lecturer_id": self.current_user.id})
        
        display_content = ""
        if lecturer_courses:
            for course in lecturer_courses:
                display_content += f"Course ID: {course.id}, Name: {course.name}\n"
                display_content += "  Assigned Groups & Students:\n"

                students_in_course_ids = set()
                groups_for_course = self.repo.find_all("group_courses", {"course_id": course.id})
                
                if groups_for_course:
                    for gc_link in groups_for_course:
                        group_obj = self.repo.find_one("groups", {"id": gc_link.group_id})
                        if group_obj:
                            display_content += f"    - Group ID: {group_obj.id}, Name: {group_obj.name}\n"
                            
                            students_in_group_links = self.repo.find_all("group_students", {"group_id": group_obj.id})
                            if students_in_group_links:
                                display_content += "      Students:\n"
                                for gs_link in students_in_group_links:
                                    student = self.repo.find_one("users", {"id": gs_link.student_id, "role": "student"})
                                    if student:
                                        students_in_course_ids.add(student.id) # Track unique students in this course
                                        grade = self.repo.find_one("grades", {"student_id": student.id, "course_id": course.id})
                                        grade_val = grade.value if grade else "N/A"
                                        display_content += f"        - ID: {student.id}, {student.get_full_name()} (Grade: {grade_val})\n"
                            else:
                                display_content += "      No students in this group.\n"
                else:
                    display_content += "    No groups assigned to this course.\n"
                display_content += "\n" # Add a newline for separation between courses
        else:
            display_content = "You are not assigned to any courses."
        
        info_text.config(state=tk.NORMAL)
        info_text.delete(1.0, tk.END)
        info_text.insert(tk.END, display_content)
        info_text.config(state=tk.DISABLED)

        tk.Button(view_frame, text="Back to Dashboard", command=self._show_dashboard).pack(pady=20) # Added

    # --- Student Dashboard Functions ---
    def _create_student_dashboard(self, parent_frame):
        tk.Button(parent_frame, text="View My Courses & Grades", command=self._student_view_courses_and_grades).pack(pady=5)
        tk.Button(parent_frame, text="View My Groups", command=self._student_view_my_groups).pack(pady=5)
        # Add more student buttons

    def _student_view_courses_and_grades(self):
        self._clear_widgets()
        view_frame = tk.Frame(self.master, padx=20, pady=20)
        view_frame.pack(expand=True, fill="both")

        tk.Label(view_frame, text=f"Student: My Courses and Grades", font=("Arial", 12, "bold")).pack(pady=10)

        info_text = tk.Text(view_frame, wrap=tk.WORD, height=15, width=60)
        info_text.pack(pady=10)
        info_text.config(state=tk.DISABLED)

        student_id = self.current_user.id
        
        # Find all groups the student belongs to
        student_groups_links = self.repo.find_all("group_students", {"student_id": student_id})
        
        courses_attended_ids = set()
        for gs_link in student_groups_links:
            group_id = gs_link.group_id
            course_group_links = self.repo.find_all("group_courses", {"group_id": group_id})
            for gc_link in course_group_links:
                courses_attended_ids.add(gc_link.course_id)
        
        display_content = ""
        if courses_attended_ids:
            for course_id in courses_attended_ids:
                course = self.repo.find_one("courses", {"id": course_id})
                if course:
                    grade_obj = self.repo.find_one("grades", {"student_id": student_id, "course_id": course_id})
                    grade_value = grade_obj.value if grade_obj else "N/A"
                    
                    lecturer_name = "N/A"
                    if course.lecturer_id:
                        lecturer = self.repo.find_one("users", {"id": course.lecturer_id, "role": "lecturer"})
                        if lecturer:
                            lecturer_name = lecturer.get_full_name()

                    display_content += f"Course: {course.name} (Lecturer: {lecturer_name})\n"
                    display_content += f"  Grade: {grade_value}\n\n"
        else:
            display_content = "You are not enrolled in any courses yet."

        info_text.config(state=tk.NORMAL)
        info_text.delete(1.0, tk.END)
        info_text.insert(tk.END, display_content)
        info_text.config(state=tk.DISABLED)

        tk.Button(view_frame, text="Back to Dashboard", command=self._show_dashboard).pack(pady=20) # Added

    def _student_view_my_groups(self):
        self._clear_widgets()
        view_frame = tk.Frame(self.master, padx=20, pady=20)
        view_frame.pack(expand=True, fill="both")

        tk.Label(view_frame, text=f"Student: My Groups", font=("Arial", 12, "bold")).pack(pady=10)

        info_text = tk.Text(view_frame, wrap=tk.WORD, height=15, width=60)
        info_text.pack(pady=10)
        info_text.config(state=tk.DISABLED)

        student_id = self.current_user.id
        
        # Find all groups the student belongs to
        student_groups_links = self.repo.find_all("group_students", {"student_id": student_id})
        
        display_content = ""
        if student_groups_links:
            for gs_link in student_groups_links:
                group = self.repo.find_one("groups", {"id": gs_link.group_id})
                if group:
                    display_content += f"Group ID: {group.id}, Name: {group.name}\n"
                    display_content += "  Courses in this Group:\n"
                    
                    group_courses_links = self.repo.find_all("group_courses", {"group_id": group.id})
                    if group_courses_links:
                        for gc_link in group_courses_links:
                            course = self.repo.find_one("courses", {"id": gc_link.course_id})
                            if course:
                                display_content += f"    - {course.name}\n"
                    else:
                        display_content += "    No courses assigned to this group.\n"
                    display_content += "\n" # Add a newline for separation between groups
        else:
            display_content = "You are not part of any groups yet."

        info_text.config(state=tk.NORMAL)
        info_text.delete(1.0, tk.END)
        info_text.insert(tk.END, display_content)
        info_text.config(state=tk.DISABLED)

        tk.Button(view_frame, text="Back to Dashboard", command=self._show_dashboard).pack(pady=20) # Added

# End of GUI class (assuming main loop follows)

# --- Main application execution ---
if __name__ == "__main__":
    root = tk.Tk()
    app = AcademicSystemGUI(root)
    root.mainloop()




