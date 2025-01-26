# src/views/dialogs/course_dialog.py

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit, QHBoxLayout,
                           QComboBox, QDialogButtonBox, QPushButton, QColorDialog,
                           QMessageBox, QFileDialog)
from PyQt6.QtGui import QColor
from src.models.course import Course
from src.models.student import Student
from src.views.dialogs.import_csv_students_dialog import ImportCsvStudentsDialog


class CourseDialog(QDialog):
    def __init__(self, parent=None, course=None):
        super().__init__(parent)
        self.parent = parent
        self.course = course
        self.db = parent.parent.db
        self.selected_student_ids = []  # Neue Variable für Import
        self.setWindowTitle("Kurs hinzufügen" if not course else "Kurs bearbeiten")
        self.color = QColor('#FFFFFF')
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
        self.subject.currentTextChanged.connect(self.load_templates)

        # Beschreibung
        layout.addWidget(QLabel("Beschreibung:"))
        self.description = QLineEdit()
        layout.addWidget(self.description)

        # Farbe
        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("Farbe:"))
        self.color_button = QPushButton()
        self.color_button.setFixedSize(40, 20)
        self.update_color_button()
        self.color_button.clicked.connect(self.choose_color)
        color_layout.addWidget(self.color_button)
        layout.addLayout(color_layout)

        # Import-Buttons nebeneinander
        import_layout = QHBoxLayout()
        
        import_csv_btn = QPushButton("Schüler aus CSV importieren")
        import_csv_btn.clicked.connect(self.import_from_csv)
        import_layout.addWidget(import_csv_btn)
        
        import_existing_btn = QPushButton("Schüler aus anderen Kursen importieren")
        import_existing_btn.clicked.connect(self.import_existing_students)
        import_layout.addWidget(import_existing_btn)
        
        layout.addLayout(import_layout)

        # Vor den Dialog-Buttons:
        # Template-Auswahl
        template_layout = QHBoxLayout()
        template_layout.addWidget(QLabel("Bewertungsvorlage:"))
        self.template = QComboBox()
        self.load_templates()
        template_layout.addWidget(self.template)
        layout.addLayout(template_layout)



        # Button Box erstellen aber NICHT verbinden
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        layout.addWidget(self.button_box)

        # Nach Setup die Signale verbinden
        self.setup_signals()

    def setup_signals(self):
        """Verbindet alle Signale nach dem Setup"""
        self.button_box.accepted.connect(self.accept)  # Jetzt die überschriebene accept() Methode
        self.button_box.rejected.connect(self.reject)

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

    def import_existing_students(self):
        """Öffnet den Import-Dialog für Schüler"""
        from src.views.dialogs.import_students_dialog import ImportStudentsDialog
        try:
            window = self.parent.parent
            dialog = ImportStudentsDialog(window)
            if dialog.exec():
                # Nur IDs speichern, Import erfolgt später
                self.selected_student_ids = dialog.get_selected_students()
                
        except Exception as e:
            QMessageBox.critical(self, "Fehler", 
                            f"Fehler beim Importieren der Schüler: {str(e)}")

    def import_from_csv(self):
        if not self.course:
            QMessageBox.warning(self, "Fehler", "Bitte speichern Sie den Kurs zuerst")
            return
            
        filepath, _ = QFileDialog.getOpenFileName(
            self, "CSV-Datei auswählen", "", "CSV Dateien (*.csv)")
        if filepath:
            dialog = ImportCsvStudentsDialog(self, self.db)
            dialog.load_csv_data(filepath)
            if dialog.exec():
                self.parent.refresh_courses()  # Aktualisiere die Kurstabelle
                QMessageBox.information(self, "Erfolg", "Die Schüler wurden erfolgreich importiert")


    def accept(self):
        """Überschreibt die Standard accept() Methode"""
        print("Accept wurde aufgerufen")  # DEBUG 
        try:
            window = self.parent.parent
            print("Starte Speichern des Kurses")  # DEBUG

            # 1. Kurs speichern/aktualisieren
            data = self.get_data()
            if self.course:
                print("Aktualisiere existierenden Kurs")  # DEBUG
                self.course.name = data['name']
                self.course.type = data['type']
                self.course.subject = data['subject']
                self.course.description = data['description']
                self.course.color = data['color']
                self.course.update(window.db)
                course_id = self.course.id
            else:
                print("Erstelle neuen Kurs mit Daten:", data)  # DEBUG
                course = Course.create(window.db, **data)
                course_id = course.id

            # 2. Schüler importieren
            semester_dates = window.db.get_semester_dates()
            if self.selected_student_ids and semester_dates:
                # Hole das aktive Semester aus der Historie
                current_semester = window.db.get_semester_by_date(semester_dates['semester_start'])
                if current_semester:
                    print(f"Aktuelles Semester gefunden: {current_semester}")  # DEBUG
                    for student_id in self.selected_student_ids:
                        student = Student.get_by_id(window.db, student_id)
                        if student:
                            student.add_course(window.db, course_id, current_semester['id'])

            print("Rufe super().accept() auf")  # DEBUG
            super().accept()

        except Exception as e:
            print(f"Fehler aufgetreten: {e}")  # DEBUG
            QMessageBox.critical(self, "Fehler", str(e))

    def load_templates(self):
        """Lädt alle Bewertungsvorlagen für das aktuelle Fach"""
        try:
            templates = self.db.get_templates_by_subject(self.subject.currentText())
            self.template.clear()
            self.template.addItem("Keine Vorlage", None)
            for template in templates:
                self.template.addItem(template['name'], template['id'])
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Laden der Vorlagen: {str(e)}")

    def get_data(self):
        """Gibt die eingegebenen Daten zurück"""
        data = {
            'name': self.name.text().strip(),
            'type': 'class' if self.type.currentText() == "Klasse" else 'course',
            'subject': self.subject.currentText().strip() or None,
            'description': self.description.text().strip() or None,
            'color': self.color.name(),
            'template_id': self.template.currentData()
        }
        return data