import sqlite3

class PlaybookParser:
    def __init__(self, db_path='playbook_visualizer.db'):
        self.db_path = db_path

    def categorize_incidents(self, title):
        categories = {
            "Fraud & Abuse": ["Fraud", "Impersonation"],
            "Network Security": ["Network", "DoS"],
            "Software & Firmware": ["Software", "Firmware", "Remote Exploitation"],
            "Physical Security": ["Physical", "Tampering"],
            "Data Security": ["Data Breach", "Ransomware", "Malware"]
        }
        for category, keywords in categories.items():
            if any(keyword in title for keyword in keywords):
                return category
        return "Other"

    def insert_incident_into_db(self, incident_title, steps, category):
        steps_str = '\n'.join([f'{k}: {v}' for k, v in steps.items()])
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO playbooks (incident_title, steps, category) VALUES (?, ?, ?)''',
                       (incident_title, steps_str, category))
        conn.commit()
        conn.close()

    def parse_file(self, file_path):
        with open(file_path, 'r') as file:
            content = file.read()

        incidents = content.split('Incident')[1:]
        for incident in incidents:
            lines = incident.strip().split('\n')
            incident_title = lines[0].strip()
            steps = {'Preparation': '', 'Detection': '', 'Response': ''}
            current_step = None

            for line in lines[1:]:
                if line.startswith('Preparation:'):
                    current_step = 'Preparation'
                elif line.startswith('Detection:'):
                    current_step = 'Detection'
                elif line.startswith('Response:'):
                    current_step = 'Response'
                if current_step:
                    steps[current_step] += line[len(current_step) + 1:].strip() + ' '

            category = self.categorize_incidents(incident_title)

            self.insert_incident_into_db(incident_title, steps, category)

