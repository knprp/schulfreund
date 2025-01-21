# src/views/dialogs/grading_system_dialog.py

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                           QLineEdit, QDoubleSpinBox, QTextEdit, 
                           QPushButton, QDialogButtonBox, QMessageBox)
from PyQt6.QtCore import Qt

class GradingSystemDialog(QDialog):
    def __init__(self, parent=None, system_id=None):
        super().__init__(parent)
        self.parent = parent
        self.system_id = system_id
        self.setWindowTitle("Notensystem " + 
                          ("bearbeiten" if system_id else "hinzufügen"))
        self.setup_ui()
        
        if system_id:
            self.load_system_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Name
        layout.addWidget(QLabel("Name:"))
        self.name = QLineEdit()
        self.name.setPlaceholderText("z.B. Unterstufe 1-6")
        layout.addWidget(self.name)
        
        # Noten-Bereich
        range_layout = QHBoxLayout()
        
        range_layout.addWidget(QLabel("Minimale Note:"))
        self.min_grade = QDoubleSpinBox()
        self.min_grade.setRange(0, 15)
        self.min_grade.setDecimals(2)
        range_layout.addWidget(self.min_grade)
        
        range_layout.addWidget(QLabel("Maximale Note:"))
        self.max_grade = QDoubleSpinBox()
        self.max_grade.setRange(0, 15)
        self.max_grade.setDecimals(2)
        range_layout.addWidget(self.max_grade)
        
        layout.addLayout(range_layout)
        
        # Schrittgröße
        step_layout = QHBoxLayout()
        step_layout.addWidget(QLabel("Schrittgröße:"))
        self.step_size = QDoubleSpinBox()
        self.step_size.setRange(0.01, 1)
        self.step_size.setDecimals(2)
        self.step_size.setValue(0.33)
        step_layout.addWidget(self.step_size)
        step_layout.addStretch()
        
        layout.addLayout(step_layout)
        
        # Beschreibung
        layout.addWidget(QLabel("Beschreibung (optional):"))
        self.description = QTextEdit()
        self.description.setMaximumHeight(100)
        layout.addWidget(self.description)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def validate_and_accept(self):
        """Prüft die Eingaben vor dem Speichern"""
        try:
            # Name ist Pflicht
            name = self.name.text().strip()
            if not name:
                raise ValueError("Bitte geben Sie einen Namen ein")

            # Min muss kleiner als Max sein
            min_grade = self.min_grade.value()
            max_grade = self.max_grade.value()
            if min_grade >= max_grade:
                raise ValueError("Die minimale Note muss kleiner als die maximale Note sein")

            # Schrittgröße muss sinnvoll sein
            step_size = self.step_size.value()
            if step_size <= 0:
                raise ValueError("Die Schrittgröße muss größer als 0 sein")
                
            # Prüfe ob Schrittgröße zum Bereich passt
            grade_range = max_grade - min_grade
            if step_size >= grade_range:
                raise ValueError("Die Schrittgröße muss kleiner als der Notenbereich sein")

            # Speichere die Daten
            self.save_data()
            self.accept()

        except ValueError as e:
            QMessageBox.warning(self, "Eingabefehler", str(e))

    def save_data(self):
        """Speichert die Daten in der Datenbank"""
        try:
            data = {
                'name': self.name.text().strip(),
                'min_grade': self.min_grade.value(),
                'max_grade': self.max_grade.value(),
                'step_size': self.step_size.value(),
                'description': self.description.toPlainText().strip() or None
            }

            if self.system_id:
                # Update
                self.parent.db.update_grading_system(self.system_id, **data)
            else:
                # Neues System
                self.system_id = self.parent.db.add_grading_system(**data)

        except Exception as e:
            QMessageBox.critical(self, "Fehler", 
                               f"Fehler beim Speichern: {str(e)}")
            raise

    def load_system_data(self):
        """Lädt die Daten eines bestehenden Systems"""
        try:
            system = self.parent.db.get_grading_system(self.system_id)
            if system:
                self.name.setText(system['name'])
                self.min_grade.setValue(system['min_grade'])
                self.max_grade.setValue(system['max_grade'])
                self.step_size.setValue(system['step_size'])
                if system.get('description'):
                    self.description.setText(system['description'])
            else:
                raise ValueError(f"System mit ID {self.system_id} nicht gefunden")

        except Exception as e:
            QMessageBox.critical(self, "Fehler", 
                               f"Fehler beim Laden: {str(e)}")
            self.reject()