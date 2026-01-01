# src/views/student/analysis_widget.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPen, QBrush, QPainter
from PyQt6.QtCharts import (QChartView, QPolarChart, QSplineSeries, 
                           QValueAxis, QCategoryAxis)

class AnalysisWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent.main_window
        self.current_student_id = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

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
            "Kurs", "Gesamt", "Sachkompetenz", "Methodenkompetenz",
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

    def load_analysis(self, student_id: int):
        try:
            self.current_student_id = student_id
            # Reset all displays
            self.type_grades_table.setRowCount(0)
            self.course_grades_table.setRowCount(0)
            self.radar_chart.removeAllSeries()

            # Get data
            course_grades = self.main_window.db.get_student_course_grades(student_id)
            course_competencies = self.main_window.db.get_student_competency_grades(student_id)

            # Only update if there's data
            if course_grades and any(grade.get('final_grade') is not None for grade in course_grades.values()):
                self.update_tables(course_grades, course_competencies)
                self.update_radar_chart(course_competencies)

        except Exception as e:
            print(f"DEBUG Analysis Error: {str(e)}")
            raise

    def update_tables(self, course_grades, competency_data):
        # Reset tables first
        self.type_grades_table.setRowCount(0)
        self.course_grades_table.setRowCount(0)

        """Aktualisiert die Tabellen mit den berechneten Noten"""
        # Spalten für die Tabelle einrichten
        num_columns = 2 + len(competency_data['areas'])
        self.course_grades_table.setColumnCount(num_columns)
        
        # Spaltenüberschriften
        headers = ['Kurs', 'Gesamt'] + competency_data['areas']
        self.course_grades_table.setHorizontalHeaderLabels(headers)

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
                    item.setBackground(self.get_grade_color(grade))
                else:
                    item = QTableWidgetItem("-")
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    
                self.course_grades_table.setItem(row, col, item)

        # Assessment Types laden und anzeigen
        for course_id in course_grades.keys():
            type_grades = self.main_window.db.get_student_assessment_type_grades(
                self.current_student_id, course_id
            )
            self.update_type_grades_table(type_grades)
            break  # Erstmal nur für einen Kurs
        
            # Only show type grades if we have any grades
        has_grades = False
        for course_id, course_data in course_grades.items():
            if course_data.get('final_grade') is not None:
                type_grades = self.main_window.db.get_student_assessment_type_grades(
                    self.current_student_id, course_id
                )
                if type_grades:
                    self.update_type_grades_table(type_grades)
                    has_grades = True
                    break

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
                avg_item.setBackground(self.get_grade_color(avg))
            else:
                avg_item = QTableWidgetItem("-")
                avg_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            self.type_grades_table.setItem(row, 1, avg_item)
            
            # Gewichtung
            weight_item = QTableWidgetItem(f"{grade_data['weight']}")
            weight_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.type_grades_table.setItem(row, 2, weight_item)

    def get_grade_color(self, grade: float) -> QColor:
        """Gibt die Hintergrundfarbe für eine Note zurück"""
        if grade <= 2.0:
            return QColor(200, 255, 200)
        elif grade <= 3.0:
            return QColor(220, 255, 220)
        elif grade <= 4.0:
            return QColor(255, 255, 200)
        elif grade <= 5.0:
            return QColor(255, 220, 220)
        else:
            return QColor(255, 200, 200)

    def update_radar_chart(self, competency_data):
        """Aktualisiert das Radar-Chart mit den Kompetenzdaten"""
        if not competency_data['areas']:
            print("DEBUG: No competency areas found")
            return

        # Chart neu erstellen
        self.radar_chart = QPolarChart()
        self.radar_series = QSplineSeries()
        self.radar_series.setName("Durchschnittsnote")

        # Visuelle Gestaltung
        pen = QPen(QColor("#1e88e5"))
        pen.setWidth(3)
        self.radar_series.setPen(pen)
        
        brush = QBrush(QColor("#1e88e5"))
        brush.setStyle(Qt.BrushStyle.SolidPattern)
        self.radar_series.setBrush(brush)
        self.radar_series.setOpacity(0.3)

        # Achsen einrichten
        angular_axis = QCategoryAxis()
        radial_axis = QValueAxis()
        
        radial_axis.setRange(1, 6)
        radial_axis.setReverse(True)
        radial_axis.setTitleText("Note")
        radial_axis.setLabelFormat("%.1f")
        radial_axis.setMinorTickCount(1)
        radial_axis.setGridLineVisible(True)
        radial_axis.setMinorGridLineVisible(True)

        # Grid-Linien konfigurieren
        grid_pen = QPen(QColor("#E0E0E0"))
        grid_pen.setWidth(1)
        radial_axis.setGridLinePen(grid_pen)
        
        minor_grid_pen = QPen(QColor("#F5F5F5"))
        minor_grid_pen.setWidth(1)
        radial_axis.setMinorGridLinePen(minor_grid_pen)

        angular_axis.setGridLineVisible(True)
        angular_axis.setGridLinePen(grid_pen)

        # Datenpunkte berechnen und hinzufügen
        self.add_data_points(competency_data, angular_axis)

        # Chart zusammenbauen
        self.radar_chart.addAxis(angular_axis, QPolarChart.PolarOrientation.PolarOrientationAngular)
        self.radar_chart.addAxis(radial_axis, QPolarChart.PolarOrientation.PolarOrientationRadial)
        self.radar_chart.addSeries(self.radar_series)
        self.radar_series.attachAxis(angular_axis)
        self.radar_series.attachAxis(radial_axis)
        
        self.chart_view.setChart(self.radar_chart)

    def add_data_points(self, competency_data, angular_axis):
        """Fügt die Datenpunkte zum Radar-Chart hinzu"""
        num_areas = len(competency_data['areas'])
        angle_step = 360.0 / num_areas

        # Durchschnitt pro Kompetenzbereich berechnen
        area_averages = {}
        for course in competency_data['grades']:
            for area, grade in course['competencies'].items():
                if area not in area_averages:
                    area_averages[area] = {'sum': 0.0, 'count': 0}
                area_averages[area]['sum'] += grade
                area_averages[area]['count'] += 1

        # Punkte hinzufügen
        for i, area in enumerate(competency_data['areas']):
            angle = i * angle_step
            if area_averages[area]['count'] > 0:
                avg = area_averages[area]['sum'] / area_averages[area]['count']
                self.radar_series.append(angle, avg)
                angular_axis.append(area, angle)

        # Kreis schließen
        if self.radar_series.count() > 0:
            first_point = self.radar_series.at(0)
            self.radar_series.append(360.0, first_point.y())