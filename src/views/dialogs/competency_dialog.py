# src/views/dialogs/competency_dialog.py

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit,
                           QComboBox, QDialogButtonBox)

class CompetencyDialog(QDialog):
    def __init__(self, parent=None, competency=None):
        super().__init__(parent)
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
        self.subject.setEditable(True)
        self.subject.addItems([
            "Mathematik", "Deutsch", "Englisch", "Geschichte", 
            "Biologie", "Physik", "Chemie", "Kunst", "Musik"
        ])
        layout.addWidget(self.subject)

        # Kompetenzbereich
        layout.addWidget(QLabel("Kompetenzbereich:"))
        self.area = QComboBox()
        self.area.addItems([
            "Fachkompetenz",
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
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def load_competency_data(self):
        """Lädt die Daten einer existierenden Kompetenz in den Dialog"""
        self.subject.setCurrentText(self.competency['subject'])
        self.area.setCurrentText(self.competency['area'])
        self.description.setText(self.competency['description'])

    def get_data(self):
        """Gibt die eingegebenen Daten zurück"""
        return {
            'subject': self.subject.currentText().strip(),
            'area': self.area.currentText(),
            'description': self.description.text().strip()
        }