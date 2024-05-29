from graphviz import Digraph
from PIL import Image, ImageTk, ImageDraw, ImageFont
import tkinter as tk
from tkinter import filedialog, messagebox

from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas


class IncidentDiagramVisualizer:
    def __init__(self, parent):
        self.parent = parent

    def generate_diagram(self, incident_title, steps, category, criticality, criticality_description):
        dot = Digraph(comment=incident_title)
        dot.attr('node', shape='box', style='filled', color='lightblue')

        criticality_colors = {
            "Low": "green",
            "Medium": "yellow",
            "High": "orange",
            "Critical": "red"
        }

        criticality_color = criticality_colors.get(criticality, "black")
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

        criticality_label = f"<<b>Criticality: {criticality} - {criticality_description}</b>>"
        dot.node('Criticality', label=criticality_label, fontcolor="black", color=criticality_color, style='filled')

        dot.attr(rankdir='TB')

        with dot.subgraph() as s:
            s.attr(rank='sink')
            s.node('Criticality')

        dot.render('diagram', format='png', cleanup=True)

        self.add_title_and_category(incident_title, category)

    def add_title_and_category(self, incident_title, category):
        img = Image.open('diagram.png')

        draw = ImageDraw.Draw(img)
        font_path = "arialbd.ttf"
        font = ImageFont.truetype(font_path, 16)

        title_text = f"{incident_title}\nCategory: {category}"
        text_width, text_height = draw.textsize(title_text, font=font)

        img_width, img_height = img.size
        x_position = (img_width - text_width) // 2

        new_img_height = img_height + text_height + 40
        new_img = Image.new('RGB', (img_width, new_img_height), (255, 255, 255))
        new_img.paste(img, (0, text_height + 40))

        draw = ImageDraw.Draw(new_img)
        draw.text((x_position, 10), title_text, font=font, fill="black")

        new_img.save('diagram_with_title.png')

    def display_diagram(self):
        new_window = tk.Toplevel(self.parent)
        new_window.title("Incident Steps Diagram")
        img = Image.open('diagram_with_title.png')
        photo = ImageTk.PhotoImage(img)

        image_label = tk.Label(new_window, image=photo)
        image_label.photo = photo
        image_label.pack()

        export_button = tk.Button(new_window, text="Export", command=self.export_diagram)
        export_button.pack()

        new_window.geometry(f"{img.width}x{img.height + 40}")

        self.new_window = new_window
        self.img = img

    def export_diagram(self):
        file_types = [('PNG Files', '*.png'), ('PDF Files', '*.pdf')]
        file_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=file_types)
        if file_path:
            if file_path.endswith('.png'):
                self.img.save(file_path)
                messagebox.showinfo("Export Successful", f"Diagram saved as {file_path}")
            elif file_path.endswith('.pdf'):
                c = canvas.Canvas(file_path, pagesize=letter)
                img_width, img_height = self.img.size
                page_width, page_height = letter

                scale = min(page_width / img_width, page_height / img_height)
                img_width *= scale
                img_height *= scale

                x = (page_width - img_width) / 2
                y = page_height - img_height

                c.drawImage(ImageReader('diagram_with_title.png'), x, y, width=img_width, height=img_height)
                c.showPage()
                c.save()
                messagebox.showinfo("Export Successful", f"Diagram saved as {file_path}")
