import tkinter as tk
import sqlite3
from tkinter import ttk, filedialog, messagebox, simpledialog

from database import create_database
from incident_diagram_visualizer import IncidentDiagramVisualizer
from playbook_parser import PlaybookParser
from auth import Authenticator


class AddIncidentForm(tk.Toplevel):
    def __init__(self, master, db_connection, parent_app):
        super().__init__(master)
        self.master = master
        self.db_connection = db_connection
        self.parent_app = parent_app
        self.title("Add New Incident")
        self.geometry("500x350")
        self.labels = ['Incident Name', 'Preparation', 'Detection', 'Response', 'Criticality', 'Criticality Description']
        self.entries = {}
        self.init_ui()

    def init_ui(self):
        for idx, label in enumerate(self.labels):
            lbl = ttk.Label(self, text=label)
            lbl.grid(row=idx, column=0, padx=10, pady=5, sticky="e")
            if label == 'Criticality':
                entry = ttk.Combobox(self, values=['Low', 'Medium', 'High', 'Critical'])
            else:
                entry = ttk.Entry(self, width=50)
            entry.grid(row=idx, column=1, padx=10, pady=5, sticky="w")
            self.entries[label] = entry

        next_incident_number = self.get_next_incident_number()
        self.entries['Incident Name'].insert(0, f"{next_incident_number}: ")

        submit_button = ttk.Button(self, text="Submit", command=self.submit_incident)
        submit_button.grid(row=len(self.labels), column=1, pady=10)

    def get_next_incident_number(self):
        cursor = self.db_connection.cursor()
        cursor.execute("SELECT incident_title FROM playbooks ORDER BY id DESC LIMIT 1")
        last_incident = cursor.fetchone()
        cursor.close()
        if last_incident:
            last_number = int(last_incident[0].split(':')[0])
            return last_number + 1
        return 1

    def submit_incident(self):
        data = {label: self.entries[label].get() for label in self.labels}
        if not all(data.values()):
            messagebox.showerror("Error", "All fields must be provided!")
            return
        self.insert_procedure(data)
        self.destroy()

    def insert_procedure(self, data):
        conn = self.db_connection
        cursor = conn.cursor()
        try:
            cursor.execute(
                'INSERT INTO playbooks (incident_title, steps, category, criticality, criticality_description) VALUES (?, ?, ?, ?, ?)',
                (data['Incident Name'],
                 f"Preparation: {data['Preparation']}\nDetection: {data['Detection']}\nResponse: {data['Response']}",
                 "Default Category",
                 data['Criticality'],
                 data['Criticality Description']))
            conn.commit()
            messagebox.showinfo("Success", "Incident added successfully")
            self.parent_app.update_incidents_listbox()
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            conn.close()


class LoginForm(tk.Toplevel):
    def __init__(self, master, db_connection, parent_app, authenticator):
        super().__init__(master)
        self.master = master
        self.db_connection = db_connection
        self.parent_app = parent_app
        self.authenticator = authenticator
        self.title("Login")
        self.geometry("500x350")
        self.labels = ['Username', 'Password']
        self.entries = {}
        self.init_ui()

    def init_ui(self):
        for idx, label in enumerate(self.labels):
            lbl = ttk.Label(self, text=label)
            lbl.grid(row=idx, column=0, padx=10, pady=5, sticky="e")
            entry = ttk.Entry(self, width=20, show="*" if label == "Password" else None)
            entry.grid(row=idx, column=1, padx=10, pady=5, sticky="w")
            self.entries[label] = entry

        login_button = ttk.Button(self, text="Login", command=self.login)
        login_button.grid(row=len(self.labels), column=1, pady=10)

    def login(self):
        username = self.entries['Username'].get()
        password = self.entries['Password'].get()
        if self.authenticator.authenticate(username, password):
            messagebox.showinfo("Login Successful", "You have successfully logged in.")
            self.destroy()
        else:
            messagebox.showerror("Login Failed", "Incorrect username or password")
        self.destroy()


class EditIncidentForm(tk.Toplevel):
    def __init__(self, master, db_connection, parent_app, incident_id, existing_details):
        super().__init__(master)
        self.master = master
        self.db_connection = db_connection
        self.parent_app = parent_app
        self.incident_id = incident_id
        self.existing_details = existing_details
        self.title("Edit Incident")
        self.geometry("500x350")
        self.labels = ['Incident Name', 'Preparation', 'Detection', 'Response', 'Criticality',
                       'Criticality Description']
        self.entries = {}
        self.init_ui()

    def init_ui(self):
        for idx, label in enumerate(self.labels):
            lbl = ttk.Label(self, text=label)
            lbl.grid(row=idx, column=0, padx=10, pady=5, sticky="e")
            if label == 'Criticality':
                entry = ttk.Combobox(self, values=['Low', 'Medium', 'High', 'Critical'])
            else:
                entry = ttk.Entry(self, width=50)
            entry.grid(row=idx, column=1, padx=10, pady=5, sticky="w")
            self.entries[label] = entry

        self.entries['Incident Name'].insert(0, self.existing_details[0])

        steps = self.existing_details[1].split('\n')
        preparation, detection, response = '', '', ''

        for step in steps:
            if step.startswith('Preparation:'):
                preparation = step.replace('Preparation: ', '').strip()
            elif step.startswith('Detection:'):
                detection = step.replace('Detection: ', '').strip()
            elif step.startswith('Response:'):
                response = step.replace('Response: ', '').strip()

        self.entries['Preparation'].insert(0, preparation)
        self.entries['Detection'].insert(0, detection)
        self.entries['Response'].insert(0, response)

        self.entries['Criticality'].insert(0, self.existing_details[3])
        self.entries['Criticality Description'].insert(0, self.existing_details[4])

        submit_button = ttk.Button(self, text="Submit", command=self.submit_edit)
        submit_button.grid(row=len(self.labels), column=1, pady=10)

    def submit_edit(self):
        data = {label: self.entries[label].get() for label in self.labels}
        if not all(data.values()):
            messagebox.showerror("Error", "All fields must be filled out")
            return

        conn = self.db_connection
        cursor = conn.cursor()
        cursor.execute('''UPDATE playbooks SET 
                          incident_title = ?, 
                          steps = ?, 
                          criticality = ?, 
                          criticality_description = ?
                          WHERE id = ?''',
                       (data['Incident Name'],
                        f"Preparation: {data['Preparation']}\nDetection: {data['Detection']}\nResponse: {data['Response']}",
                        data['Criticality'],
                        data['Criticality Description'],
                        self.incident_id))
        conn.commit()
        self.parent_app.update_incidents_listbox()
        self.destroy()


class HelpScreen(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Help")
        self.geometry("600x400")
        self.init_ui()

    def init_ui(self):
        help_text = (
            "Welcome to the Playbook Visualizer Application!\n\n"
            "This application allows you to upload, visualize, and manage cybersecurity playbooks.\n\n"
            "Upload Document Format:\n"
            "1. The document must be in plain text format.\n"
            "2. The document should include sections for Preparation, Detection, and Response.\n"
            "3. The document should also include a section for Criticality and Criticality Description\n"
            "4. Each section should be clearly labeled and contain relevant information.\n\n"
            "Example Format:\n"
            "Incident X: Incident Title\n"
            "Preparation: Details about preparation.\n"
            "Detection: Details about detection.\n"
            "Response: Details about response.\n"
            "Criticality: Low, Medium, High, Critical\n"
            "Criticality Description: Description/Details about criticality\n\n"
            "For more information, reach out to me from github: https://github.com/keremalpdag"
        )
        label = tk.Label(self, text=help_text, justify=tk.LEFT, padx=10, pady=10)
        label.pack(expand=True, fill='both')


class PlaybookVisualizerApp:
    def __init__(self, root):
        self.root = root
        self.parser = PlaybookParser()
        self.auth = Authenticator()
        self.diagram_visualizer = IncidentDiagramVisualizer(root)

        root.title("PlaybookVisualizer")

        window_width = 800
        window_height = 600

        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()

        center_x = int((screen_width / 2) - (window_width / 2))
        center_y = int((screen_height / 2) - (window_height / 2))

        root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y - 30}')

        self.title_frame = ttk.Frame(root)
        self.title_frame.pack(fill=tk.X, padx=10, pady=5)
        self.title_label = ttk.Label(self.title_frame, text="PlaybookVisualizer", font=("Arial", 16))
        self.title_label.pack()

        self.input_frame = ttk.Frame(root)
        self.input_frame.pack(fill=tk.X, padx=10, pady=5)
        self.input_label = ttk.Label(self.input_frame, text="Upload Playbook:")
        self.input_label.pack(side=tk.LEFT)

        self.upload_button = ttk.Button(self.input_frame, text="Upload", command=self.upload_playbook)
        self.upload_button.pack(side=tk.LEFT, padx=10)

        self.category_frame = ttk.Frame(root)
        self.category_frame.pack(fill=tk.X, padx=10, pady=5)
        categories = ["All", "Fraud & Abuse", "Network Security", "Software & Firmware", "Physical Security",
                      "Data Security", "Other"]
        for category in categories:
            button = ttk.Button(self.category_frame, text=category,
                                command=lambda c=category: self.filter_by_category(c))
            button.pack(side=tk.LEFT, padx=2)

        self.search_frame = ttk.Frame(root)
        self.search_frame.pack(fill=tk.X, padx=10, pady=5)
        self.search_label = ttk.Label(self.search_frame, text="Search Incident:")
        self.search_label.pack(side=tk.LEFT)
        self.search_entry = ttk.Entry(self.search_frame)
        self.search_entry.pack(fill=tk.X, expand=True, side=tk.LEFT)
        self.search_entry.bind("<KeyRelease>", self.filter_incidents)

        self.incident_frame = ttk.Frame(root)
        self.incident_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.incidents_listbox = tk.Listbox(self.incident_frame)
        self.incidents_listbox.pack(fill=tk.BOTH, expand=True)
        self.incidents_listbox.bind("<Button-3>", self.show_context_menu)

        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Delete", command=self.delete_incident)
        self.context_menu.add_command(label="Edit", command=self.open_edit_incident_form)

        self.view_button = ttk.Button(root, text="View Selected Incident", command=self.view_incident_details)
        self.view_button.pack(pady=5)

        self.incident_count_label = ttk.Label(root, text="Total Incidents: 0", font=("Arial", 14))
        self.incident_count_label.pack(side=tk.BOTTOM, fill=tk.X)

        self.update_incidents_listbox()

        self.help_button = ttk.Button(self.input_frame, text="Help", command=self.open_help_screen)
        self.help_button.pack(side=tk.RIGHT, padx=10)

        self.reset_button = ttk.Button(self.input_frame, text="Reset All", command=self.delete_all_incidents)
        self.reset_button.pack(side=tk.RIGHT, padx=10)

        self.add_button = ttk.Button(self.input_frame, text="Add Incident Procedure",
                                     command=self.open_add_incident_form)
        self.add_button.pack(side=tk.RIGHT, padx=10)

        self.login_button = ttk.Button(self.input_frame, text="Login", command=self.open_login_form)
        self.login_button.pack(side=tk.RIGHT, padx=10)



    def open_help_screen(self):
        HelpScreen(self.root)

    def open_login_form(self):
        db_connection = self.get_db_connection()
        authenticator = self.auth
        LoginForm(self.root, db_connection, self, authenticator)

    def open_add_incident_form(self):
        if self.auth.is_authenticated:
            db_connection = self.get_db_connection()
            AddIncidentForm(self.root, db_connection, self)
        else:
            messagebox.showerror("Authentication Required", "You must be logged in to perform this action.")

    def get_db_connection(self):
        return sqlite3.connect('playbook_visualizer.db')

    def delete_all_incidents(self):
        if self.auth.is_authenticated:
            if messagebox.askyesno("Confirm",
                                   "Are you sure you want to delete all incidents? This action cannot be undone."):

                conn = self.get_db_connection()
                cursor = conn.cursor()
                cursor.execute('DELETE FROM playbooks')
                conn.commit()
                conn.close()

                self.incidents_listbox.delete(0, tk.END)
                messagebox.showinfo("Reset Complete", "All incidents have been deleted.")
                self.update_incident_count()
        else:
            messagebox.showerror("Authentication Required", "You must be logged in to perform this action.")
            input_username = simpledialog.askstring("Username", "Enter Username")
            input_password = simpledialog.askstring("Password", "Enter Password:", show='*')
            if self.auth.authenticate(input_username, input_password):
                tk.messagebox.showinfo("Authentication", "Authentication successful!")
            else:
                tk.messagebox.showerror("Authentication", "Authentication failed!")
                return

    def show_context_menu(self, event):
        try:
            self.incidents_listbox.selection_clear(0, tk.END)
            self.incidents_listbox.selection_set(self.incidents_listbox.nearest(event.y))
            self.context_menu.post(event.x_root, event.y_root)
        except Exception as e:
            print(e)

    def open_edit_incident_form(self):
        selection_index = self.incidents_listbox.curselection()
        if not selection_index:
            messagebox.showinfo("Selection Error", "No incident selected.")
            return
        selected_incident_title = self.incidents_listbox.get(selection_index)
        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, incident_title, steps, category, criticality, criticality_description FROM playbooks WHERE incident_title = ?", (selected_incident_title,))
        result = cursor.fetchone()
        conn.close()
        if result:
            incident_id = result[0]
            existing_details = result[1:]
            EditIncidentForm(self.root, self.get_db_connection(), self, incident_id, existing_details)
        else:
            messagebox.showerror("Error", "Incident ID not found.")

    def delete_incident(self):
        if self.auth.is_authenticated:
            try:
                selection_index = self.incidents_listbox.curselection()
                selected_incident_title = self.incidents_listbox.get(selection_index)

                conn = self.get_db_connection()
                cursor = conn.cursor()
                cursor.execute('DELETE FROM playbooks WHERE incident_title = ?', (selected_incident_title,))
                conn.commit()
                conn.close()

                self.incidents_listbox.delete(selection_index)
                self.update_incident_count()
            except Exception as e:
                print(e)
                messagebox.showerror("Error", "Failed to delete the incident")
        else:
            messagebox.showerror("Authentication Required", "You must be logged in to perform this action.")
            input_username = simpledialog.askstring("Username", "Enter Username")
            input_password = simpledialog.askstring("Password", "Enter Password:", show='*')
            if self.auth.authenticate(input_username, input_password):
                tk.messagebox.showinfo("Authentication", "Authentication successful!")
            else:
                tk.messagebox.showerror("Authentication", "Authentication failed!")
                return

    def edit_incident(self, incident_id):
        if self.auth.is_authenticated:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                'SELECT incident_title, steps, category, criticality, criticality_description FROM playbooks WHERE id = ?',
                (incident_id,))
            existing_details = cursor.fetchone()
            conn.close()

            if existing_details:
                EditIncidentForm(self.root, self.get_db_connection(), self, incident_id, existing_details)
            else:
                messagebox.showerror("Error", "Incident not found")
        else:
            messagebox.showerror("Authentication Required", "You must be logged in to perform this action.")

    def fetch_incidents(self, category=None):
        conn = self.get_db_connection()
        cursor = conn.cursor()
        query = "SELECT incident_title FROM playbooks"
        if category and category != "All":
            query += " WHERE category = ?"
            cursor.execute(query, (category,))
        else:
            cursor.execute(query)
        incidents = [row[0] for row in cursor.fetchall()]
        conn.close()
        return incidents

    def update_incidents_listbox(self, category=None):
        incidents = self.fetch_incidents(category)
        self.incidents_listbox.delete(0, tk.END)
        for incident_title in incidents:
            self.incidents_listbox.insert(tk.END, incident_title)
        self.update_incident_count()

    def update_incident_count(self):
        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM playbooks")
        count = cursor.fetchone()[0]
        conn.close()
        self.incident_count_label.config(text=f"Total Incidents: {count}")

    def filter_incidents(self, event):
        search_query = self.search_entry.get().lower()
        if search_query:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT incident_title FROM playbooks WHERE LOWER(incident_title) LIKE ?",
                           ('%' + search_query + '%',))
            filtered_incidents = [row[0] for row in cursor.fetchall()]
            conn.close()
        else:
            filtered_incidents = self.fetch_incidents()

        self.incidents_listbox.delete(0, tk.END)
        for incident_title in filtered_incidents:
            self.incidents_listbox.insert(tk.END, incident_title)

    def upload_playbook(self):
        if self.auth.is_authenticated:
            file_path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
            if file_path:
                if not file_path.endswith('.txt'):
                    tk.messagebox.showerror("Invalid File Type", "Only .txt files are supported.")
                    return
                self.parser.parse_file(file_path)
                self.update_incidents_listbox()
                tk.messagebox.showinfo("Upload Successful", "Playbook data has been uploaded and stored.")
        else:
            messagebox.showerror("Authentication Required", "You must be logged in to perform this action.")
            input_username = simpledialog.askstring("Username", "Enter Username")
            input_password = simpledialog.askstring("Password", "Enter Password:", show='*')
            if self.auth.authenticate(input_username, input_password):
                tk.messagebox.showinfo("Authentication", "Authentication successful!")
            else:
                tk.messagebox.showerror("Authentication", "Authentication failed!")

    def view_incident_details(self):
        selection_index = self.incidents_listbox.curselection()
        if not selection_index:
            messagebox.showinfo("Selection Error", "No incident selected.")
            return
        selected_incident_title = self.incidents_listbox.get(selection_index)
        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT steps, category, criticality, criticality_description FROM playbooks WHERE incident_title = ?",
            (selected_incident_title,))
        result = cursor.fetchone()
        conn.close()
        if result:
            steps_sequence, category, criticality, criticality_description = result
            self.diagram_visualizer.generate_diagram(selected_incident_title, steps_sequence, category, criticality,
                                                     criticality_description)
            self.diagram_visualizer.display_diagram()
        else:
            messagebox.showinfo("Error", "Incident details not found.")

    def filter_by_category(self, category):
        self.update_incidents_listbox(category)


if __name__ == "__main__":
    create_database()
    root = tk.Tk()
    app = PlaybookVisualizerApp(root)
    root.mainloop()
