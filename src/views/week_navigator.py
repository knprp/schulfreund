# src/views/week_navigator.py

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import QDate, pyqtSignal

class WeekNavigator(QWidget):
    """Widget zur Navigation zwischen Wochen"""
    
    # Signal wird emittiert, wenn sich die Woche ändert
    week_changed = pyqtSignal(QDate)  # Sendet das Datum des Wochenstarts
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_week_start = self._get_week_start(QDate.currentDate())
        self.setup_ui()
        self.update_label()
        
    def setup_ui(self):
        """Erstellt die UI-Komponenten"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Vorherige Woche Button
        self.prev_button = QPushButton("<")
        self.prev_button.clicked.connect(self.previous_week)
        layout.addWidget(self.prev_button)
        
        # Label für aktuelle Woche
        self.week_label = QLabel()
        layout.addWidget(self.week_label)
        
        # Nächste Woche Button
        self.next_button = QPushButton(">")
        self.next_button.clicked.connect(self.next_week)
        layout.addWidget(self.next_button)
        
    def _get_week_start(self, date: QDate) -> QDate:
        """Ermittelt den Montag der Woche für ein gegebenes Datum"""
        return date.addDays(-date.dayOfWeek() + 1)
    
    def update_label(self):
        """Aktualisiert die Wochenanzeige"""
        week_end = self.current_week_start.addDays(4)  # Freitag
        self.week_label.setText(
            f"{self.current_week_start.toString('dd.MM.')} - "
            f"{week_end.toString('dd.MM.yyyy')}"
        )
        
    def set_week(self, date: QDate):
        """Setzt die angezeigte Woche auf die Woche des übergebenen Datums"""
        self.current_week_start = self._get_week_start(date)
        self.update_label()
        self.week_changed.emit(self.current_week_start)
        
    def previous_week(self):
        """Wechselt zur vorherigen Woche"""
        self.current_week_start = self.current_week_start.addDays(-7)
        self.update_label()
        self.week_changed.emit(self.current_week_start)
        
    def next_week(self):
        """Wechselt zur nächsten Woche"""
        self.current_week_start = self.current_week_start.addDays(7)
        self.update_label()
        self.week_changed.emit(self.current_week_start)