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

from src.database.db_manager import DatabaseManager
from src.views.list_manager import ListManager
from src.views.tabs.course_tab import CourseTab
from src.views.tabs.student_tab import StudentTab
from src.views.tabs.competency_tab import CompetencyTab
from src.views.tabs.settings_tab import SettingsTab
from src.views.calendar_container import CalendarContainer

class SchoolManagement(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Datenbank initialisieren
        self.db = DatabaseManager()
        
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
    
    def setup_calendar_container(self):
        """Ersetzt den alten Kalender mit dem neuen CalendarContainer"""
        # Alten Kalender und zugehörige Widgets entfernen
        old_widgets = ['calendarWidget', 'listView_tag', 'listView_fokus',
                    'listView_ereignisse', 'label', 'label_2', 
                    'label_3', 'label_4', 'label_5', 'label_6',
                    'addLessonButton']
        
        for widget_name in old_widgets:
            if hasattr(self, widget_name):
                widget = getattr(self, widget_name)
                widget.setParent(None)
                widget.deleteLater()
        
        # Neuen CalendarContainer erstellen und einsetzen
        self.calendar_container = CalendarContainer(self)
        if not hasattr(self.tab_kal, 'layout') or self.tab_kal.layout() is None:
            self.tab_kal.setLayout(QVBoxLayout())
        self.tab_kal.layout().addWidget(self.calendar_container)
        
    def setup_ui(self):
        """Initialisiert die Benutzeroberfläche"""
        # Tabs initialisieren
        self.setup_tabs()
        
        # Menüs einrichten
        self.setup_menus()

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

    def setup_menus(self):
        """Richtet die Menüleiste ein"""
        self.menuKurse.addAction("Neuer Kurs", self.course_tab.add_course)
        self.menuKurse.addAction("Kurse anzeigen", 
                                lambda: self.tabWidget.setCurrentWidget(self.tab_kurse))

    def on_date_selected(self, date):
        """Event-Handler für Kalenderauswahl"""
        self.list_manager.update_all(date)
        self.list_manager.update_day_list(date)

    def on_add_lesson_clicked(self):
        """Event-Handler für '+ Button' im Kalender"""
        self.list_manager.add_day_lesson(self.calendarWidget.selectedDate())

if __name__ == '__main__':
    app = QApplication(sys.argv)
    school = SchoolManagement()
    school.show()
    sys.exit(app.exec())