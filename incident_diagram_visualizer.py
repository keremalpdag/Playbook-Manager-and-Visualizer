from graphviz import Digraph
from PIL import Image, ImageTk
import tkinter as tk

class IncidentDiagramVisualizer:
    def __init__(self, parent):
        self.parent = parent

    def generate_diagram(self, incident_title, steps, category):
        dot = Digraph(comment=incident_title)

        # Define attributes for the graph, nodes, and edges
        dot.attr('node', shape='box', style='filled', color='lightblue')
        dot.attr('graph', label=f"{incident_title}\nCategory: {category}", fontsize='20')

        # Split steps into phases and create nodes
        phases = steps.split('\n')
        for phase in phases:
            phase_name, phase_desc = phase.split(': ', 1)
            dot.node(phase_name, label=f'{phase_name}: {phase_desc}')

        # Connect nodes in sequence
        if len(phases) > 1:
            for i in range(1, len(phases)):
                dot.edge(phases[i-1].split(': ', 1)[0], phases[i].split(': ', 1)[0])

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
