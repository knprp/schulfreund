from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
                           QTableWidget, QTableWidgetItem, QHeaderView,
                           QPushButton, QLabel, QLineEdit, QMessageBox,
                           QComboBox)
from PyQt6.QtCore import Qt
from PyQt6.QtCharts import QChart, QChartView, QPolarChart, QSplineSeries, QValueAxis, QCategoryAxis
from PyQt6.QtGui import QPen, QColor, QPainter, QBrush
import math

from src.views.dialogs.student_dialog import StudentDialog


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

        self.detail_tabs = QTabWidget()
        
        # Tab 1: Bemerkungen
        self.remarks_widget = self.setup_remarks_tab()
        self.detail_tabs.addTab(self.remarks_widget, "Bemerkungen")
        
        # Tab 2: Notenübersicht
        self.grades_widget = self.setup_grades_tab()
        self.detail_tabs.addTab(self.grades_widget, "Noten")
        
        # Tab 3: Notenanalyse
        self.analysis_widget = self.setup_analysis_tab()
        self.detail_tabs.addTab(self.analysis_widget, "Analyse")

        right_layout.addWidget(self.detail_tabs)

        # Splitter hinzufügen
        layout.addWidget(left_widget, 1)  # Stretch-Faktor 1
        layout.addWidget(right_widget, 2)  # Stretch-Faktor 2

        self.refresh_all()

    def setup_remarks_tab(self) -> QWidget:
        """Erstellt den Tab für Bemerkungen"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Tabelle für Bemerkungen
        self.remarks_table = QTableWidget()
        self.remarks_table.setColumnCount(3)
        self.remarks_table.setHorizontalHeaderLabels(["Datum", "Typ", "Bemerkung"])
        self.remarks_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.remarks_table)

        # Buttons für Bemerkungen
        button_layout = QHBoxLayout()
        
        add_remark_btn = QPushButton("Bemerkung hinzufügen")
        add_remark_btn.clicked.connect(self.add_remark)
        button_layout.addWidget(add_remark_btn)
        
        delete_remark_btn = QPushButton("Bemerkung löschen")
        delete_remark_btn.clicked.connect(self.delete_remark)
        button_layout.addWidget(delete_remark_btn)
        
        layout.addLayout(button_layout)

        return widget

    def setup_grades_tab(self) -> QWidget:
        """Erstellt den Tab für die detaillierte Notenübersicht"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Tabelle für Einzelnoten
        self.grades_table = QTableWidget()
        self.grades_table.setColumnCount(6)
        self.grades_table.setHorizontalHeaderLabels([
            "Datum", "Kurs", "Typ", "Note", "Thema", "Bemerkung"
        ])
        
        # Spaltenbreiten konfigurieren
        header = self.grades_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Datum
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)  # Kurs
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)  # Typ
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Note
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)  # Thema
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)  # Bemerkung

        self.grades_table.setColumnWidth(1, 120)  # Kurs
        self.grades_table.setColumnWidth(2, 100)  # Typ

        layout.addWidget(self.grades_table)
        return widget

    def setup_analysis_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Grundlegende Statistiken
        stats_layout = QHBoxLayout()
        
        # Durchschnittsnote
        avg_box = QWidget()
        avg_layout = QVBoxLayout(avg_box)
        avg_layout.addWidget(QLabel("<b>Durchschnitt</b>"))
        self.avg_label = QLabel("-")
        self.avg_label.setStyleSheet("font-size: 24px;")
        avg_layout.addWidget(self.avg_label)
        stats_layout.addWidget(avg_box)
        
        layout.addLayout(stats_layout)

        # Assessment Types Tabelle
        layout.addWidget(QLabel("<b>Noten nach Bewertungstyp</b>"))
        self.type_grades_table = QTableWidget()
        self.type_grades_table.setColumnCount(3)
        self.type_grades_table.setHorizontalHeaderLabels([
            "Bewertungstyp", "Durchschnitt", "Gewichtung"
        ])
        
        header = self.type_grades_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Typ
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)    # Durchschnitt
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)    # Gewichtung
        
        self.type_grades_table.setColumnWidth(1, 100)  # Durchschnitt
        self.type_grades_table.setColumnWidth(2, 100)  # Gewichtung
        
        layout.addWidget(self.type_grades_table)

        # Notenverteilung pro Kurs
        layout.addWidget(QLabel("<b>Notenverteilung pro Kurs</b>"))
        self.course_grades_table = QTableWidget()
        self.course_grades_table.setColumnCount(6)
        self.course_grades_table.setHorizontalHeaderLabels([
            "Kurs", "Gesamt", "Fachkompetenz", "Methodenkompetenz",
            "Sozialkompetenz", "Selbstkompetenz"
        ])
        
        header = self.course_grades_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # Kurs
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)  # Gesamt
        for i in range(2, 6):  # Kompetenzbereiche
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)

        self.course_grades_table.setColumnWidth(0, 120)  # Kurs
        self.course_grades_table.setColumnWidth(1, 80)   # Gesamt

        layout.addWidget(self.course_grades_table)

        # Radar Chart
        layout.addWidget(QLabel("<b>Kompetenzbereiche</b>"))
        self.radar_chart = QPolarChart()
        self.radar_series = QSplineSeries()
        self.chart_view = QChartView(self.radar_chart)
        self.chart_view.setMinimumHeight(400)
        self.chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        layout.addWidget(self.chart_view)

        return widget
        
    def update_analysis_ui(self, course_grades, competency_data):
        """Aktualisiert die UI mit den berechneten Noten"""
        # Spalten für die Tabelle einrichten
        num_columns = 2 + len(competency_data['areas'])  # Kurs + Gesamt + Kompetenzbereiche
        self.course_grades_table.setColumnCount(num_columns)
        
        # Spaltenüberschriften
        headers = ['Kurs', 'Gesamt'] + competency_data['areas']
        self.course_grades_table.setHorizontalHeaderLabels(headers)
        
        # Spaltenbreiten
        header = self.course_grades_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # Kurs
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)  # Gesamt
        for i in range(2, num_columns):  # Kompetenzbereiche
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)

        self.course_grades_table.setColumnWidth(0, 120)  # Kurs
        self.course_grades_table.setColumnWidth(1, 80)   # Gesamt

        # Zeilen füllen
        self.course_grades_table.setRowCount(len(competency_data['grades']))
        
        for row, course_data in enumerate(competency_data['grades']):
            # Kursname
            self.course_grades_table.setItem(
                row, 0, 
                QTableWidgetItem(course_data['course_name'])
            )
            
            # Gesamtnote
            course_grade = course_grades.get(course_data['course_id'], {}).get('final_grade')
            grade_item = QTableWidgetItem(str(round(course_grade, 2)) if course_grade else "-")
            grade_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.course_grades_table.setItem(row, 1, grade_item)
            
            # Kompetenzbereiche
            for col, area in enumerate(competency_data['areas'], start=2):
                grade = course_data['competencies'].get(area)
                if grade is not None:
                    item = QTableWidgetItem(f"{round(grade, 2)}")
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    
                    # Farbliche Hervorhebung
                    grade_value = float(grade)
                    if grade_value <= 2.0:
                        item.setBackground(QColor(200, 255, 200))
                    elif grade_value <= 3.0:
                        item.setBackground(QColor(220, 255, 220))
                    elif grade_value <= 4.0:
                        item.setBackground(QColor(255, 255, 200))
                    elif grade_value <= 5.0:
                        item.setBackground(QColor(255, 220, 220))
                    else:
                        item.setBackground(QColor(255, 200, 200))
                else:
                    item = QTableWidgetItem("-")
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    
                self.course_grades_table.setItem(row, col, item)

        # Assessment Types laden und anzeigen
        for course_id in course_grades.keys():  # Wir nehmen den ersten Kurs
            type_grades = self.main_window.db.get_student_assessment_type_grades(
                self.current_student_id, course_id
            )
            self.update_type_grades_table(type_grades)
            break  # Erstmal nur für einen Kurs

    def update_type_grades_table(self, type_grades: list):
        """Aktualisiert die Assessment Type Tabelle"""
        self.type_grades_table.setRowCount(len(type_grades))
        
        for row, grade_data in enumerate(type_grades):
            # Name mit Einrückung je nach Level
            indent = "    " * grade_data['level']
            name_item = QTableWidgetItem(indent + grade_data['name'])
            self.type_grades_table.setItem(row, 0, name_item)
            
            # Durchschnitt
            if grade_data['average_grade'] is not None:
                avg = round(grade_data['average_grade'], 2)
                avg_item = QTableWidgetItem(str(avg))
                avg_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                
                # Farbliche Hervorhebung wie bei den anderen Noten
                if avg <= 2.0:
                    avg_item.setBackground(QColor(200, 255, 200))
                elif avg <= 3.0:
                    avg_item.setBackground(QColor(220, 255, 220))
                elif avg <= 4.0:
                    avg_item.setBackground(QColor(255, 255, 200))
                elif avg <= 5.0:
                    avg_item.setBackground(QColor(255, 220, 220))
                else:
                    avg_item.setBackground(QColor(255, 200, 200))
            else:
                avg_item = QTableWidgetItem("-")
                avg_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            self.type_grades_table.setItem(row, 1, avg_item)
            
            # Gewichtung
            weight_item = QTableWidgetItem(f"{grade_data['weight']}")
            weight_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.type_grades_table.setItem(row, 2, weight_item)

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

    def add_remark(self):
        """Öffnet den Dialog zum Hinzufügen einer Bemerkung"""
        try:
            if not self.current_student_id:
                return
                
            from src.views.dialogs.remark_dialog import RemarkDialog
            dialog = RemarkDialog(self.main_window)
            
            if dialog.exec():
                data = dialog.get_data()
                self.main_window.db.execute(
                    """INSERT INTO student_remarks 
                    (student_id, type, remark_text)
                    VALUES (?, ?, ?)""",
                    (self.current_student_id, data['type'], data['text'])
                )
                self.load_remarks(self.current_student_id)
                
        except Exception as e:
            QMessageBox.critical(
                self,
                "Fehler",
                f"Fehler beim Hinzufügen der Bemerkung: {str(e)}"
            )

    def delete_remark(self):
        """Löscht die ausgewählte Bemerkung"""
        try:
            selected = self.remarks_table.selectedItems()
            if not selected:
                return
                
            row = selected[0].row()
            date = self.remarks_table.item(row, 0).text()
            text = self.remarks_table.item(row, 2).text()
            
            reply = QMessageBox.question(
                self,
                'Bemerkung löschen',
                f'Möchten Sie die Bemerkung vom {date} wirklich löschen?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.main_window.db.execute(
                    """DELETE FROM student_remarks 
                    WHERE student_id = ? AND created_at = ?""",
                    (self.current_student_id, date)
                )
                self.load_remarks(self.current_student_id)
                
        except Exception as e:
            QMessageBox.critical(
                self,
                "Fehler",
                f"Fehler beim Löschen der Bemerkung: {str(e)}"
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
        self.load_remarks(student_id)
        self.load_grades(student_id)
        self.load_analysis(student_id)

    def load_remarks(self, student_id: int):
        """Lädt die Bemerkungen eines Schülers"""
        try:
            cursor = self.main_window.db.execute(
                """SELECT created_at, type, remark_text 
                FROM student_remarks
                WHERE student_id = ?
                ORDER BY created_at DESC""",
                (student_id,)
            )
            remarks = cursor.fetchall()
            
            self.remarks_table.setRowCount(len(remarks))
            for row, remark in enumerate(remarks):
                self.remarks_table.setItem(
                    row, 0,
                    QTableWidgetItem(remark['created_at'])
                )
                self.remarks_table.setItem(
                    row, 1,
                    QTableWidgetItem(remark['type'])
                )
                self.remarks_table.setItem(
                    row, 2,
                    QTableWidgetItem(remark['remark_text'])
                )
                
        except Exception as e:
            QMessageBox.critical(
                self,
                "Fehler",
                f"Fehler beim Laden der Bemerkungen: {str(e)}"
            )

    def load_grades(self, student_id: int):
        """Lädt die Einzelnoten eines Schülers"""
        try:
            cursor = self.main_window.db.execute(
                """SELECT 
                    a.date,
                    c.name as course_name,
                    at.name as type_name,
                    a.grade,
                    COALESCE(a.topic, '') as topic,
                    COALESCE(a.comment, '') as comment
                FROM assessments a
                JOIN courses c ON a.course_id = c.id
                JOIN assessment_types at ON a.assessment_type_id = at.id
                WHERE a.student_id = ?
                ORDER BY a.date DESC""",
                (student_id,)
            )
            grades = cursor.fetchall()
            
            self.grades_table.setRowCount(len(grades))
            for row, grade in enumerate(grades):
                # Datum
                self.grades_table.setItem(
                    row, 0,
                    QTableWidgetItem(grade['date'])
                )
                # Kurs
                self.grades_table.setItem(
                    row, 1,
                    QTableWidgetItem(grade['course_name'])
                )
                # Typ
                self.grades_table.setItem(
                    row, 2,
                    QTableWidgetItem(grade['type_name'])
                )
                
                # Note mit Färbung
                grade_item = QTableWidgetItem(str(grade['grade']))
                grade_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                
                # Farbgebung basierend auf Note
                grade_value = float(grade['grade'])
                if grade_value <= 2.0:
                    grade_item.setBackground(QColor(200, 255, 200))
                elif grade_value <= 3.0:
                    grade_item.setBackground(QColor(220, 255, 220))
                elif grade_value <= 4.0:
                    grade_item.setBackground(QColor(255, 255, 200))
                elif grade_value <= 5.0:
                    grade_item.setBackground(QColor(255, 220, 220))
                else:
                    grade_item.setBackground(QColor(255, 200, 200))
                
                self.grades_table.setItem(row, 3, grade_item)
                
                # Thema und Bemerkung
                self.grades_table.setItem(
                    row, 4,
                    QTableWidgetItem(grade['topic'])
                )
                self.grades_table.setItem(
                    row, 5,
                    QTableWidgetItem(grade['comment'])
                )
                
        except Exception as e:
            QMessageBox.critical(
                self,
                "Fehler",
                f"Fehler beim Laden der Noten: {str(e)}"
            )

    def load_analysis(self, student_id: int):
        """Lädt und zeigt die Notenanalyse für einen Schüler"""
        try:
            self.current_student_id = student_id

            # Hole Daten aus dem DB-Manager
            course_grades = self.main_window.db.get_student_course_grades(student_id)
            course_competencies = self.main_window.db.get_student_competency_grades(student_id)

            # Update UI
            self.update_analysis_ui(course_grades, course_competencies)
            
            # Radar Chart aktualisieren
            self.load_competency_analysis(student_id)  # Diese Zeile fehlte!

        except Exception as e:
            print(f"DEBUG Analysis Error: {str(e)}")
            QMessageBox.critical(
                self, "Fehler", f"Fehler bei der Notenanalyse: {str(e)}"
            )

    def load_competency_analysis(self, student_id: int):
        try:
            # Hole die Kompetenzdaten über die neue Methode
            competency_data = self.main_window.db.get_student_competency_grades(student_id)
            
            if not competency_data['areas']:
                print("DEBUG: No competency areas found")
                return

            # Chart komplett neu erstellen
            self.radar_chart = QPolarChart()
            self.radar_series = QSplineSeries()
            self.radar_series.setName("Durchschnittsnote")

            # Visuelle Verbesserungen
            pen = QPen()
            pen.setWidth(3)
            pen.setColor(QColor("#1e88e5"))
            self.radar_series.setPen(pen)
            
            # Fläche füllen
            brush = QBrush(QColor("#1e88e5"))
            brush.setStyle(Qt.BrushStyle.SolidPattern)
            self.radar_series.setBrush(brush)
            self.radar_series.setOpacity(0.3)

            # Achsen
            self.angular_axis = QCategoryAxis()
            self.radial_axis = QValueAxis()
            
            # Achseneigenschaften setzen
            self.radial_axis.setRange(1, 6)  # Notenbereich
            self.radial_axis.setReverse(True)  # 6 innen, 1 außen
            self.radial_axis.setTitleText("Note")
            self.radial_axis.setLabelFormat("%.1f")

            # Grid-Linien konfigurieren
            self.radial_axis.setMinorTickCount(1)
            self.radial_axis.setGridLineVisible(True)
            self.radial_axis.setMinorGridLineVisible(True)

            # Grid-Linien-Style anpassen
            major_grid_pen = QPen(QColor("#E0E0E0"))
            major_grid_pen.setWidth(1)
            self.radial_axis.setGridLinePen(major_grid_pen)

            minor_grid_pen = QPen(QColor("#F5F5F5"))
            minor_grid_pen.setWidth(1)
            self.radial_axis.setMinorGridLinePen(minor_grid_pen)

            # Winkel-Achse Grid-Linien
            self.angular_axis.setGridLineVisible(True)
            self.angular_axis.setGridLinePen(major_grid_pen)

            # Punkte berechnen und hinzufügen
            num_areas = len(competency_data['areas'])
            angle_step = 360.0 / num_areas

            # Berechne Durchschnitt pro Kompetenzbereich über alle Kurse
            area_averages = {}
            for course in competency_data['grades']:
                for area, grade in course['competencies'].items():
                    if area not in area_averages:
                        area_averages[area] = {'sum': 0.0, 'count': 0}
                    area_averages[area]['sum'] += grade
                    area_averages[area]['count'] += 1

            print("DEBUG: Area averages:", area_averages)  # Debug output

            # Punkte zum Chart hinzufügen
            for i, area in enumerate(competency_data['areas']):
                angle = i * angle_step
                avg = (area_averages[area]['sum'] / area_averages[area]['count'] 
                    if area_averages[area]['count'] > 0 else 0)
                
                print(f"DEBUG: Adding point - Area: {area}, Angle: {angle}, Value: {avg}")  # Debug
                
                if avg > 0:  # Nur Punkte hinzufügen wenn es einen Wert gibt
                    self.radar_series.append(angle, avg)
                    self.angular_axis.append(area, angle)

            # Schließe den Kreis wenn es Daten gibt
            if self.radar_series.count() > 0:
                first_point = self.radar_series.at(0)
                self.radar_series.append(360.0, first_point.y())

            # Chart aufbauen
            self.radar_chart.addAxis(self.angular_axis, QPolarChart.PolarOrientation.PolarOrientationAngular)
            self.radar_chart.addAxis(self.radial_axis, QPolarChart.PolarOrientation.PolarOrientationRadial)
            self.radar_chart.addSeries(self.radar_series)
            self.radar_series.attachAxis(self.angular_axis)
            self.radar_series.attachAxis(self.radial_axis)
            
            # ChartView aktualisieren
            self.chart_view.setChart(self.radar_chart)
            print("DEBUG: Points in series:", [
                (p.x(), p.y()) for p in self.radar_series.points()
            ])

        except Exception as e:
            print("DEBUG: Exception in load_competency_analysis:", str(e))
            raise