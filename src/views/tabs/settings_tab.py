# src/views/tabs/settings_tab.py

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTabWidget
from src.views.settings.semester_settings import SemesterSettings
from src.views.settings.timetable_settings import TimetableSettings
from src.views.settings.grading_systems_settings import GradingSystemsSettings  

class SettingsTab(QWidget):
    """Container-Widget für die verschiedenen Einstellungsbereiche"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setup_ui()

    def setup_ui(self):
        # Hauptlayout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Tab-Widget für die verschiedenen Einstellungsbereiche
        self.settings_tabs = QTabWidget()
        
        # Halbjahres-Einstellungen
        self.semester_settings = SemesterSettings(self.parent)
        self.settings_tabs.addTab(self.semester_settings, "Halbjahre")
        
        # Stundenplan-Einstellungen
        self.timetable_settings = TimetableSettings(self.parent)
        self.settings_tabs.addTab(self.timetable_settings, "Stundenplan")

        # Notensysteme
        self.grading_systems = GradingSystemsSettings(self.parent)
        self.settings_tabs.addTab(self.grading_systems, "Notensystem")

        
        layout.addWidget(self.settings_tabs)
        layout.addStretch()