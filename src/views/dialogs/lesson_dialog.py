# src/views/dialogs/lesson_dialog.py

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QTimeEdit, QComboBox, QDialogButtonBox,
                           QCheckBox, QCalendarWidget, QMessageBox)
from PyQt6.QtCore import QTime, QDate, Qt

class LessonDialog(QDialog):
    def __init__(self, parent=None, selected_date=None):
        super().__init__(parent)
        self.parent = parent
        self.selected_date = selected_date or QDate.currentDate()
        self.subject_label = QLabel("-")  # Hier als Klassenattribut definieren
        self.setWindowTitle("Unterrichtsstunde hinzufügen")
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Kurs/Klasse (Pflichtfeld)
        course_layout = QHBoxLayout()
        course_layout.addWidget(QLabel("Kurs/Klasse:*"))
        self.course = QComboBox()
        self.course.currentIndexChanged.connect(self.update_subject_display)
        self.load_courses()
        course_layout.addWidget(self.course)
        layout.addLayout(course_layout)
        
        # Anzeige des Fachs
        subject_layout = QHBoxLayout()
        subject_layout.addWidget(QLabel("Fach:"))
        subject_layout.addWidget(self.subject_label)  # Verwenden des Klassenattributs
        layout.addLayout(subject_layout)

        # Datum
        layout.addWidget(QLabel("Datum:"))
        self.calendar = QCalendarWidget()
        if self.selected_date:
            self.calendar.setSelectedDate(self.selected_date)
        layout.addWidget(self.calendar)

        # Uhrzeit
        time_layout = QHBoxLayout()
        time_layout.addWidget(QLabel("Uhrzeit:"))
        self.time = QTimeEdit()
        self.time.setDisplayFormat("HH:mm")
        self.time.setTime(QTime(8, 0))  # Standard: 8:00 Uhr
        time_layout.addWidget(self.time)
        layout.addLayout(time_layout)

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
            self.course.addItem("Bitte wählen...", None)  # Standardauswahl
            for course in courses:
                display_text = f"{course['name']} ({course['type']})"
                self.course.addItem(display_text, course)  # Speichere das gesamte course dict
            self.update_subject_display()  # Initiales Update
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Laden der Kurse: {str(e)}")

    def update_subject_display(self):
        """Aktualisiert die Anzeige des Fachs basierend auf der Kursauswahl"""
        course_data = self.course.currentData()
        if course_data and course_data.get('subject'):
            self.subject_label.setText(course_data['subject'])
        else:
            self.subject_label.setText("-")

    def validate_and_accept(self):
        """Prüft die Eingaben vor dem Akzeptieren"""
        course_data = self.course.currentData()
        if not course_data:
            QMessageBox.warning(self, "Fehler", "Bitte wählen Sie einen Kurs/eine Klasse aus!")
            return
        if not course_data.get('subject'):
            QMessageBox.warning(self, "Fehler", "Der gewählte Kurs hat kein zugeordnetes Fach!")
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
        course_data = self.course.currentData()
        return {
            'course_id': course_data['id'],
            'date': self.calendar.selectedDate().toString("yyyy-MM-dd"),
            'time': self.time.time().toString("HH:mm"),
            'subject': course_data['subject'],  # Fach kommt jetzt aus dem Kurs
            'is_recurring': self.recurring_checkbox.isChecked()
        }