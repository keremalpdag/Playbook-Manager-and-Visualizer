import tkinter as tk
import sqlite3
from tkinter import ttk
from tkinter import filedialog

from database import create_database
from incident_diagram_visualizer import IncidentDiagramVisualizer
from playbook_parser import PlaybookParser
from auth import Authenticator
from tkinter import simpledialog, messagebox


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
        self.input_label = ttk.Label(self.input_frame, text="Upload Playbook/Procedure:")
        self.input_label.pack(side=tk.LEFT)
        self.upload_button = ttk.Button(self.input_frame, text="Upload", command=self.upload_playbook)
        self.upload_button.pack(side=tk.RIGHT)

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

        self.view_button = ttk.Button(root, text="View Selected Incident", command=self.view_incident_details)
        self.view_button.pack(pady=5)

        self.update_incidents_listbox()

        self.add_button = ttk.Button(self.input_frame, text="Add Procedure", command=self.add_procedure)
        self.add_button.pack(side=tk.LEFT, padx=10)

    def fetch_incidents(self, category=None):
        conn = sqlite3.connect('playbook_visualizer.db')
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

    def filter_incidents(self, event):
        search_query = self.search_entry.get().lower()
        if search_query:
            conn = sqlite3.connect('playbook_visualizer.db')
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
            file_path = filedialog.askopenfilename()
            if file_path:
                self.parser.parse_file(file_path)
                self.update_incidents_listbox()
                tk.messagebox.showinfo("Upload Successful", "Playbook data has been uploaded and stored.")
        else:
            input_username = simpledialog.askstring("Username", "Enter Username")
            input_password = simpledialog.askstring("Password", "Enter Password:", show='*')
            if self.auth.authenticate(input_username,input_password):
                tk.messagebox.showinfo("Authentication", "Authentication successful!")
            else:
                tk.messagebox.showerror("Authentication", "Authentication failed!")
                return

    def view_incident_details(self):
        selection_index = self.incidents_listbox.curselection()
        if not selection_index:
            messagebox.showinfo("Selection Error", "No incident selected.")
            return
        selected_incident_title = self.incidents_listbox.get(selection_index)
        conn = sqlite3.connect('playbook_visualizer.db')
        cursor = conn.cursor()
        cursor.execute("SELECT steps, category FROM playbooks WHERE incident_title = ?", (selected_incident_title,))
        result = cursor.fetchone()
        conn.close()
        if result:
            steps_sequence, category = result
            self.diagram_visualizer.generate_diagram(selected_incident_title, steps_sequence, category)
            self.diagram_visualizer.display_diagram()
        else:
            messagebox.showinfo("Error", "Incident details not found.")

    def filter_by_category(self, category):
        self.update_incidents_listbox(category)

    def add_procedure(self):
        # Open dialogs to ask for incident number, name, and phases
        incident_number = simpledialog.askstring("New Incident", "Enter the incident number:")
        if not incident_number:
            messagebox.showerror("Error", "Incident number is required!")
            return
        incident_name = simpledialog.askstring("New Incident", "Enter the incident name:")
        if not incident_name:
            messagebox.showerror("Error", "Incident name is required!")
            return

        preparation = simpledialog.askstring("New Incident", "Enter Preparation phase details:")
        detection = simpledialog.askstring("New Incident", "Enter Detection phase details:")
        response = simpledialog.askstring("New Incident", "Enter Response phase details:")

        if not (preparation and detection and response):
            messagebox.showerror("Error", "All phases must be provided!")
            return

        # Format steps
        steps = f"Preparation: {preparation}\nDetection: {detection}\nResponse: {response}"
        category = "Default Category"  # This can be modified to include category selection if necessary
        self.insert_procedure(f"{incident_number}: {incident_name}", steps, category)

    def insert_procedure(self, title, steps, category):
        conn = sqlite3.connect('playbook_visualizer.db')
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO playbooks (incident_title, steps, category) VALUES (?, ?, ?)',
                           (title, steps, category))
            conn.commit()
            messagebox.showinfo("Success", "Procedure added successfully")
            self.update_incidents_listbox()  # Refresh the listbox
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Failed to add the procedure")
        finally:
            conn.close()


if __name__ == "__main__":
    create_database()
    root = tk.Tk()
    app = PlaybookVisualizerApp(root)
    root.mainloop()
