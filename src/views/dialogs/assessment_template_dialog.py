# src/views/dialogs/assessment_template_dialog.py

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                           QLineEdit, QComboBox, QDialogButtonBox, 
                           QTextEdit, QMessageBox)
from PyQt6.QtCore import Qt

class AssessmentTemplateDialog(QDialog):
    def __init__(self, parent=None, template=None):
        super().__init__(parent)
        self.parent = parent
        self.template = template
        self.setWindowTitle("Vorlage bearbeiten" if template else "Neue Vorlage")
        self.setup_ui()
        
        if template:
            self.load_template_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Name
        layout.addWidget(QLabel("Name:*"))
        self.name = QLineEdit()
        layout.addWidget(self.name)

        # Fach
        layout.addWidget(QLabel("Fach:*"))
        self.subject = QComboBox()
        self.subject.setEditable(True)
        self.load_subjects()
        layout.addWidget(self.subject)

        # Notensystem
        layout.addWidget(QLabel("Notensystem:*"))
        self.grading_system = QComboBox()
        self.load_grading_systems()
        layout.addWidget(self.grading_system)

        # Beschreibung
        layout.addWidget(QLabel("Beschreibung:"))
        self.description = QTextEdit()
        self.description.setMaximumHeight(100)
        layout.addWidget(self.description)

        # Pflichtfeld-Hinweis
        layout.addWidget(QLabel("* Pflichtfeld"))

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def load_subjects(self):
        try:
            # Hole alle vorhandenen Fächer aus den Kursen
            cursor = self.parent.db.execute(
                """SELECT DISTINCT subject FROM courses 
                   WHERE subject IS NOT NULL ORDER BY subject"""
            )
            subjects = [row['subject'] for row in cursor.fetchall()]
            self.subject.addItems(subjects)
        except Exception as e:
            QMessageBox.critical(self, "Fehler", 
                               f"Fehler beim Laden der Fächer: {str(e)}")

    def load_grading_systems(self):
        try:
            systems = self.parent.db.get_all_grading_systems()
            for system in systems:
                display_text = f"{system['name']} ({system['min_grade']}-{system['max_grade']})"
                self.grading_system.addItem(display_text, system['id'])
        except Exception as e:
            QMessageBox.critical(self, "Fehler", 
                               f"Fehler beim Laden der Notensysteme: {str(e)}")

    def load_template_data(self):
        self.name.setText(self.template['name'])
        self.subject.setCurrentText(self.template['subject'])
        # Finde und setze das richtige Notensystem
        for i in range(self.grading_system.count()):
            if self.grading_system.itemData(i) == self.template['grading_system_id']:
                self.grading_system.setCurrentIndex(i)
                break
        self.description.setText(self.template.get('description', ''))

    def validate_and_accept(self):
        if not self.name.text().strip():
            QMessageBox.warning(self, "Fehler", "Bitte geben Sie einen Namen ein")
            return
        if not self.subject.currentText().strip():
            QMessageBox.warning(self, "Fehler", "Bitte wählen Sie ein Fach")
            return
        if self.grading_system.currentData() is None:
            QMessageBox.warning(self, "Fehler", "Bitte wählen Sie ein Notensystem")
            return
        self.accept()

    def get_data(self) -> dict:
        """Gibt die eingegebenen Daten zurück"""
        return {
            'name': self.name.text().strip(),
            'subject': self.subject.currentText().strip(),
            'grading_system_id': self.grading_system.currentData(),
            'description': self.description.toPlainText().strip() or None
        }