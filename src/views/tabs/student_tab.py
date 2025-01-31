from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
                           QTableWidget, QTableWidgetItem, QHeaderView,
                           QPushButton, QLabel, QLineEdit, QMessageBox,
                           QComboBox)
from PyQt6.QtCore import Qt
from PyQt6.QtCharts import QChart, QChartView, QPolarChart, QSplineSeries, QValueAxis, QCategoryAxis
from PyQt6.QtGui import QPen, QColor, QPainter, QBrush
import math

from src.views.dialogs.student_dialog import StudentDialog
from src.views.student.remarks_widget import RemarksWidget
from src.views.student.grades_widget import GradesWidget
from src.views.student.analysis_widget import AnalysisWidget



class StudentTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.setup_ui()

    def setup_ui(self):
        """Erstellt die grundlegende UI-Struktur"""
        self.current_student_id = None
        layout = QHBoxLayout(self)

        # Linke Seite - Schülerliste
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        # Suchfeld
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Suchen...")
        self.search_input.textChanged.connect(self.filter_students)
        left_layout.addWidget(self.search_input)

        # Kursfilter (vor dem Suchfeld)
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Kurs:"))
        self.course_filter = QComboBox()
        self.course_filter.currentIndexChanged.connect(self.refresh_students)
        filter_layout.addWidget(self.course_filter)

        # Refresh button
        self.refresh_button = QPushButton("Aktualisieren")
        self.refresh_button.clicked.connect(self.refresh_all)
        filter_layout.addWidget(self.refresh_button)

        # Filter-Layout zum left_layout hinzufügen (VOR dem Suchfeld)
        left_layout.insertLayout(0, filter_layout)  # Als erstes Element einfügen

        # Schülertabelle
        self.students_table = QTableWidget()
        self.students_table.setColumnCount(3)
        self.students_table.setHorizontalHeaderLabels(["Nachname", "Vorname", "Kurse"])
        self.students_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.students_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.students_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.students_table.itemSelectionChanged.connect(self.on_student_selected)
        left_layout.addWidget(self.students_table)

        # Buttons für Schülerverwaltung
        button_layout = QHBoxLayout()
        
        add_button = QPushButton("Hinzufügen")
        add_button.clicked.connect(self.add_student)
        button_layout.addWidget(add_button)
        
        edit_button = QPushButton("Bearbeiten")
        edit_button.clicked.connect(self.edit_student)
        button_layout.addWidget(edit_button)
        
        delete_button = QPushButton("Löschen")
        delete_button.clicked.connect(self.delete_student)
        button_layout.addWidget(delete_button)
        
        left_layout.addLayout(button_layout)

        # Rechte Seite - TabWidget
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        # Neues Label für Schülerinfo
        self.student_header = QLabel()
        self.student_header.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            padding: 10px;
            background-color: #f0f0f0;
            border-radius: 5px;
            margin-bottom: 10px;
        """)
        self.student_header.setVisible(False)  # Initial versteckt
        right_layout.addWidget(self.student_header)

        self.detail_tabs = QTabWidget()
        
        # Tab 1: Bemerkungen
        self.remarks_widget = RemarksWidget(self)
        self.detail_tabs.addTab(self.remarks_widget, "Bemerkungen")

        
        # Tab 2: Notenübersicht
        self.grades_widget = GradesWidget(self)
        self.detail_tabs.addTab(self.grades_widget, "Noten")
        
        # Tab 3: Notenanalyse
        self.analysis_widget = AnalysisWidget(self)
        self.detail_tabs.addTab(self.analysis_widget, "Analyse")

        right_layout.addWidget(self.detail_tabs)

        # Splitter hinzufügen
        layout.addWidget(left_widget, 1)  # Stretch-Faktor 1
        layout.addWidget(right_widget, 2)  # Stretch-Faktor 2

        self.refresh_all()
       

    def refresh_students(self):
        """Aktualisiert die Schülerliste"""
        try:
            students = self.main_window.db.get_all_students()
            self.students_table.setRowCount(len(students))
            
            for row, student in enumerate(students):
                # Name
                self.students_table.setItem(
                    row, 0, 
                    QTableWidgetItem(student['last_name'])
                )
        except Exception as e:
            print ("Fehler beim refreshen trat auf:", e)

    def refresh_course_filter(self):
        """Aktualisiert die Kursauswahl"""
        try:
            self.course_filter.blockSignals(True)
            current_course = self.course_filter.currentData()
            
            self.course_filter.clear()
            self.course_filter.addItem("Alle Kurse", None)
            
            semester = self.main_window.db.get_semester_dates()
            if semester:
                cursor = self.main_window.db.execute(
                    """SELECT DISTINCT c.id, c.name 
                    FROM courses c
                    JOIN student_courses sc ON c.id = sc.course_id
                    JOIN semester_history sh ON sc.semester_id = sh.id
                    WHERE sh.start_date = ? AND sh.end_date = ?
                    ORDER BY c.name""",
                    (semester['semester_start'], semester['semester_end'])
                )
                for course in cursor.fetchall():
                    self.course_filter.addItem(course['name'], course['id'])

            # Versuche die vorherige Auswahl wiederherzustellen
            if current_course:
                index = self.course_filter.findData(current_course)
                if index >= 0:
                    self.course_filter.setCurrentIndex(index)
                    
            self.course_filter.blockSignals(False)
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Fehler",
                f"Fehler beim Aktualisieren der Kursauswahl: {str(e)}"
            )

    def refresh_all(self):
        """Aktualisiert alle Daten"""
        self.refresh_course_filter()
        self.refresh_students()
        if self.current_student_id:
            self.load_student_details(self.current_student_id)

    def add_student(self):
        """Öffnet den Dialog zum Hinzufügen eines Schülers"""
        try:
            dialog = StudentDialog(
                parent=self.main_window,
                student=None,
                db=self.main_window.db
            )
            
            while True:
                result = dialog.exec()
                if result == 0:  # Abbrechen
                    break
                    
                data = dialog.get_data()
                student = self.create_student(data)
                
                if result == 2:  # Speichern und Neu
                    dialog.clear_input()
                    continue
                    
                break
                
            self.refresh_students()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Fehler",
                f"Fehler beim Hinzufügen des Schülers: {str(e)}"
            )

    def edit_student(self):
        """Öffnet den Dialog zum Bearbeiten eines Schülers"""
        try:
            selected = self.students_table.selectedItems()
            if not selected:
                return
                
            student_id = self.students_table.item(
                selected[0].row(), 0
            ).data(Qt.ItemDataRole.UserRole)
            
            # Row-Objekt aus der Datenbank holen
            row = self.main_window.db.execute(
                "SELECT * FROM students WHERE id = ?",
                (student_id,)
            ).fetchone()
            
            if row:
                # Row in Student-Objekt konvertieren
                from src.models.student import Student
                student = Student(
                    id=row['id'],
                    first_name=row['first_name'],
                    last_name=row['last_name']
                )
                
                dialog = StudentDialog(
                    parent=self.main_window,
                    student=student,
                    db=self.main_window.db
                )
                
                if dialog.exec():
                    data = dialog.get_data()
                    self.update_student(student_id, data)
                    self.refresh_students()
                    
        except Exception as e:
            QMessageBox.critical(
                self,
                "Fehler",
                f"Fehler beim Bearbeiten des Schülers: {str(e)}"
            )

    def delete_student(self):
        """Löscht den ausgewählten Schüler"""
        try:
            selected = self.students_table.selectedItems()
            if not selected:
                return
                
            student_id = self.students_table.item(
                selected[0].row(), 0
            ).data(Qt.ItemDataRole.UserRole)
            
            name = f"{self.students_table.item(selected[0].row(), 1).text()} {self.students_table.item(selected[0].row(), 0).text()}"
            
            reply = QMessageBox.question(
                self,
                'Schüler löschen',
                f'Möchten Sie den Schüler "{name}" wirklich löschen?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.main_window.db.execute(
                    "DELETE FROM students WHERE id = ?",
                    (student_id,)
                )
                self.refresh_students()
                
        except Exception as e:
            QMessageBox.critical(
                self,
                "Fehler",
                f"Fehler beim Löschen des Schülers: {str(e)}"
            )

    def create_student(self, data: dict) -> int:
        """Erstellt einen neuen Schüler in der Datenbank"""
        try:
            cursor = self.main_window.db.execute(
                """INSERT INTO students (first_name, last_name)
                VALUES (?, ?)""",
                (data['first_name'], data['last_name'])
            )
            student_id = cursor.lastrowid
            
            # Kurszuordnungen
            if data['course_ids']:
                semester = self.main_window.db.get_semester_dates()
                if not semester:
                    raise ValueError("Kein aktives Semester gefunden")
                    
                # Hole semester_id aus der Historie
                cursor = self.main_window.db.execute(
                    """SELECT id FROM semester_history 
                    WHERE start_date = ? AND end_date = ?""",
                    (semester['semester_start'], semester['semester_end'])
                )
                semester_result = cursor.fetchone()
                if not semester_result:
                    raise ValueError("Aktives Semester nicht in der Historie gefunden")
                
                for course_id in data['course_ids']:
                    self.main_window.db.execute(
                        """INSERT INTO student_courses 
                        (student_id, course_id, semester_id)
                        VALUES (?, ?, ?)""",
                        (student_id, course_id, semester_result['id'])
                    )
            
            return student_id
            
        except Exception as e:
            raise Exception(f"Fehler beim Erstellen des Schülers: {str(e)}")

    def update_student(self, student_id: int, data: dict) -> None:
        """Aktualisiert einen Schüler in der Datenbank"""
        try:
            self.main_window.db.execute(
                """UPDATE students 
                SET first_name = ?, last_name = ?
                WHERE id = ?""",
                (data['first_name'], data['last_name'], student_id)
            )
            
            # Kurszuordnungen aktualisieren
            semester = self.main_window.db.get_semester_dates()
            if not semester:
                raise ValueError("Kein aktives Semester gefunden")
                
            # Hole semester_id aus der Historie
            cursor = self.main_window.db.execute(
                """SELECT id FROM semester_history 
                WHERE start_date = ? AND end_date = ?""",
                (semester['semester_start'], semester['semester_end'])
            )
            semester_result = cursor.fetchone()
            if not semester_result:
                raise ValueError("Aktives Semester nicht in der Historie gefunden")
                
            # Lösche alte Zuordnungen
            self.main_window.db.execute(
                "DELETE FROM student_courses WHERE student_id = ? AND semester_id = ?",
                (student_id, semester_result['id'])
            )
            
            # Füge neue Zuordnungen hinzu
            for course_id in data['course_ids']:
                self.main_window.db.execute(
                    """INSERT INTO student_courses 
                    (student_id, course_id, semester_id)
                    VALUES (?, ?, ?)""",
                    (student_id, course_id, semester_result['id'])
                )
                
        except Exception as e:
            raise Exception(f"Fehler beim Aktualisieren des Schülers: {str(e)}")

    def refresh_students(self):
        """Aktualisiert die Schülerliste"""
        try:
            course_id = self.course_filter.currentData()
            
            if course_id:
                # Hole Schüler des ausgewählten Kurses
                semester = self.main_window.db.get_semester_dates()
                if not semester:
                    return
                    
                cursor = self.main_window.db.execute(
                    """SELECT DISTINCT s.* 
                    FROM students s
                    JOIN student_courses sc ON s.id = sc.student_id
                    JOIN semester_history sh ON sc.semester_id = sh.id
                    WHERE sc.course_id = ?
                    AND sh.start_date = ? AND sh.end_date = ?
                    ORDER BY s.last_name, s.first_name""",
                    (course_id, semester['semester_start'], semester['semester_end'])
                )
            else:
                # Hole alle Schüler
                cursor = self.main_window.db.execute(
                    """SELECT * FROM students 
                    ORDER BY last_name, first_name"""
                )
                
            students = cursor.fetchall()
            
            self.students_table.setRowCount(len(students))
            for row, student in enumerate(students):
                # Name
                self.students_table.setItem(
                    row, 0, 
                    QTableWidgetItem(student['last_name'])
                )
                self.students_table.setItem(
                    row, 1, 
                    QTableWidgetItem(student['first_name'])
                )
                
                # ID als userData speichern
                self.students_table.item(row, 0).setData(
                    Qt.ItemDataRole.UserRole, 
                    student['id']
                )
                
                # Kurse laden und anzeigen
                courses = self.get_student_courses(student['id'])
                self.students_table.setItem(
                    row, 2,
                    QTableWidgetItem(", ".join(courses))
                )
                
        except Exception as e:
            QMessageBox.critical(
                self,
                "Fehler",
                f"Fehler beim Laden der Schüler: {str(e)}"
            )


    def get_student_courses(self, student_id: int) -> list[str]:
        """Holt alle aktuellen Kurse eines Schülers"""
        try:
            semester = self.main_window.db.get_semester_dates()
            if not semester:
                return []
                
            cursor = self.main_window.db.execute(
                """SELECT DISTINCT c.name 
                FROM courses c
                JOIN student_courses sc ON c.id = sc.course_id
                JOIN semester_history sh ON sc.semester_id = sh.id
                WHERE sc.student_id = ?
                AND sh.start_date = ? AND sh.end_date = ?
                ORDER BY c.name""",
                (student_id, semester['semester_start'], semester['semester_end'])
            )
            
            return [row['name'] for row in cursor.fetchall()]
            
        except Exception as e:
            print(f"Fehler beim Laden der Kurse: {str(e)}")
            return []

    def filter_students(self, text: str):
        """Filtert die Schülerliste basierend auf der Sucheingabe"""
        for row in range(self.students_table.rowCount()):
            show = False
            for col in range(self.students_table.columnCount()):
                item = self.students_table.item(row, col)
                if item and text.lower() in item.text().lower():
                    show = True
                    break
            self.students_table.setRowHidden(row, not show)

    def on_student_selected(self):
        """Handler für Schülerauswahl"""
        selected = self.students_table.selectedItems()
        if not selected:
            return
            
        student_id = self.students_table.item(
            selected[0].row(), 0
        ).data(Qt.ItemDataRole.UserRole)
        
        self.load_student_details(student_id)

    def load_student_details(self, student_id: int):
        """Lädt alle Details für einen Schüler"""
        try:
            # Hole Schülerdetails
            cursor = self.main_window.db.execute(
                "SELECT first_name, last_name FROM students WHERE id = ?",
                (student_id,)
            )
            student = cursor.fetchone()
            
            # Hole Kurse des Schülers
            courses = self.get_student_courses(student_id)
            
            # Aktualisiere Header
            header_text = f"{student['first_name']} {student['last_name']}"
            if courses:
                header_text += f" ({', '.join(courses)})"
            self.student_header.setText(header_text)
            self.student_header.setVisible(True)
            
            # Details laden
            self.remarks_widget.current_student_id = student_id
            self.remarks_widget.load_remarks(student_id)
            self.grades_widget.current_student_id = student_id
            self.grades_widget.load_grades(student_id)
            self.analysis_widget.current_student_id = student_id
            self.analysis_widget.load_analysis(student_id)
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Fehler", 
                f"Fehler beim Laden der Schülerdetails: {str(e)}"
            )