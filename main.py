#!/usr/bin/env python3
import sys
from src.database.db_manager import DatabaseManager
from src.views.list_manager import ListManager
from src.views.dialogs.student_dialog import StudentDialog
from src.models.student import Student
from src.views.tabs.course_tab import CourseTab
from src.views.tabs.settings_tab import SettingsTab
from src.views.dialogs.lesson_dialog import LessonDialog

from datetime import datetime, timedelta
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                           QHBoxLayout, QTabWidget, QTableWidget, QPushButton,
                           QLineEdit, QComboBox, QLabel, QSpinBox, QTableWidgetItem,
                           QDialog, QDialogButtonBox, QCalendarWidget, QTimeEdit,
                           QMenu, QMenuBar, QMessageBox, QGroupBox, QDateEdit,
                           QHBoxLayout, QCalendarWidget)
from PyQt6.QtCore import Qt, QTime, QDate, QTimer
from PyQt6.QtGui import QStandardItemModel, QStandardItem 
from PyQt6 import uic
import sqlite3

class StudentDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Schüler hinzufügen")
        layout = QVBoxLayout(self)

        # Name Eingabefeld
        self.name = QLineEdit()
        layout.addWidget(QLabel("Name:"))
        layout.addWidget(self.name)

        # OK und Abbrechen Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

class CompetencyDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Kompetenz hinzufügen")
        layout = QVBoxLayout(self)

        self.subject = QComboBox()
        self.subject.addItems(["Mathematik", "Deutsch", "Englisch", "Geschichte"])
        layout.addWidget(QLabel("Fach:"))
        layout.addWidget(self.subject)

        self.area = QComboBox()
        self.area.addItems(["Fachkompetenz", "Methodenkompetenz", "Sozialkompetenz", "Selbstkompetenz"])
        layout.addWidget(QLabel("Kompetenzbereich:"))
        layout.addWidget(self.area)

        self.description = QLineEdit()
        layout.addWidget(QLabel("Beschreibung:"))
        layout.addWidget(self.description)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

class LessonDialog(QDialog):
    def __init__(self, parent=None, selected_date=None):
        super().__init__(parent)
        self.setWindowTitle("Unterrichtsstunde hinzufügen")
        layout = QVBoxLayout(self)

        # Datum
        self.date = QCalendarWidget()
        if selected_date:
            self.date.setSelectedDate(selected_date)
        layout.addWidget(QLabel("Datum:"))
        layout.addWidget(self.date)

        # Uhrzeit
        self.time = QTimeEdit()
        self.time.setDisplayFormat("HH:mm")
        self.time.setTime(QTime(8, 0))  # Standard: 8:00 Uhr
        layout.addWidget(QLabel("Uhrzeit:"))
        layout.addWidget(self.time)

        # Fach
        self.subject = QComboBox()
        self.subject.addItems(["Mathematik", "Deutsch", "Englisch", "Geschichte"])
        layout.addWidget(QLabel("Fach:"))
        layout.addWidget(self.subject)

        # Thema
        self.topic = QLineEdit()
        layout.addWidget(QLabel("Thema:"))
        layout.addWidget(self.topic)

        # Kompetenzen
        layout.addWidget(QLabel("Kompetenzen:"))
        self.competencies_table = QTableWidget()
        self.competencies_table.setColumnCount(4)
        self.competencies_table.setHorizontalHeaderLabels(['ID', 'Fach', 'Bereich', 'Beschreibung'])
        layout.addWidget(self.competencies_table)

        # Kompetenzauswahl initialisieren
        self.comp_select = QComboBox()
        self.selected_competencies = []

        # Kompetenzen laden
        self.load_competencies(parent)

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
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def load_competencies(self):
        """Diese Methode würde im CompetencyDialog verwendet"""
        competencies = self.parent.db.get_all_competencies()
        self.competency_combo.clear()
        for comp in competencies:
            self.competency_combo.addItem(
                f"{comp['subject']} - {comp['area']}: {comp['description']}", 
                comp['id']
            )

    def add_competency(self):
        comp_text = self.comp_select.currentText()
        if comp_text:  # Prüfen ob überhaupt Kompetenzen verfügbar sind
            comp_id = int(comp_text.split(' - ')[0])

            # Prüfen ob Kompetenz bereits ausgewählt
            if  comp_id not in [x[0] for x in self.selected_competencies]:
                comp = next(c for c in self.comp_data if c[0] == comp_id)
                self.selected_competencies.append(comp)

                # Zur Tabelle hinzufügen
                row = self.competencies_table.rowCount()
                self.competencies_table.insertRow(row)
                for i, item in enumerate(comp):
                    self.competencies_table.setItem(row, i, QTableWidgetItem(str(item)))

class GradeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Bewertung hinzufügen")
        self.parent = parent
        layout = QVBoxLayout(self)

        # Schülerauswahl
        self.student = QComboBox()
        c = parent.conn.cursor()
        c.execute("SELECT id, name FROM students")
        self.students = c.fetchall()
        self.student.addItems([f"{id} - {name}" for id, name in self.students])
        layout.addWidget(QLabel("Schüler:"))
        layout.addWidget(self.student)

        # Stundenauswahl
        self.lesson = QComboBox()
        c.execute("SELECT id, date, subject, topic FROM lessons")
        self.lessons = c.fetchall()
        self.lesson.addItems([f"{id} - {date} - {subject} - {topic}" for id, date, subject, topic in self.lessons])
        layout.addWidget(QLabel("Stunde:"))
        layout.addWidget(self.lesson)

        # Kompetenzauswahl
        self.competency = QComboBox()
        c.execute("SELECT id, subject, area, description FROM competencies")
        self.competencies = c.fetchall()
        self.competency.addItems([f"{id} - {subject} - {area} - {description}" for id, subject, area, description in self.competencies])
        layout.addWidget(QLabel("Kompetenz:"))
        layout.addWidget(self.competency)

        # Note
        self.grade = QSpinBox()
        self.grade.setRange(1, 6)
        layout.addWidget(QLabel("Note:"))
        layout.addWidget(self.grade)

        # Kommentar
        self.comment = QLineEdit()
        layout.addWidget(QLabel("Kommentar:"))
        layout.addWidget(self.comment)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_data(self):
        student_id = int(self.student.currentText().split(' - ')[0])
        lesson_id = int(self.lesson.currentText().split(' - ')[0])
        competency_id = int(self.competency.currentText().split(' - ')[0])
        return {
            'student_id': student_id,
            'lesson_id': lesson_id,
            'competency_id': competency_id,
            'grade': self.grade.value(),
            'comment': self.comment.text()
        }

class RecurringLessonDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Wiederkehrende Stunde anlegen")
        layout = QVBoxLayout(self)

        # Fach
        self.subject = QComboBox()
        self.subject.addItems(["Mathematik", "Deutsch", "Englisch", "Geschichte"])
        layout.addWidget(QLabel("Fach:"))
        layout.addWidget(self.subject)

        # Klasse/Kurs
        self.course = QLineEdit()
        layout.addWidget(QLabel("Klasse/Kurs:"))
        layout.addWidget(self.course)

        # Wochentag
        self.weekday = QComboBox()
        self.weekday.addItems(["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag"])
        layout.addWidget(QLabel("Wochentag:"))
        layout.addWidget(self.weekday)

        # Uhrzeit
        self.time = QTimeEdit()
        self.time.setTime(QTime(8, 0))
        layout.addWidget(QLabel("Uhrzeit:"))
        layout.addWidget(self.time)

        # Dauer (in Minuten)
        self.duration = QSpinBox()
        self.duration.setRange(45, 180)
        self.duration.setValue(45)
        layout.addWidget(QLabel("Dauer (Minuten):"))
        layout.addWidget(self.duration)

        # Kompetenzen (Multiple)
        self.competencies = QComboBox()
        c = parent.conn.cursor()
        c.execute("SELECT id, subject, area, description FROM competencies")
        self.comp_data = c.fetchall()
        self.competencies.addItems([f"{id} - {subject} - {area} - {description}"
                                  for id, subject, area, description in self.comp_data])
        layout.addWidget(QLabel("Kompetenzen:"))
        layout.addWidget(self.competencies)

        self.selected_competencies = []
        btn_add_comp = QPushButton("Kompetenz hinzufügen")
        btn_add_comp.clicked.connect(self.add_competency)
        layout.addWidget(btn_add_comp)

        self.comp_list = QTableWidget()
        self.comp_list.setColumnCount(4)
        self.comp_list.setHorizontalHeaderLabels(['ID', 'Fach', 'Bereich', 'Beschreibung'])
        layout.addWidget(self.comp_list)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def add_competency(self):
        comp_id = int(self.competencies.currentText().split(' - ')[0])
        if comp_id not in [x[0] for x in self.selected_competencies]:
            comp = next(c for c in self.comp_data if c[0] == comp_id)
            self.selected_competencies.append(comp)
            row = self.comp_list.rowCount()
            self.comp_list.insertRow(row)
            for i, item in enumerate(comp):
                self.comp_list.setItem(row, i, QTableWidgetItem(str(item)))

class SchoolManagement(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()
        uic.loadUi("school.ui", self)
        self.list_manager = ListManager(self)
        self.calendarWidget.clicked.connect(self.on_date_selected)
        self.students_tab = self.tab_sus
        self.addLessonButton.clicked.connect(self.on_add_lesson_clicked)

        self.competencies_tab = QWidget()
        self.tabWidget.addTab(self.competencies_tab, "Kompetenzen")
        self.setup_competencies_tab()
        self.setup_students_tab()

        self.listView_tag.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.listView_tag.customContextMenuRequested.connect(self.show_lesson_context_menu)

        # Kurse-Tab initialisieren
        self.course_tab = CourseTab(self)
        self.tab_kurse.layout = QVBoxLayout(self.tab_kurse)
        self.tab_kurse.layout.addWidget(self.course_tab)

        # settings_tab-Code:
        self.settings_tab = SettingsTab(self)
        self.tab_sett.layout = QVBoxLayout(self.tab_sett)
        self.tab_sett.layout.addWidget(self.settings_tab)
        
        # Kurse-Menü
        self.menuKurse = QMenu("Kurse", self.menubar)
        self.menubar.addAction(self.menuKurse.menuAction())
        self.menuKurse.addAction("Neuer Kurs", self.course_tab.add_course)
        self.menuKurse.addAction("Kurse anzeigen", lambda: self.tabWidget.setCurrentWidget(self.tab_kurse))
        
        # Kompetenzen-Menü
        self.menuKompetenzen = QMenu("Kompetenzen", self.menubar)
        self.menubar.addAction(self.menuKompetenzen.menuAction())
        self.menuKompetenzen.addAction("Neue Kompetenz", self.add_competency)
        self.menuKompetenzen.addAction("Kompetenzen anzeigen", self.show_competencies)

        
        # Widgets referenzieren
        self.calendar = self.calendarWidget
        self.day_lessons = self.listView_tag
        self.focus_list = self.listView_fokus
        self.events_list = self.listView_ereignisse
        
        # Signale verbinden
        self.calendar.clicked.connect(self.on_date_selected)

        # Context Menu für Kalender
        self.calendar.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.calendar.customContextMenuRequested.connect(self.show_calendar_context_menu)
        self.calendar.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.calendar.customContextMenuRequested.connect(self.show_calendar_context_menu)



    def setup_students_tab(self):
        """Richtet den Schüler-Tab ein"""
        layout = QVBoxLayout(self.students_tab)
        
        # Tabelle für Schüler
        self.students_table = QTableWidget()
        self.students_table.setColumnCount(1)
        self.students_table.setHorizontalHeaderLabels(['Name'])
        self.students_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.students_table.verticalHeader().setVisible(False)
        self.students_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.students_table)
        
        # Button zum Hinzufügen
        btn_layout = QHBoxLayout()
        btn_add = QPushButton("Schüler hinzufügen")
        btn_add.clicked.connect(self.add_student)
        btn_layout.addWidget(btn_add)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # Kontext-Menü für die Tabelle einrichten
        self.students_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.students_table.customContextMenuRequested.connect(
            lambda pos: self.show_context_menu(pos, self.students_table)
        )
        
        # Initial Schüler laden
        self.refresh_students()



    def setup_competencies_tab(self):
        layout = QVBoxLayout(self.competencies_tab)

        self.competencies_table = QTableWidget()
        self.competencies_table.setColumnCount(3)
        self.competencies_table.setHorizontalHeaderLabels(['Fach', 'Bereich', 'Beschreibung'])
        layout.addWidget(self.competencies_table)

        btn_add = QPushButton("Kompetenz hinzufügen")
        btn_add.clicked.connect(self.add_competency)
        layout.addWidget(btn_add)

        self.add_context_menu(self.competencies_table)

        self.refresh_competencies()

    def setup_grades_tab(self):
        layout = QVBoxLayout(self.grades_tab)

        # Filtermöglichkeiten
        filter_layout = QHBoxLayout()
        self.student_filter = QComboBox()
        self.lesson_filter = QComboBox()
        self.competency_filter = QComboBox()
        filter_layout.addWidget(QLabel("Schüler:"))
        filter_layout.addWidget(self.student_filter)
        filter_layout.addWidget(QLabel("Stunde:"))
        filter_layout.addWidget(self.lesson_filter)
        filter_layout.addWidget(QLabel("Kompetenz:"))
        filter_layout.addWidget(self.competency_filter)
        layout.addLayout(filter_layout)

        self.grades_table = QTableWidget()
        self.grades_table.setColumnCount(6)
        self.grades_table.setHorizontalHeaderLabels(['ID', 'Schüler', 'Stunde', 'Kompetenz', 'Note', 'Kommentar'])
        layout.addWidget(self.grades_table)

        btn_add = QPushButton("Bewertung hinzufügen")
        btn_add.clicked.connect(self.add_grade)
        layout.addWidget(btn_add)


    def show_calendar_popup(self, date_edit):
        calendar = QCalendarWidget(self)
        calendar.clicked.connect(lambda date: self.set_date(date, date_edit, calendar))
        calendar.setWindowFlags(Qt.WindowType.Popup)
        calendar.show()
        # Position the calendar under the date edit
        pos = date_edit.mapToGlobal(date_edit.rect().bottomLeft())
        calendar.move(pos)

    def set_date(self, date, date_edit, calendar):
        date_edit.setDate(date)
        calendar.close()

    def set_current_semester(self):
        today = QDate.currentDate()
        if today.month() <= 7:  # Erstes Halbjahr
            self.start_date.setDate(QDate(today.year(), 2, 1))
            self.end_date.setDate(QDate(today.year(), 7, 31))
        else:  # Zweites Halbjahr
            self.start_date.setDate(QDate(today.year(), 8, 1))
            self.end_date.setDate(QDate(today.year() + 1, 1, 31))


    def add_student(self):
        try:
            dialog = StudentDialog(self)
            if dialog.exec():
                name = dialog.name.text().strip()
                if not name:
                    raise ValueError("Der Name darf nicht leer sein")
                    
                student = Student.create(self.db, name)
                self.refresh_students()
                self.statusBar().showMessage(f"Schüler {name} wurde hinzugefügt", 3000)
                
        except Exception as e:
            QMessageBox.critical(self, "Fehler", str(e))

 

    def refresh_students(self):
        try:
            self.students_table.setRowCount(0)
            students = Student.get_all(self.db)
            for student in students:
                row = self.students_table.rowCount()
                self.students_table.insertRow(row)
                item = QTableWidgetItem(student.name)
                item.setData(Qt.ItemDataRole.UserRole, student.id)  # Hier speichern wir die ID
                self.students_table.setItem(row, 0, item)
        except Exception as e:
            QMessageBox.critical(self, "Fehler", str(e))

    def add_lesson(self):
        dialog = LessonDialog(self)
        if dialog.exec():
            try:
                lesson_data = {
                    'date': dialog.date.selectedDate().toString("yyyy-MM-dd"),
                    'time': dialog.time.time().toString("HH:mm"),
                    'subject': dialog.subject.currentText(),
                    'topic': dialog.topic.text()
                }
                lesson_id = self.db.add_lesson(lesson_data)
                
                # Kompetenzen zuordnen
                for comp in dialog.selected_competencies:
                    self.db.add_lesson_competency(lesson_id, comp[0])
                    
                self.refresh_lessons()
                if hasattr(self, 'calendar'):
                    self.on_date_selected(dialog.date.selectedDate())
            except Exception as e:
                QMessageBox.critical(self, "Fehler", str(e))

    def refresh_lessons(self):
        try:
            self.lessons_table.setRowCount(0)
            lessons = self.db.get_all_lessons()
            for lesson in lessons:
                row = self.lessons_table.rowCount()
                self.lessons_table.insertRow(row)
                for i, value in enumerate([lesson['date'], lesson['subject'], lesson['topic']]):
                    self.lessons_table.setItem(row, i, QTableWidgetItem(str(value)))
        except Exception as e:
            QMessageBox.critical(self, "Fehler", str(e))

    def refresh_all(self):
        """Aktualisiert alle Listen und Tabellen"""
        if hasattr(self, 'course_tab'):
            self.course_tab.refresh_courses()
        # Andere refresh-Aufrufe...

    def add_competency(self):
        dialog = CompetencyDialog(self)
        if dialog.exec():
            try:
                comp_data = {
                    'subject': dialog.subject.currentText(),
                    'area': dialog.area.currentText(),
                    'description': dialog.description.text()
                }
                self.db.add_competency(comp_data)
                self.refresh_competencies()
            except Exception as e:
                QMessageBox.critical(self, "Fehler", str(e))

    def refresh_competencies(self):
        try:
            self.competencies_table.setRowCount(0)
            competencies = self.db.get_all_competencies()
            for comp in competencies:
                row = self.competencies_table.rowCount()
                self.competencies_table.insertRow(row)
                for i, value in enumerate([comp['subject'], comp['area'], comp['description']]):
                    self.competencies_table.setItem(row, i, QTableWidgetItem(str(value)))
        except Exception as e:
            QMessageBox.critical(self, "Fehler", str(e))

    def show_competencies(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Kompetenzen")
        layout = QVBoxLayout(dialog)
        
        table = QTableWidget()
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(['Fach', 'Bereich', 'Beschreibung'])
        layout.addWidget(table)
        
        try:
            competencies = self.db.get_all_competencies()
            table.setRowCount(0)
            for comp in competencies:
                pos = table.rowCount()
                table.insertRow(pos)
                for i, value in enumerate([comp['subject'], comp['area'], comp['description']]):
                    table.setItem(pos, i, QTableWidgetItem(str(value)))
        except Exception as e:
            QMessageBox.critical(self, "Fehler", str(e))
        
        dialog.exec()

    def add_grade(self):
            dialog = GradeDialog(self)
            if dialog.exec():
                try:
                    data = dialog.get_data()
                    self.db.add_grade(data)
                    self.refresh_grades()  # Aktualisiert die Notenansicht
                    self.list_manager.update_focus_list(self.calendarWidget.selectedDate())  # Aktualisiert die Fokus-Liste
                except Exception as e:
                    QMessageBox.critical(self, "Fehler", f"Fehler beim Speichern der Note: {str(e)}")

    def edit_grade(self, grade_id):
        try:
            existing_grade = self.db.get_grade(grade_id)
            dialog = GradeDialog(self, existing_grade)
            if dialog.exec():
                data = dialog.get_data()
                self.db.update_grade(grade_id, data)
                self.refresh_grades()
                self.list_manager.update_focus_list(self.calendarWidget.selectedDate())
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Bearbeiten der Note: {str(e)}")


        self.grades_table.setRowCount(0)
        for row in c.fetchall():
            self.grades_table.insertRow(self.grades_table.rowCount())
            for i, item in enumerate(row):
                self.grades_table.setItem(self.grades_table.rowCount()-1, i,
                                        QTableWidgetItem(str(item)))

    def setup_calendar_tab(self):
        layout = QVBoxLayout(self.calendar_tab)

        # Kalender
        self.calendar = QCalendarWidget()
        self.calendar.clicked.connect(self.on_date_selected)
        layout.addWidget(self.calendar)

        # Anzeige der Stunden für den ausgewählten Tag
        self.day_lessons = QTableWidget()
        self.day_lessons.setColumnCount(4)
        self.day_lessons.setHorizontalHeaderLabels(['Zeit', 'Fach', 'Thema', 'Kompetenzen'])
        layout.addWidget(self.day_lessons)

        # Button zum Hinzufügen
        btn_add = QPushButton("Unterrichtsstunde hinzufügen")
        btn_add.clicked.connect(self.add_lesson)
        layout.addWidget(btn_add)

    def on_date_selected(self, date):
        try:
            self.list_manager.update_all(date)
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Aktualisieren der Listen: {str(e)}")

    def add_recurring_lesson(self):
        dialog = RecurringLessonDialog(self)
        if dialog.exec():
            c = self.conn.cursor()

            # Stunde speichern
            c.execute("""INSERT INTO recurring_lessons
                        (subject, course, weekday, time, duration)
                        VALUES (?, ?, ?, ?, ?)""",
                    (dialog.subject.currentText(),
                    dialog.course.text(),
                    dialog.weekday.currentIndex(),
                    dialog.time.time().toString(),
                    dialog.duration.value()))

            lesson_id = c.lastrowid

            # Kompetenzen zuordnen
            for comp in dialog.selected_competencies:
                c.execute("""INSERT INTO lesson_competencies
                            (lesson_id, competency_id) VALUES (?, ?)""",
                        (lesson_id, comp[0]))

            self.conn.commit()
            self.refresh_calendar()

    def refresh_calendar(self):
        c = self.conn.cursor()

        # Tabelle leeren (außer Uhrzeiten)
        for row in range(self.week_table.rowCount()):
            for col in range(1, self.week_table.columnCount()):
                self.week_table.setItem(row, col, QTableWidgetItem(""))

        # Wiederkehrende Stunden eintragen
        c.execute("""SELECT subject, course, weekday, time, duration
                    FROM recurring_lessons""")

        for subject, course, weekday, time, duration in c.fetchall():
            hour = int(time.split(':')[0])
            cell_text = f"{subject}\n{course}"
            self.week_table.setItem(hour, weekday + 1,
                                QTableWidgetItem(cell_text))

    def add_lesson(self):
        selected_date = self.calendar.selectedDate() if hasattr(self, 'calendar') else None
        dialog = LessonDialog(self, selected_date)
        if dialog.exec():
            c = self.conn.cursor()

            # Stunde speichern
            selected_date = dialog.date.selectedDate().toString("yyyy-MM-dd")
            selected_time = dialog.time.time().toString("HH:mm")

            c.execute("""INSERT INTO lessons (date, time, subject, topic)
                        VALUES (?, ?, ?, ?)""",
                    (selected_date,
                    selected_time,
                    dialog.subject.currentText(),
                    dialog.topic.text()))

            lesson_id = c.lastrowid

            # Kompetenzen zuordnen
            for comp in dialog.selected_competencies:
                c.execute("""INSERT INTO lesson_competencies
                            (lesson_id, competency_id) VALUES (?, ?)""",
                        (lesson_id, comp[0]))

            self.conn.commit()
            if hasattr(self, 'calendar'):
                self.on_date_selected(dialog.date.selectedDate())
            self.refresh_lessons()

    def add_context_menu(self, table):
        table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        table.customContextMenuRequested.connect(
            lambda pos, t=table: self.show_context_menu(pos, t))

    def show_context_menu(self, pos, table):
        item = table.itemAt(pos)
        if item is None:
            return
            
        menu = QMenu()
        edit_action = menu.addAction("Bearbeiten")
        delete_action = menu.addAction("Löschen")
        
        action = menu.exec(table.viewport().mapToGlobal(pos))
        
        if action:
            row = table.rowAt(pos.y())
            item = table.item(row, 0)  # Erste Spalte enthält das Item mit der ID
            if item:
                item_id = item.data(Qt.ItemDataRole.UserRole)
                
                if action == edit_action:
                    self.edit_item(table, item_id)
                elif action == delete_action:
                    self.delete_item(table, item_id)
        
    def show_lesson_context_menu(self, pos):
        self.list_manager.show_lesson_context_menu(pos)
        
    def edit_item(self, table, item_id):
        try:
            if table == self.students_table:
                student = Student.get_by_id(self.db, item_id)
                if student:
                    dialog = StudentDialog(self)
                    dialog.name.setText(student.name)
                    if dialog.exec():
                        new_name = dialog.name.text().strip()
                        if new_name:
                            student.name = new_name
                            student.update(self.db)
                            self.refresh_students()
                        else:
                            raise ValueError("Der Name darf nicht leer sein")
                else:
                    raise ValueError("Schüler nicht gefunden")
                    
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Bearbeiten: {str(e)}")
    
    def update_item(self, table_name, item_id, dialog):
        try:
            if table_name == "students":
                self.db.update_student(item_id, dialog.name.text())
            elif table_name == "lessons":
                lesson_data = {
                    'date': dialog.date.selectedDate().toString("yyyy-MM-dd"),
                    'time': dialog.time.time().toString("HH:mm"),
                    'subject': dialog.subject.currentText(),
                    'topic': dialog.topic.text()
                }
                self.db.update_lesson(item_id, lesson_data)
            elif table_name == "competencies":
                comp_data = {
                    'subject': dialog.subject.currentText(),
                    'area': dialog.area.currentText(),
                    'description': dialog.description.text()
                }
                self.db.update_competency(item_id, comp_data)
        except Exception as e:
            QMessageBox.critical(self, "Fehler", str(e))

    def delete_item(self, table, item_id):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Question)
        msg.setText("Möchten Sie diesen Eintrag wirklich löschen?")
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if msg.exec() == QMessageBox.StandardButton.Yes:
            try:
                if table == self.students_table:
                    self.db.delete_student(item_id)
                elif table == self.lessons_table:
                    self.db.delete_lesson(item_id)
                elif table == self.competencies_table:
                    self.db.delete_competency(item_id)
                
                self.refresh_table(table)
            except Exception as e:
                QMessageBox.critical(self, "Fehler", f"Fehler beim Löschen: {str(e)}")

    def refresh_table(self, table):
        try:
            if table == self.students_table:
                self.refresh_students()
            elif table == self.lessons_table:
                self.refresh_lessons()
            elif table == self.competencies_table:
                self.refresh_competencies()
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Aktualisieren der Tabelle: {str(e)}")

    def show_calendar_context_menu(self, pos):
        menu = QMenu()
        add_action = menu.addAction("Unterrichtsstunde hinzufügen")
        action = menu.exec(self.calendar.mapToGlobal(pos))
    
        if action == add_action:
            self.add_day_lesson()

    def load_students(self):
        """Diese Methode würde im StudentDialog verwendet"""
        students = self.parent.db.get_all_students()
        self.student_combo.clear()
        for student in students:
            self.student_combo.addItem(student['name'], student['id'])

    def on_add_lesson_clicked(self):
        """Handler für den '+ Button' im Kalender"""
        self.list_manager.add_day_lesson(self.calendarWidget.selectedDate())

    def show_calendar_context_menu(self, pos):
        """Kontext-Menü für den Kalender"""
        menu = QMenu()
        add_action = menu.addAction("Unterrichtsstunde hinzufügen")
        action = menu.exec(self.calendar.mapToGlobal(pos))

        if action == add_action:
            self.list_manager.add_day_lesson(self.calendarWidget.selectedDate())

if __name__ == '__main__':
    app = QApplication(sys.argv)
    school = SchoolManagement()
    school.show()
    sys.exit(app.exec())
