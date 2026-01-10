#!/usr/bin/env python3
import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                           QHBoxLayout, QTabWidget, QTableWidget, QPushButton,
                           QLineEdit, QComboBox, QLabel, QSpinBox, QTableWidgetItem,
                           QDialog, QDialogButtonBox, QCalendarWidget, QTimeEdit,
                           QMenu, QMenuBar, QMessageBox)
from PyQt6.QtCore import Qt, QTime, QDate
from PyQt6.QtGui import QIcon
from PyQt6 import uic
from pathlib import Path

from src.database.db_manager import DatabaseManager
from src.controllers import (
    StudentController,
    CourseController,
    LessonController,
    AssessmentController,
    SettingsController,
    SemesterController,
    SubjectController,
    CompetencyController,
    GradingSystemController,
    AssessmentTemplateController
)
from src.views.list_manager import ListManager
from src.views.tabs.course_tab import CourseTab
from src.views.tabs.student_tab import StudentTab
from src.views.tabs.competency_tab import CompetencyTab
from src.views.tabs.settings_tab import SettingsTab
from src.views.tabs.subject_tab import SubjectTab
from src.views.calendar_container import CalendarContainer
from src.views.status_display import StatusDisplay
from src.models.holiday_manager import HolidayManager

class SchoolManagement(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Datenbank initialisieren
        self.db = DatabaseManager()

        # Controller initialisieren
        self.controllers = type('Controllers', (), {})()
        self.controllers.student = StudentController(self.db)
        self.controllers.course = CourseController(self.db)
        self.controllers.lesson = LessonController(self.db)
        self.controllers.assessment = AssessmentController(self.db)
        self.controllers.settings = SettingsController(self.db)
        self.controllers.semester = SemesterController(self.db)
        self.controllers.subject = SubjectController(self.db)
        self.controllers.competency = CompetencyController(self.db)
        self.controllers.grading_system = GradingSystemController(self.db)
        self.controllers.assessment_template = AssessmentTemplateController(self.db)

        # Holiday Manager initialisieren und Daten laden
        self.holiday_manager = HolidayManager(self.db)
        self.holiday_manager.initialize_holidays()
        
        # UI aus .ui Datei laden
        uic.loadUi("school.ui", self)
        self.setWindowIcon(QIcon('favicon.ico'))

        # Setze den Kalender-Tab als Startansicht
        self.tabWidget.setCurrentIndex(0)
        
        # UI-Komponenten initialisieren (inkl. settings_tab)
        self.setup_ui()
        
        # Den CalendarContainer erstellen (der die WeekView enthält)
        self.setup_calendar_container()
        
        # ListManager für Kalenderansichten initialisieren
        self.list_manager = ListManager(self)
        
        # Status-Display initialisieren
        self.status_display = StatusDisplay(self)

        # Semester-Anzeige initialisieren
        self.status_display.update_semester_display()

        # Icon setzen - mehrere Versuche
        icon_path = Path('assets/icon.png')
        if icon_path.exists():
            icon = QIcon(str(icon_path))
            self.setWindowIcon(icon)
            # Explizit für Linux/X11/Wayland
            self.setAttribute(Qt.WidgetAttribute.WA_SetWindowIcon, True)
            QApplication.setWindowIcon(icon)  # Global für die ganze Anwendung
        else:
            print(f"Warning: Icon file not found at {icon_path}")
    
    def setup_calendar_container(self):
        """Ersetzt den alten Kalender mit dem neuen CalendarContainer"""
        # Alten Kalender und zugehörige Widgets aus dem Layout entfernen
        for widget in [self.calendarWidget, self.listView_tag, self.listView_fokus,
                      self.listView_ereignisse, self.label, self.label_2, 
                      self.label_3, self.label_4, self.label_5, self.label_6,
                      self.addLessonButton]:
            widget.setParent(None)
            widget.deleteLater()
        
        # Neuen CalendarContainer erstellen und einsetzen
        self.calendar_container = CalendarContainer(self)
        self.tab_kal.layout = QVBoxLayout(self.tab_kal)
        self.tab_kal.layout.setContentsMargins(0, 0, 0, 0)
        self.tab_kal.layout.addWidget(self.calendar_container)
        
    def setup_ui(self):
        """Initialisiert die Benutzeroberfläche"""
        # Tabs initialisieren
        self.setup_tabs()

    def setup_tabs(self):
        """Initialisiert alle Tab-Komponenten"""
        # Kurse-Tab
        self.course_tab = CourseTab(self)
        self.tab_kurse.setLayout(QVBoxLayout())  # Wichtig: setLayout statt .layout =
        self.tab_kurse.layout().addWidget(self.course_tab)
        
        # Schüler-Tab
        self.student_tab = StudentTab(self)
        self.tab_sus.setLayout(QVBoxLayout())
        self.tab_sus.layout().addWidget(self.student_tab)

        # FächerTab
        self.subject_tab = SubjectTab(self)
        self.tab_faecher.setLayout(QVBoxLayout())
        self.tab_faecher.layout().addWidget(self.subject_tab)
        
        # Kompetenzen-Tab
        self.competency_tab = CompetencyTab(self)
        self.tab_komp = QWidget()
        self.tabWidget.addTab(self.tab_komp, "Kompetenzen")
        self.tab_komp.setLayout(QVBoxLayout())
        self.tab_komp.layout().addWidget(self.competency_tab)

        # Einstellungen-Tab
        self.settings_tab = SettingsTab(self)
        self.tab_sett.setLayout(QVBoxLayout())
        self.tab_sett.layout().addWidget(self.settings_tab)

    def show_calendar_context_menu(self, pos):
        """Zeigt das Kontextmenü für den Kalender"""
        menu = QMenu()
        add_action = menu.addAction("Unterrichtsstunde hinzufügen")
        action = menu.exec(self.calendarWidget.mapToGlobal(pos))
        
        if action == add_action:
            self.list_manager.add_day_lesson(self.calendarWidget.selectedDate())

    def on_add_lesson_clicked(self):
        """Handler für den '+ Button' im Kalender"""
        self.list_manager.add_day_lesson(self.calendarWidget.selectedDate())


    def on_date_selected(self, date):
        """Event-Handler für Kalenderauswahl"""
        self.list_manager.update_all(date)
        self.list_manager.update_day_list(date)

    def refresh_all(self):
        """Aktualisiert alle relevanten Ansichten"""
        # Refresh various tabs and dialogs
        if hasattr(self, 'subject_tab'):
            self.subject_tab.refresh_subjects()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    school = SchoolManagement()
    school.show()
    sys.exit(app.exec())