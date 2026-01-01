# src/views/dialogs/competency_dialog.py
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit,
                           QComboBox, QDialogButtonBox, QMessageBox)

class CompetencyDialog(QDialog):
    def __init__(self, parent=None, competency=None):
        super().__init__(parent)
        self.main_window = parent.parent  # Referenz zum Hauptfenster
        self.competency = competency
        self.setWindowTitle(
            "Kompetenz bearbeiten" if competency else "Kompetenz hinzufügen"
        )
        self.setup_ui()
        if competency:
            self.load_competency_data()

    def setup_ui(self):
        """Erstellt die Benutzeroberfläche des Dialogs"""
        layout = QVBoxLayout(self)

        # Fach
        layout.addWidget(QLabel("Fach:"))
        self.subject = QComboBox()
        self.subject.setEditable(False)  # Keine freie Eingabe mehr
        self.load_subjects()
        layout.addWidget(self.subject)

        # Kompetenzbereich
        layout.addWidget(QLabel("Kompetenzbereich:"))
        self.area = QComboBox()
        self.area.addItems([
            "Sachkompetenz",
            "Methodenkompetenz",
            "Sozialkompetenz",
            "Selbstkompetenz"
        ])
        layout.addWidget(self.area)

        # Beschreibung
        layout.addWidget(QLabel("Beschreibung:"))
        self.description = QLineEdit()
        layout.addWidget(self.description)

        # Dialog-Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.validate_and_accept)  # Neue Validierungsmethode
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def load_subjects(self):
        """Lädt die verfügbaren Fächer aus der Datenbank"""
        try:
            self.subject.clear()
            
            # Hole alle Fächer
            cursor = self.main_window.db.execute(
                "SELECT name FROM subjects ORDER BY name"
            )
            subjects = cursor.fetchall()
            
            for subject in subjects:
                self.subject.addItem(subject['name'])
                
        except Exception as e:
            QMessageBox.critical(self, "Fehler", 
                               f"Fehler beim Laden der Fächer: {str(e)}")

    def validate_and_accept(self):
        """Validiert die Eingaben vor dem Speichern"""
        if not self.subject.currentText():
            QMessageBox.warning(self, "Fehler", "Bitte wählen Sie ein Fach aus")
            return
        if not self.description.text().strip():
            QMessageBox.warning(self, "Fehler", "Bitte geben Sie eine Beschreibung ein")
            self.description.setFocus()
            return
        self.accept()

    def load_competency_data(self):
        """Lädt die Daten einer existierenden Kompetenz in den Dialog"""
        # Finde und setze das Fach
        index = self.subject.findText(self.competency['subject'])
        if index >= 0:
            self.subject.setCurrentIndex(index)
        self.area.setCurrentText(self.competency['area'])
        self.description.setText(self.competency['description'])

    def get_data(self):
        """Gibt die eingegebenen Daten zurück"""
        return {
            'subject': self.subject.currentText(),
            'area': self.area.currentText(),
            'description': self.description.text().strip()
        }