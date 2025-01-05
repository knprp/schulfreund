from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QLineEdit, QDialogButtonBox, QPushButton)

class StudentDialog(QDialog):
    def __init__(self, parent=None, student=None):
        super().__init__(parent)
        self.student = student
        self.setWindowTitle("Schüler bearbeiten" if student else "Schüler hinzufügen")
        self.setup_ui()
        
        if student:
            self.load_student_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Vorname Eingabefeld
        first_name_layout = QVBoxLayout()
        first_name_layout.addWidget(QLabel("Vorname:"))
        self.first_name = QLineEdit()
        self.first_name.setPlaceholderText("Vorname eingeben")
        first_name_layout.addWidget(self.first_name)
        layout.addLayout(first_name_layout)

        # Nachname Eingabefeld
        last_name_layout = QVBoxLayout()
        last_name_layout.addWidget(QLabel("Nachname:"))
        self.last_name = QLineEdit()
        self.last_name.setPlaceholderText("Nachname eingeben")
        last_name_layout.addWidget(self.last_name)
        layout.addLayout(last_name_layout)

        # Button-Layout
        button_layout = QHBoxLayout()

        # Standard-Buttons (OK/Abbrechen)
        self.button_box = QDialogButtonBox()
        if not self.student:  # Nur beim Erstellen neuer Schüler
            save_new_btn = QPushButton("Speichern && Neu")
            save_new_btn.clicked.connect(self.save_and_new)
            self.button_box.addButton(save_new_btn, QDialogButtonBox.ButtonRole.ActionRole)

        self.button_box.addButton(QDialogButtonBox.StandardButton.Ok)
        self.button_box.addButton(QDialogButtonBox.StandardButton.Cancel)
        
        self.button_box.accepted.connect(self.validate_and_accept)
        self.button_box.rejected.connect(self.reject)
        button_layout.addWidget(self.button_box)
        
        layout.addLayout(button_layout)

    def validate_and_accept(self):
        """Prüft die Eingaben vor dem Akzeptieren"""
        if self.validate_input():
            self.accept()

    def validate_input(self) -> bool:
        """Prüft die Eingaben und gibt True zurück wenn sie gültig sind"""
        first_name = self.first_name.text().strip()
        last_name = self.last_name.text().strip()

        if not first_name:
            self.first_name.setFocus()
            return False
        if not last_name:
            self.last_name.setFocus()
            return False
        return True

    def save_and_new(self):
        """Speichert den aktuellen Schüler und bereitet den Dialog für einen neuen vor"""
        if self.validate_input():
            self.done(2)  # Eigener Return-Code für "Speichern und Neu"

    def get_data(self) -> dict:
        """Gibt die eingegebenen Daten zurück"""
        return {
            'first_name': self.first_name.text().strip(),
            'last_name': self.last_name.text().strip()
        }

    def load_student_data(self):
        """Lädt die Daten eines existierenden Schülers in den Dialog"""
        if self.student:
            self.first_name.setText(self.student.first_name)
            self.last_name.setText(self.student.last_name)

    def clear_input(self):
        """Leert alle Eingabefelder"""
        self.first_name.clear()
        self.last_name.clear()
        self.first_name.setFocus()