# src/views/dialogs/lesson_dialog.py

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QTimeEdit, QComboBox, QLineEdit, QDialogButtonBox,
                           QCheckBox, QCalendarWidget, QMessageBox)
from PyQt6.QtCore import QTime, QDate, Qt

class LessonDialog(QDialog):
    def __init__(self, parent=None, selected_date=None):
        super().__init__(parent)
        self.parent = parent
        self.selected_date = selected_date or QDate.currentDate()
        self.setWindowTitle("Unterrichtsstunde hinzufügen")
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Kurs/Klasse (Pflichtfeld)
        layout.addWidget(QLabel("Kurs/Klasse:*"))
        self.course = QComboBox()
        self.load_courses()
        layout.addWidget(self.course)

        # Datum
        layout.addWidget(QLabel("Datum:"))
        self.calendar = QCalendarWidget()
        if self.selected_date:
            self.calendar.setSelectedDate(self.selected_date)
        layout.addWidget(self.calendar)

        # Uhrzeit
        layout.addWidget(QLabel("Uhrzeit:"))
        self.time = QTimeEdit()
        self.time.setDisplayFormat("HH:mm")
        self.time.setTime(QTime(8, 0))  # Standard: 8:00 Uhr
        layout.addWidget(self.time)

        # Fach
        layout.addWidget(QLabel("Fach:"))
        self.subject = QComboBox()
        self.subject.addItems(["Mathematik", "Deutsch", "Englisch", "Geschichte"])
        layout.addWidget(self.subject)

        # Thema
        layout.addWidget(QLabel("Thema:"))
        self.topic = QLineEdit()
        layout.addWidget(self.topic)

        # Checkbox für wiederkehrende Termine
        self.recurring_checkbox = QCheckBox("Im gesamten Halbjahr wiederholen")
        layout.addWidget(self.recurring_checkbox)

        # Pflichtfeld-Hinweis
        layout.addWidget(QLabel("* Pflichtfeld"))

        # Dialog-Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_data(self):
        """Gibt die eingegebenen Daten zurück"""
        return {
            'date': self.calendar.selectedDate().toString("yyyy-MM-dd"),
            'time': self.time.time().toString("HH:mm"),
            'subject': self.subject.currentText(),
            'topic': self.topic.text(),
            'is_recurring': self.recurring_checkbox.isChecked()
        }



    def load_courses(self):
        """Lädt alle verfügbaren Kurse/Klassen"""
        try:
            courses = self.parent.db.get_all_courses()
            self.course.clear()
            for course in courses:
                # Zeige Name und Typ des Kurses
                display_text = f"{course['name']} ({course['type']})"
                self.course.addItem(display_text, course['id'])
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Laden der Kurse: {str(e)}")

    def validate_and_accept(self):
        """Prüft die Eingaben vor dem Akzeptieren"""
        if self.course.currentData() is None:
            QMessageBox.warning(self, "Fehler", "Bitte wählen Sie einen Kurs/eine Klasse aus!")
            return
        self.accept()


    def update_subject(self, index):
        if index <= 0:  # "Bitte wählen..." oder ungültig
            self.subject.clear()
            return
            
        course_id = self.course.currentData()
        course = next((c for c in self.courses_data if c['id'] == course_id), None)
        if course and course['subject']:
            self.subject.setText(course['subject'])
        else:
            self.subject.clear()

    def load_competencies(self):
        try:
            competencies = self.parent.db.get_all_competencies()
            self.comp_select.clear()
            for comp in competencies:
                display_text = f"{comp['subject']} - {comp['area']}: {comp['description']}"
                self.comp_select.addItem(display_text, comp['id'])
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Laden der Kompetenzen: {str(e)}")

    def add_competency(self):
        if self.comp_select.currentData() is None:
            return
            
        comp_id = self.comp_select.currentData()
        if comp_id not in [x[0] for x in self.selected_competencies]:
            try:
                comp = self.parent.db.get_competency(comp_id)
                if comp:
                    self.selected_competencies.append((
                        comp['id'],
                        comp['subject'],
                        comp['area'],
                        comp['description']
                    ))
                    row = self.competencies_table.rowCount()
                    self.competencies_table.insertRow(row)
                    for i, value in enumerate([comp['id'], comp['subject'], 
                                            comp['area'], comp['description']]):
                        self.competencies_table.setItem(row, i, QTableWidgetItem(str(value)))
            except Exception as e:
                QMessageBox.critical(self, "Fehler", f"Fehler beim Hinzufügen der Kompetenz: {str(e)}")

    def get_all_courses(self) -> list:
        """Holt alle verfügbaren Kurse und Klassen."""
        try:
            cursor = self.execute(
                """SELECT id, name, type, subject 
                FROM courses 
                ORDER BY name"""
            )
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            raise Exception(f"Fehler beim Abrufen der Kurse: {str(e)}")

    def get_data(self):
        """Gibt die eingegebenen Daten zurück"""
        return {
            'course_id': self.course.currentData(),
            'date': self.calendar.selectedDate().toString("yyyy-MM-dd"),
            'time': self.time.time().toString("HH:mm"),
            'subject': self.subject.currentText(),
            'topic': self.topic.text(),
            'is_recurring': self.recurring_checkbox.isChecked()
        }