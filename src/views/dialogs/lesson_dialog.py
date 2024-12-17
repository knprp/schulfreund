# src/views/dialogs/lesson_dialog.py

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QComboBox, QPushButton, QTableWidget, QTableWidgetItem,
    QDialogButtonBox, QCalendarWidget, QTimeEdit, QMessageBox
)
from PyQt6.QtCore import Qt, QTime

class LessonDialog(QDialog):
    def __init__(self, parent=None, selected_date=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("Unterrichtsstunde hinzufügen")
        self.setup_ui(selected_date)

    def setup_ui(self, selected_date):
        layout = QVBoxLayout(self)

        # Kursauswahl (NEU!)
        layout.addWidget(QLabel("Kurs/Klasse:*"))
        self.course = QComboBox()
        self.load_courses()
        layout.addWidget(self.course)

        # Datum
        layout.addWidget(QLabel("Datum:*"))
        self.date = QCalendarWidget()
        if selected_date:
            self.date.setSelectedDate(selected_date)
        layout.addWidget(self.date)

        # Uhrzeit
        layout.addWidget(QLabel("Uhrzeit:*"))
        self.time = QTimeEdit()
        self.time.setDisplayFormat("HH:mm")
        self.time.setTime(QTime(8, 0))  # Standard: 8:00 Uhr
        layout.addWidget(self.time)

        # Fach wird aus dem Kurs übernommen
        layout.addWidget(QLabel("Fach:*"))
        self.subject = QLineEdit()
        self.subject.setReadOnly(True)  # Wird automatisch aus Kurs gefüllt
        layout.addWidget(self.subject)

        # Thema
        layout.addWidget(QLabel("Thema:*"))
        self.topic = QLineEdit()
        layout.addWidget(self.topic)

        # Kompetenzen
        layout.addWidget(QLabel("Kompetenzen:"))
        self.competencies_table = QTableWidget()
        self.competencies_table.setColumnCount(4)
        self.competencies_table.setHorizontalHeaderLabels(['ID', 'Fach', 'Bereich', 'Beschreibung'])
        layout.addWidget(self.competencies_table)

        # Kompetenzauswahl
        self.comp_select = QComboBox()
        self.selected_competencies = []
        self.load_competencies()

        # Buttons für Kompetenzauswahl
        select_layout = QHBoxLayout()
        select_layout.addWidget(self.comp_select)
        btn_add_comp = QPushButton("Kompetenz hinzufügen")
        btn_add_comp.clicked.connect(self.add_competency)
        select_layout.addWidget(btn_add_comp)
        layout.addLayout(select_layout)

        # Dialog-Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        # Kursauswahl mit Subject-Update verbinden
        self.course.currentIndexChanged.connect(self.update_subject)

    def load_courses(self):
        try:
            courses = self.parent.db.execute(
                "SELECT id, name, subject FROM courses ORDER BY name"
            ).fetchall()
            
            self.courses_data = courses  # Speichern für späteren Zugriff
            self.course.clear()
            self.course.addItem("Bitte wählen...", None)
            
            for course in courses:
                display_text = f"{course['name']} ({course['subject'] or 'Kein Fach'})"
                self.course.addItem(display_text, course['id'])
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Laden der Kurse: {str(e)}")

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

    def validate_and_accept(self):
        if not self.course.currentData():
            QMessageBox.warning(self, "Fehler", "Bitte wählen Sie einen Kurs aus.")
            return
        if not self.topic.text().strip():
            QMessageBox.warning(self, "Fehler", "Bitte geben Sie ein Thema ein.")
            return
            
        self.accept()

    def get_data(self) -> dict:
        return {
            'course_id': self.course.currentData(),
            'date': self.date.selectedDate().toString("yyyy-MM-dd"),
            'time': self.time.time().toString("HH:mm"),
            'subject': self.subject.text(),
            'topic': self.topic.text().strip(),
            'competencies': [comp[0] for comp in self.selected_competencies]
        }