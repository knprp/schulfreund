# src/views/calendar_container.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget, 
                           QPushButton, QListView, QLabel, QCalendarWidget)
from PyQt6.QtCore import Qt, QDate
from src.views.week_view import WeekView

class CalendarContainer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setup_ui()

    def setup_ui(self):
        """Erstellt das Layout mit allen UI-Elementen"""
        # Hauptlayout als QHBoxLayout
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Linker Bereich (Kalender/WeekView)
        left_layout = QVBoxLayout()
        
        # Toggle-Button und "+" in einer Reihe
        button_layout = QHBoxLayout()
        self.view_toggle = QPushButton("Zur Wochenansicht")
        self.view_toggle.clicked.connect(self.toggle_view)
        button_layout.addWidget(self.view_toggle)
        
        self.add_lesson_btn = QPushButton("+")
        button_layout.addWidget(self.add_lesson_btn)
        button_layout.addStretch()
        left_layout.addLayout(button_layout)
        
        # StackedWidget für Kalender/Wochenansicht
        self.stack = QStackedWidget()
        self.calendar_widget = QCalendarWidget()
        self.calendar_widget.clicked.connect(self.on_date_selected)
        self.week_view = WeekView(self.parent)
        
        self.stack.addWidget(self.calendar_widget)
        self.stack.addWidget(self.week_view)
        left_layout.addWidget(self.stack)
        
        main_layout.addLayout(left_layout, stretch=7)  # 70% der Breite
        
        # Rechter Bereich (Listen)
        right_layout = QVBoxLayout()
        right_layout.setSpacing(5)
        
        # Stunden des Tages
        right_layout.addWidget(QLabel("<b>Stunden des Tages</b>"))
        self.lessons_list = QListView()
        right_layout.addWidget(self.lessons_list)
        
        # Wichtige Ereignisse
        right_layout.addWidget(QLabel("<b>Wichtige Ereignisse</b>"))
        self.events_list = QListView()
        right_layout.addWidget(self.events_list)
        
        # Achte heute auf
        right_layout.addWidget(QLabel("<b>Achte heute auf</b>"))
        self.focus_list = QListView()
        right_layout.addWidget(self.focus_list)
        
        main_layout.addLayout(right_layout, stretch=3)  # 30% der Breite

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