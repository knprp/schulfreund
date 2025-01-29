from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
                           QTableWidget, QTableWidgetItem, QHeaderView,
                           QPushButton, QLabel, QLineEdit, QMessageBox,
                           QComboBox)
from PyQt6.QtCore import Qt
from PyQt6.QtCharts import QChart, QChartView, QPolarChart, QSplineSeries, QValueAxis, QCategoryAxis
from PyQt6.QtGui import QPen, QColor, QPainter
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
        """Erstellt den Tab für die Notenübersicht"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Tabelle für Noten
        self.grades_table = QTableWidget()
        self.grades_table.setColumnCount(5)
        self.grades_table.setHorizontalHeaderLabels([
            "Datum", "Kurs", "Typ", "Note", "Bemerkung"
        ])
        header = self.grades_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.grades_table)

        return widget

    def setup_analysis_tab(self) -> QWidget:
        """Erstellt den Tab für die Notenanalyse"""
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
        
        # Beste Note
        best_box = QWidget()
        best_layout = QVBoxLayout(best_box)
        best_layout.addWidget(QLabel("<b>Beste Note</b>"))
        self.best_label = QLabel("-")
        self.best_label.setStyleSheet("font-size: 24px;")
        best_layout.addWidget(self.best_label)
        stats_layout.addWidget(best_box)
        
        # Schlechteste Note
        worst_box = QWidget()
        worst_layout = QVBoxLayout(worst_box)
        worst_layout.addWidget(QLabel("<b>Schlechteste Note</b>"))
        self.worst_label = QLabel("-")
        self.worst_label.setStyleSheet("font-size: 24px;")
        worst_layout.addWidget(self.worst_label)
        stats_layout.addWidget(worst_box)

        layout.addLayout(stats_layout)
        
        # Notenverteilung pro Kurs
        layout.addWidget(QLabel("<b>Notenverteilung pro Kurs</b>"))
        self.course_grades_table = QTableWidget()
        self.course_grades_table.setColumnCount(4)
        self.course_grades_table.setHorizontalHeaderLabels([
            "Kurs", "Durchschnitt", "Beste", "Schlechteste"
        ])
        self.course_grades_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        layout.addWidget(self.course_grades_table)

        # Chart erstellen
        self.radar_chart = QPolarChart()
        self.radar_series = QSplineSeries()
        self.radar_series.setName("Durchschnittsnote")  # Name für Legende
        
        # Achsen
        self.angular_axis = QCategoryAxis()
        self.radial_axis = QValueAxis()
        
        # Achseneigenschaften setzen
        self.radial_axis.setReverse(True)  # 6 innen, 1 außen
        self.radial_axis.setTitleText("Note")
        self.radial_axis.setLabelFormat("%.1f")
        
        # Chart-Eigenschaften
        self.radar_chart.legend().setVisible(True)
        self.radar_chart.setTitle("Leistung nach Kompetenzbereichen")
        
        # Achsen hinzufügen
        self.radar_chart.addAxis(self.angular_axis, QPolarChart.PolarOrientation.PolarOrientationAngular)
        self.radar_chart.addAxis(self.radial_axis, QPolarChart.PolarOrientation.PolarOrientationRadial)
        
        self.radar_chart.addSeries(self.radar_series)
        self.radar_series.attachAxis(self.angular_axis)
        self.radar_series.attachAxis(self.radial_axis)
        
        # Serienfarbe und -stil
        pen = self.radar_series.pen()
        pen.setWidth(2)
        pen.setColor(QColor("#2563eb"))  # Schönes Blau
        self.radar_series.setPen(pen)
        
        # ChartView
        chart_view = QChartView(self.radar_chart)
        chart_view.setMinimumHeight(400)  # Etwas größer
        chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)  # Bessere Qualität
        layout.addWidget(chart_view)

        return widget

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
        """Lädt die Noten eines Schülers"""
        try:
            cursor = self.main_window.db.execute(
                """SELECT 
                    a.date,
                    c.name as course_name,
                    at.name as type_name,
                    a.grade,
                    COALESCE(a.topic, '') as comment
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
                self.grades_table.setItem(
                    row, 0,
                    QTableWidgetItem(grade['date'])
                )
                self.grades_table.setItem(
                    row, 1,
                    QTableWidgetItem(grade['course_name'])
                )
                self.grades_table.setItem(
                    row, 2,
                    QTableWidgetItem(grade['type_name'])
                )
                self.grades_table.setItem(
                    row, 3,
                    QTableWidgetItem(str(grade['grade']))
                )
                self.grades_table.setItem(
                    row, 4,
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
            # Gesamtstatistik
            cursor = self.main_window.db.execute(
                """SELECT 
                    ROUND(AVG(grade), 2) as average,
                    MIN(grade) as best,
                    MAX(grade) as worst
                FROM assessments
                WHERE student_id = ?""", 
                (student_id,)
            )
            overall_stats = cursor.fetchone()
            
            # Labels aktualisieren
            if overall_stats and overall_stats['average']:
                self.avg_label.setText(f"{overall_stats['average']}")
                self.best_label.setText(f"{overall_stats['best']}")
                self.worst_label.setText(f"{overall_stats['worst']}")
            else:
                self.avg_label.setText("-")
                self.best_label.setText("-")
                self.worst_label.setText("-")

            # Statistik pro Kurs
            cursor = self.main_window.db.execute(
                """SELECT 
                    c.name as course_name,
                    ROUND(AVG(a.grade), 2) as average,
                    MIN(a.grade) as best,
                    MAX(a.grade) as worst,
                    COUNT(a.id) as count
                FROM assessments a
                JOIN courses c ON a.course_id = c.id
                WHERE a.student_id = ?
                GROUP BY c.id
                HAVING count > 0
                ORDER BY c.name""",
                (student_id,)
            )
            course_stats = cursor.fetchall()
            
            # Tabelle aktualisieren
            self.course_grades_table.setRowCount(len(course_stats))
            for row, stats in enumerate(course_stats):
                self.course_grades_table.setItem(
                    row, 0,
                    QTableWidgetItem(stats['course_name'])
                )
                self.course_grades_table.setItem(
                    row, 1,
                    QTableWidgetItem(str(stats['average']))
                )
                self.course_grades_table.setItem(
                    row, 2,
                    QTableWidgetItem(str(stats['best']))
                )
                self.course_grades_table.setItem(
                    row, 3,
                    QTableWidgetItem(str(stats['worst']))
                )

                # Formatierung der Noten
                for col in range(1, 4):
                    item = self.course_grades_table.item(row, col)
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    
        except Exception as e:
            QMessageBox.critical(
                self,
                "Fehler",
                f"Fehler bei der Notenanalyse: {str(e)}"
            )

        # Lade und zeige Kompetenzanalyse
        competency_data = self.load_competency_analysis(student_id)
        if competency_data:
            html = f"""
            <div id="radar-root"></div>
            <script>
                const data = {json.dumps(competency_data)};
                ReactDOM.render(
                    React.createElement(CompetencyRadar, {{ data: data }}),
                    document.getElementById('radar-root')
                );
            </script>
            """
            self.radar_view.setHtml(html)

    def load_competency_analysis(self, student_id: int):
        """Lädt und aktualisiert den Radar-Chart mit Kompetenzdaten"""
        try:
            cursor = self.main_window.db.execute(
                """SELECT 
                    c.area as competency_area,
                    ROUND(AVG(a.grade), 2) as average_grade,
                    COUNT(*) as count
                FROM assessments a
                JOIN lessons l ON a.lesson_id = l.id 
                JOIN lesson_competencies lc ON l.id = lc.lesson_id
                JOIN competencies c ON lc.competency_id = c.id
                WHERE a.student_id = ?
                GROUP BY c.area""",
                (student_id,)
            )
            competency_data = [dict(row) for row in cursor.fetchall()]
            
            # Chart aktualisieren
            self.radar_series.clear()
            
            # Kategorien entfernen und neu setzen
            categories = self.angular_axis.categoriesLabels()
            for category in categories:
                self.angular_axis.remove(category)
            
            # Daten hinzufügen
            for i, data in enumerate(competency_data):
                self.radar_series.append(i, data['average_grade'])
                self.angular_axis.append(data['competency_area'], i)
            
            # Achsen anpassen
            self.radial_axis.setRange(1, 6)  # Notenskala
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Fehler",
                f"Fehler beim Laden der Kompetenzanalyse: {str(e)}"
            )