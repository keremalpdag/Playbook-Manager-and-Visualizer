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
        self.incidents_listbox.bind("<Button-3>", self.show_context_menu)  # Bind right-click to show context menu

        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Delete", command=self.delete_incident)
        self.context_menu.add_command(label="Edit", command=self.edit_incident)

        self.view_button = ttk.Button(root, text="View Selected Incident", command=self.view_incident_details)
        self.view_button.pack(pady=5)

        self.update_incidents_listbox()

        self.add_button = ttk.Button(self.input_frame, text="Add Procedure", command=self.add_procedure)
        self.add_button.pack(side=tk.LEFT, padx=10)

        self.reset_button = ttk.Button(self.input_frame, text="Reset All", command=self.delete_all_incidents)
        self.reset_button.pack(side=tk.RIGHT, padx=10)

    def delete_all_incidents(self):
        if self.auth.is_authenticated:
            if messagebox.askyesno("Confirm",
                                   "Are you sure you want to delete all incidents? This action cannot be undone."):
                # Clear all records from the database
                conn = sqlite3.connect('playbook_visualizer.db')
                cursor = conn.cursor()
                cursor.execute('DELETE FROM playbooks')
                conn.commit()
                conn.close()
                # Clear the listbox
                self.incidents_listbox.delete(0, tk.END)
                messagebox.showinfo("Reset Complete", "All incidents have been deleted.")
        else:
            messagebox.showerror("Authentication Required", "You must be logged in to perform this action.")
            input_username = simpledialog.askstring("Username", "Enter Username")
            input_password = simpledialog.askstring("Password", "Enter Password:", show='*')
            if self.auth.authenticate(input_username,input_password):
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
            print(e)  # Log or handle the exception appropriately

    def delete_incident(self):
        if self.auth.is_authenticated:
            try:
                selection_index = self.incidents_listbox.curselection()
                selected_incident_title = self.incidents_listbox.get(selection_index)
                # Delete from database
                conn = sqlite3.connect('playbook_visualizer.db')
                cursor = conn.cursor()
                cursor.execute('DELETE FROM playbooks WHERE incident_title = ?', (selected_incident_title,))
                conn.commit()
                conn.close()
                # Remove from listbox
                self.incidents_listbox.delete(selection_index)
            except Exception as e:
                print(e)  # Log or handle the exception appropriately
                messagebox.showerror("Error", "Failed to delete the incident")
        else:
            messagebox.showerror("Authentication Required", "You must be logged in to perform this action.")
            input_username = simpledialog.askstring("Username", "Enter Username")
            input_password = simpledialog.askstring("Password", "Enter Password:", show='*')
            if self.auth.authenticate(input_username,input_password):
                tk.messagebox.showinfo("Authentication", "Authentication successful!")
            else:
                tk.messagebox.showerror("Authentication", "Authentication failed!")
                return

    def edit_incident(self):
        selection = self.incidents_listbox.curselection()
        if not selection:
            messagebox.showerror("Error", "No incident selected!")
            return

        selected_index = selection[0]
        selected_incident = self.incidents_listbox.get(selected_index)
        incident_id = selected_incident.split(":")[0].strip()  # Assuming ID is prefixed to the title

        # Fetch existing details from the database
        conn = sqlite3.connect('playbook_visualizer.db')
        cursor = conn.cursor()
        cursor.execute('SELECT incident_title, steps FROM playbooks WHERE id = ?', (incident_id,))
        incident = cursor.fetchone()
        conn.close()

        if not incident:
            messagebox.showerror("Error", "Incident not found!")
            return

        # Split title and steps
        incident_title, steps = incident

        # Dialogs to edit details
        new_incident_title = simpledialog.askstring("Edit Incident", "Edit the incident title:",
                                                    initialvalue=incident_title)
        if not new_incident_title:
            return
        new_steps = simpledialog.askstring("Edit Incident", "Edit the steps details:", initialvalue=steps)
        if not new_steps:
            return

        # Update database
        conn = sqlite3.connect('playbook_visualizer.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE playbooks SET incident_title = ?, steps = ? WHERE id = ?',
                       (new_incident_title, new_steps, incident_id))
        conn.commit()
        conn.close()

        # Update listbox display
        self.incidents_listbox.delete(selected_index)
        self.incidents_listbox.insert(selected_index, f"{incident_id}: {new_incident_title}")

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
            messagebox.showerror("Authentication Required", "You must be logged in to perform this action.")
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
        if self.auth.is_authenticated:
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

            steps = f"Preparation: {preparation}\nDetection: {detection}\nResponse: {response}"
            category = "Default Category"  # This can be modified to include category selection if necessary
            self.insert_procedure(f"{incident_number}: {incident_name}", steps, category)
        else:
            messagebox.showerror("Authentication Required", "You must be logged in to perform this action.")
            input_username = simpledialog.askstring("Username", "Enter Username")
            input_password = simpledialog.askstring("Password", "Enter Password:", show='*')
            if self.auth.authenticate(input_username,input_password):
                tk.messagebox.showinfo("Authentication", "Authentication successful!")
            else:
                tk.messagebox.showerror("Authentication", "Authentication failed!")
                return

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
