# src/views/calendar_container.py

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QGridLayout,
                           QPushButton, QStackedWidget, QCalendarWidget, 
                           QListView, QLabel)
from PyQt6.QtCore import Qt, QDate
from src.views.week_view import WeekView
from src.views.day_schedule_view import DayScheduleView  # Neue Import

class CalendarContainer(QWidget):
    """Container für das Layout der Kalenderansicht."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setup_ui()

    def setup_ui(self):
        """Erstellt das Layout mit allen UI-Elementen"""
        grid_layout = QGridLayout(self)
        grid_layout.setSpacing(10)

        # Umschalt-Button für die Ansichten
        self.view_toggle = QPushButton("Zur Wochenansicht")
        self.view_toggle.clicked.connect(self.toggle_view)
        grid_layout.addWidget(self.view_toggle, 0, 0, 1, 1)

        # StackedWidget für Kalender/Wochenansicht
        self.stack = QStackedWidget()
        
        # Kalenderansicht
        self.calendar_widget = QCalendarWidget()
        self.calendar_widget.clicked.connect(self.on_date_selected)
        
        # Wochenansicht
        self.week_view = WeekView(self.parent)
        
        self.stack.addWidget(self.calendar_widget)
        self.stack.addWidget(self.week_view)
        
        grid_layout.addWidget(self.stack, 1, 0, 1, 2)

        # "+" Button für neue Stunden
        self.add_lesson_btn = QPushButton("+")
        grid_layout.addWidget(self.add_lesson_btn, 0, 1)

        # Stunden des Tages (jetzt mit TableView)
        lessons_label = QLabel("<b>Stunden des Tages</b>")
        grid_layout.addWidget(lessons_label, 0, 2)
        
        self.day_schedule = DayScheduleView(self)
        grid_layout.addWidget(self.day_schedule, 1, 2)

        # Wichtige Ereignisse (bleibt ListView)
        events_label = QLabel("<b>Wichtige Ereignisse</b>")
        grid_layout.addWidget(events_label, 2, 0)
        
        self.events_list = QListView()
        grid_layout.addWidget(self.events_list, 3, 0, 1, 2)

        # Achte heute auf (bleibt ListView)
        focus_label = QLabel("<b>Achte heute auf</b>")
        grid_layout.addWidget(focus_label, 2, 2)
        
        self.focus_list = QListView()
        grid_layout.addWidget(self.focus_list, 3, 2)
        
        # grid_layout.addLayout(right_layout, stretch=3)  # 30% der Breite

    def toggle_view(self):
        """Wechselt zwischen Kalender- und Wochenansicht"""
        current_index = self.stack.currentIndex()
        new_index = 1 if current_index == 0 else 0
        self.stack.setCurrentIndex(new_index)
        
        text = "Zur Kalenderansicht" if new_index == 1 else "Zur Wochenansicht"
        self.view_toggle.setText(text)
        
        if new_index == 1:  # Wochenansicht
            self.update_week_view()

    def update_week_view(self):
        """Aktualisiert die Wochenansicht"""
        monday = self.calendar_widget.selectedDate()
        # Auf Montag zurückgehen
        while monday.dayOfWeek() != 1:
            monday = monday.addDays(-1)
        self.week_view.update_view(monday)

    def on_date_selected(self, date):
        """Wird aufgerufen, wenn ein Datum im Kalender ausgewählt wird"""
        if self.parent and hasattr(self.parent, 'list_manager'):
            self.parent.list_manager.update_all(date)

    def get_selected_date(self):
        """Gibt das aktuell ausgewählte Datum zurück"""
        return self.calendar_widget.selectedDate()