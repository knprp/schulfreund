# src/views/calendar_container.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QGridLayout,
                           QPushButton, QStackedWidget, QCalendarWidget,
                           QListView, QLabel, QHBoxLayout, QSplitter)
from PyQt6.QtCore import Qt, QDate
from src.views.week_view import WeekView
from src.views.day_schedule_view import DayScheduleView

class CalendarContainer(QWidget):
    """Container für das Layout der Kalenderansicht."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setup_ui()

    def setup_ui(self):
        """Erstellt das Layout mit allen UI-Elementen"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header-Bereich
        header = QHBoxLayout()
        header.setContentsMargins(10, 10, 10, 5)

        # Umschalt-Button für die Ansichten
        self.view_toggle = QPushButton("Zur Kalenderansicht")
        self.view_toggle.clicked.connect(self.toggle_view)
        header.addWidget(self.view_toggle)

        # "+" Button für neue Stunden
        self.add_lesson_btn = QPushButton("+")
        self.add_lesson_btn.setFixedWidth(40)
        header.addWidget(self.add_lesson_btn)
        
        header.addStretch()
        main_layout.addLayout(header)

        # Hauptbereich mit Splitter
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Linke Seite: Stack mit Kalender/Wochenansicht
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(10, 0, 5, 10)

        self.stack = QStackedWidget()
        
        # Kalenderansicht
        self.calendar_widget = QCalendarWidget()
        self.calendar_widget.clicked.connect(self.on_date_selected)
        self.stack.addWidget(self.calendar_widget)
        
        # Wochenansicht
        self.week_view = WeekView(self.parent)
        self.stack.addWidget(self.week_view)
        
        # WeekView als Standard setzen
        self.stack.setCurrentIndex(1)
        
        left_layout.addWidget(self.stack)
        content_splitter.addWidget(left_widget)

        # Rechte Seite: Tagesstunden und Listen
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(5, 0, 10, 10)

        # Stunden des Tages
        lessons_label = QLabel("<b>Stunden des Tages</b>")
        right_layout.addWidget(lessons_label)
        
        self.day_schedule = DayScheduleView(self)
        right_layout.addWidget(self.day_schedule)

        # Listen im unteren Bereich
        lists_layout = QHBoxLayout()
        
        # Wichtige Ereignisse
        events_layout = QVBoxLayout()
        events_layout.addWidget(QLabel("<b>Wichtige Ereignisse</b>"))
        self.events_list = QListView()
        events_layout.addWidget(self.events_list)
        lists_layout.addLayout(events_layout)

        # Achte heute auf
        focus_layout = QVBoxLayout()
        focus_layout.addWidget(QLabel("<b>Achte heute auf</b>"))
        self.focus_list = QListView()
        focus_layout.addWidget(self.focus_list)
        lists_layout.addLayout(focus_layout)

        right_layout.addLayout(lists_layout)
        content_splitter.addWidget(right_widget)

        # Setze initiale Größenverhältnis (70:30)
        content_splitter.setSizes([700, 300])
        
        main_layout.addWidget(content_splitter)

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