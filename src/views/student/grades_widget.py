# src/views/student/grades_widget.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTableWidget, 
                           QTableWidgetItem, QHeaderView, QMessageBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

class GradesWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent.main_window
        self.current_student_id = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

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

        # Doppelklick-Handler hinzufügen
        self.grades_table.itemDoubleClicked.connect(self.on_grade_double_clicked)

        layout.addWidget(self.grades_table)

    def load_grades(self, student_id: int):
        """Lädt die Einzelnoten eines Schülers"""
        try:
            self.current_student_id = student_id
            # Lade Noten über Controller
            grades = self.main_window.controllers.student.get_student_assessments(student_id)
            
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

    def on_grade_double_clicked(self, item):
        """Öffnet den LessonDetailsDialog für die ausgewählte Note"""
        try:
            row = item.row()
            date = self.grades_table.item(row, 0).text()
            # Hole lesson_id über Controller
            lesson_id = self.main_window.controllers.student.get_lesson_id_for_assessment(
                self.current_student_id, date
            )
            
            if lesson_id:
                from src.views.dialogs.lesson_details_dialog import LessonDetailsDialog
                dialog = LessonDetailsDialog(self.main_window, lesson_id)
                # Zum Schüler-Tab wechseln
                dialog.tab_widget.setCurrentIndex(1)
                if dialog.exec():
                    # Noten nach Dialog-Schluss aktualisieren
                    self.load_grades(self.current_student_id)
        except Exception as e:
            QMessageBox.critical(
                self,
                "Fehler", 
                f"Fehler beim Öffnen der Stundendetails: {str(e)}"
            )