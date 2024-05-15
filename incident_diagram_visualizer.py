from graphviz import Digraph
from PIL import Image, ImageTk
import tkinter as tk

class IncidentDiagramVisualizer:
    def __init__(self, parent):
        self.parent = parent

    def generate_diagram(self, incident_title, steps, category, criticality, criticality_description):
        dot = Digraph(comment=incident_title)
        dot.attr('node', shape='box', style='filled', color='lightblue')
        dot.attr('graph',
                 label=f"{incident_title}\\nCategory: {category}\\nCriticality: {criticality} - {criticality_description}",
                 fontsize='20')

        phases = steps.split('\n')
        for phase in phases:
            if ': ' in phase:
                phase_name, phase_desc = phase.split(': ', 1)
                dot.node(phase_name, label=f'{phase_name}: {phase_desc}')

        previous_phase = None
        for phase in phases:
            if ': ' in phase:
                current_phase = phase.split(': ', 1)[0]
                if previous_phase:
                    dot.edge(previous_phase, current_phase)
                previous_phase = current_phase

        dot.render('diagram', format='png', cleanup=True)

    def display_diagram(self):
        new_window = tk.Toplevel(self.parent)
        new_window.title("Incident Steps Diagram")
        img = Image.open('diagram.png')
        photo = ImageTk.PhotoImage(img)

        image_label = tk.Label(new_window, image=photo)
        image_label.photo = photo
        image_label.pack()

        new_window.geometry(f"{img.width}x{img.height}")
