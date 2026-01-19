from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QLineEdit, QDialogButtonBox, QPushButton,
                           QListWidget, QListWidgetItem)
from PyQt6.QtCore import Qt

class StudentDialog(QDialog):
    def __init__(self, parent=None, student=None, db=None):
        super().__init__(parent)
        self.student = student
        # Nur Controller-gestützter Pfad
        if hasattr(parent, 'controllers'):
            self.main_window = parent
        elif hasattr(parent, 'parent') and hasattr(parent.parent, 'controllers'):
            self.main_window = parent.parent
        else:
            raise ValueError("StudentDialog benötigt Zugriff auf Controller.")
        self.setWindowTitle("Schüler bearbeiten" if student else "Schüler hinzufügen")
        self.setup_ui()
        
        if student:
            self.load_student_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Kurs/Klasse Auswahl
        course_layout = QVBoxLayout()
        course_layout.addWidget(QLabel("Kurse/Klassen (Mehrfachauswahl möglich):"))
        self.course_list = QListWidget()
        self.course_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        course_layout.addWidget(self.course_list)
        layout.addLayout(course_layout)
        self.refresh_courses()

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
            save_new_btn.setDefault(True)
            self.button_box.addButton(save_new_btn, QDialogButtonBox.ButtonRole.ActionRole)

        self.button_box.addButton(QDialogButtonBox.StandardButton.Ok)
        self.button_box.addButton(QDialogButtonBox.StandardButton.Cancel)
        
        self.button_box.accepted.connect(self.validate_and_accept)
        self.button_box.rejected.connect(self.reject)
        button_layout.addWidget(self.button_box)

        layout.addLayout(button_layout)

    def refresh_courses(self):
        """Lädt die verfügbaren Kurse in die Liste"""
        self.course_list.clear()
        try:
            courses = self.main_window.controllers.course.get_all_courses()
            for course in courses:
                item = QListWidgetItem(course['name'])
                item.setData(Qt.ItemDataRole.UserRole, course['id'])
                self.course_list.addItem(item)
        except Exception as e:
            print(f"Fehler beim Laden der Kurse: {e}")

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
        selected_items = self.course_list.selectedItems()
        course_ids = [item.data(Qt.ItemDataRole.UserRole) for item in selected_items]
        
        return {
            'first_name': self.first_name.text().strip(),
            'last_name': self.last_name.text().strip(),
            'course_ids': course_ids  # Jetzt eine Liste von IDs
        }


    def load_student_data(self):
        """Lädt die Daten eines existierenden Schülers in den Dialog"""
        if self.student:
            self.first_name.setText(self.student.first_name)
            self.last_name.setText(self.student.last_name)
            
            # Aktuelle Kurse laden
            # Hole aktuelle Kurse über Controller wenn möglich
            current_courses = self.main_window.controllers.student.get_student_courses(self.student.id)
            if current_courses:
                for i in range(self.course_list.count()):
                    item = self.course_list.item(i)
                    course_id = item.data(Qt.ItemDataRole.UserRole)
                    if any(c['id'] == course_id for c in current_courses):
                        item.setSelected(True)


    def clear_input(self):
        """Leert alle Eingabefelder"""
        self.first_name.clear()
        self.last_name.clear()
        self.first_name.setFocus()