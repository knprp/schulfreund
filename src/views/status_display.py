# src/views/status_display.py

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt6.QtCore import QDate

class StatusDisplay:
    """Verwaltet die permanenten Anzeigen in der Statusbar"""
    
    def __init__(self, main_window):
        self.main_window = main_window
        
class StatusDisplay:
    def __init__(self, main_window):
        self.main_window = main_window
        # Erstelle ein permanentes Widget für das Semester
        self.semester_widget = QWidget()
        self.semester_layout = QHBoxLayout(self.semester_widget)
        self.semester_layout.setContentsMargins(0, 0, 0, 0)
        self.semester_label = QLabel()
        self.semester_layout.addWidget(self.semester_label)
        self.main_window.statusBar().addPermanentWidget(self.semester_widget)

    def update_semester_display(self):
        """Aktualisiert die Anzeige des aktuellen Semesters in der Statusbar"""
        try:
            semester = self.main_window.db.get_semester_dates()
            
            if semester:
                start = QDate.fromString(semester['semester_start'], "yyyy-MM-dd")
                end = QDate.fromString(semester['semester_end'], "yyyy-MM-dd")
                current = QDate.currentDate()
                
                days_until_end = current.daysTo(end)
                
                semester_text = f"Aktuelles Semester: {start.toString('dd.MM.yyyy')} - {end.toString('dd.MM.yyyy')}"
                self.semester_label.setText(semester_text)
                
                if days_until_end < 0:
                    self.semester_label.setStyleSheet("color: red;")
                    self.semester_label.setToolTip("Semester ist bereits abgelaufen!")
                elif days_until_end <= 14:
                    self.semester_label.setStyleSheet("color: orange;")
                    self.semester_label.setToolTip(f"Semester endet in {days_until_end} Tagen!")
                else:
                    self.semester_label.setStyleSheet("color: black;")
                    self.semester_label.setToolTip(f"Noch {days_until_end} Tage bis zum Semesterende")
                
            else:
                self.semester_label.setText("Kein aktives Semester")
                self.semester_label.setStyleSheet("color: gray;")
                self.semester_label.setToolTip("")
                
        except Exception as e:
            print(f"Fehler beim Aktualisieren der Semesteranzeige: {str(e)}")