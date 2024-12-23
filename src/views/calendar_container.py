# src/views/calendar_container.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QGridLayout,
                           QPushButton, QStackedWidget, QCalendarWidget, 
                           QListView, QLabel)
from PyQt6.QtCore import Qt, QDate
from src.views.week_view import WeekView

class CalendarContainer(QWidget):
    """Container für das Layout der Kalenderansicht. Stellt nur die UI-Komponenten
    bereit, während die Logik im ListManager liegt."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.current_date = QDate.currentDate()  # Aktuelles Datum speichern
        self.setup_ui()

    def setup_ui(self):
        """Erstellt das Layout mit allen UI-Elementen"""
        grid_layout = QGridLayout(self)
        grid_layout.setSpacing(10)

        # Umschalt-Button für die Ansichten
        self.view_toggle = QPushButton("Zur Kalenderansicht")  # Geänderter Standardtext
        self.view_toggle.clicked.connect(self.toggle_view)
        grid_layout.addWidget(self.view_toggle, 0, 0, 1, 1)

        # StackedWidget für Kalender/Wochenansicht
        self.stack = QStackedWidget()
        
        # Kalenderansicht
        self.calendar_widget = QCalendarWidget()
        self.calendar_widget.setSelectedDate(self.current_date)  # Aktuelles Datum setzen
        self.calendar_widget.clicked.connect(self.on_date_selected)
        
        # Wochenansicht
        self.week_view = WeekView(self.parent)
        
        self.stack.addWidget(self.calendar_widget)
        self.stack.addWidget(self.week_view)
        
        # Initial die Wochenansicht anzeigen
        self.stack.setCurrentIndex(1)
        
        grid_layout.addWidget(self.stack, 1, 0, 1, 2)

        # "+" Button für neue Stunden
        self.add_lesson_btn = QPushButton("+")
        grid_layout.addWidget(self.add_lesson_btn, 0, 1)

        # Listen (werden vom ListManager verwaltet)
        self.setup_lists(grid_layout)
        
        # Initial die Wochenansicht aktualisieren
        self.update_week_view()

    def setup_lists(self, grid_layout):
        """Richtet die Listen ein, die vom ListManager verwaltet werden"""
        # Stunden des Tages
        lessons_label = QLabel("<b>Stunden des Tages</b>")
        grid_layout.addWidget(lessons_label, 0, 2)
        
        self.lessons_list = QListView()
        grid_layout.addWidget(self.lessons_list, 1, 2)

        # Wichtige Ereignisse
        events_label = QLabel("<b>Wichtige Ereignisse</b>")
        grid_layout.addWidget(events_label, 2, 0)
        
        self.events_list = QListView()
        grid_layout.addWidget(self.events_list, 3, 0, 1, 2)

        # Achte heute auf
        focus_label = QLabel("<b>Achte heute auf</b>")
        grid_layout.addWidget(focus_label, 2, 2)
        
        self.focus_list = QListView()
        grid_layout.addWidget(self.focus_list, 3, 2)

    def toggle_view(self):
        """Wechselt zwischen Kalender- und Wochenansicht"""
        current_index = self.stack.currentIndex()
        new_index = 1 if current_index == 0 else 0
        self.stack.setCurrentIndex(new_index)
        
        text = "Zur Kalenderansicht" if new_index == 1 else "Zur Wochenansicht"
        self.view_toggle.setText(text)
        
        if new_index == 1:  # Wochenansicht
            # Hole das aktuelle Datum aus dem Kalender
            selected_date = self.calendar_widget.selectedDate()
            # Setze die Woche in der WeekView
            self.week_view.week_navigator.set_week(selected_date)

    def update_week_view(self):
        """Aktualisiert die Wochenansicht"""
        current_date = self.calendar_widget.selectedDate()
        monday = current_date.addDays(-current_date.dayOfWeek() + 1)
        self.week_view.update_view(monday)

    def on_date_selected(self, date):
        """Wird aufgerufen, wenn ein Datum im Kalender ausgewählt wird"""
        if self.parent and hasattr(self.parent, 'list_manager'):
            self.parent.list_manager.update_all(date)

    def get_selected_date(self):
        """Gibt das aktuell ausgewählte Datum zurück"""
        return self.calendar_widget.selectedDate()