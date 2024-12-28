# src/views/dialogs/course_dialog.py

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit, QHBoxLayout,
                           QComboBox, QDialogButtonBox, QPushButton, QColorDialog)
from PyQt6.QtGui import QColor


class CourseDialog(QDialog):
    def __init__(self, parent=None, course=None):
        super().__init__(parent)
        self.course = course
        self.setWindowTitle("Kurs hinzufügen" if not course else "Kurs bearbeiten")
        self.color = QColor('#FFFFFF')  # Standardfarbe Weiß
        self.setup_ui()
        
        if course:
            self.load_course_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Name
        layout.addWidget(QLabel("Name:"))
        self.name = QLineEdit()
        layout.addWidget(self.name)

        # Typ
        layout.addWidget(QLabel("Typ:"))
        self.type = QComboBox()
        self.type.addItems(["Klasse", "Kurs"])
        layout.addWidget(self.type)

        # Fach
        layout.addWidget(QLabel("Fach:"))
        self.subject = QComboBox()
        self.subject.setEditable(True)
        self.subject.addItems(["Mathematik", "Deutsch", "Englisch", "Geschichte"])
        layout.addWidget(self.subject)

        # Beschreibung
        layout.addWidget(QLabel("Beschreibung:"))
        self.description = QLineEdit()
        layout.addWidget(self.description)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )

        # Farbe
        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("Farbe:"))
        self.color_button = QPushButton()
        self.color_button.setFixedSize(40, 20)
        self.update_color_button()
        self.color_button.clicked.connect(self.choose_color)
        color_layout.addWidget(self.color_button)
        layout.addLayout(color_layout)

    
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def load_course_data(self):
        self.name.setText(self.course.name)
        self.type.setCurrentText("Klasse" if self.course.type == 'class' else "Kurs")
        if self.course.subject:
            self.subject.setCurrentText(self.course.subject)
        self.description.setText(self.course.description or "")
        if self.course.color:
            self.color = QColor(self.course.color)
            self.update_color_button()

    def update_color_button(self):
        """Aktualisiert die Farbe des Buttons"""
        self.color_button.setStyleSheet(
            f"background-color: {self.color.name()}; border: 1px solid gray;"
        )

    def choose_color(self):
        """Öffnet den Farbwähler-Dialog"""
        color = QColorDialog.getColor(self.color, self)
        if color.isValid():
            self.color = color
            self.update_color_button()

    def get_data(self):
        data = {
            'name': self.name.text().strip(),
            'type': 'class' if self.type.currentText() == "Klasse" else 'course',
            'subject': self.subject.currentText().strip() or None,
            'description': self.description.text().strip() or None,
            'color': self.color.name()  # Speichere die Farbe als HTML-Code
        }
        return data