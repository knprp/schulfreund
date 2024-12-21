# src/views/week_view.py

from PyQt6.QtWidgets import (QWidget, QTableWidget, QTableWidgetItem, QHeaderView,
                           QVBoxLayout, QMenu)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QColor, QBrush

class WeekView(QWidget):
    """Widget zur Anzeige des Wochenstundenplans"""
    
    # Signal für Kontextmenü-Interaktionen
    lesson_clicked = pyqtSignal(int)  # Sendet lesson_id
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.current_week = QDate.currentDate()
        self.setup_ui()
        self.setup_context_menu()

    def setup_ui(self):
        """Initialisiert die Benutzeroberfläche"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Tabelle erstellen
        self.table = QTableWidget()
        
        # Verhindern von Bearbeitung durch Klicks
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        self.table.setColumnCount(5)  # Mo-Fr
        self.table.setRowCount(10)    # Stunden 1-10
        
        # Spaltenüberschriften (Wochentage)
        weekdays = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag']
        self.table.setHorizontalHeaderLabels(weekdays)
        
        # Zeilenüberschriften (Stunden)
        time_slots = [
            '08:00 - 08:45', '08:45 - 09:30', 
            '09:45 - 10:30', '10:30 - 11:15',
            '11:30 - 12:15', '12:15 - 13:00',
            '13:30 - 14:15', '14:15 - 15:00',
            '15:00 - 15:45', '15:45 - 16:30'
        ]
        self.table.setVerticalHeaderLabels(time_slots)
        
        # Spaltenbreite anpassen
        header = self.table.horizontalHeader()
        for i in range(5):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
        
        # Zeilenhöhe anpassen
        for i in range(10):
            self.table.setRowHeight(i, 60)
        
        layout.addWidget(self.table)
        
        # Styling
        self.table.setShowGrid(True)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                gridline-color: #d0d0d0;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                padding: 4px;
                border: 1px solid #d0d0d0;
            }
        """)

    def setup_context_menu(self):
        """Richtet das Kontextmenü ein"""
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)

    def show_context_menu(self, pos):
        """Zeigt das Kontextmenü an der Mausposition"""
        item = self.table.itemAt(pos)
        menu = QMenu()
        
        row = self.table.rowAt(pos.y())
        col = self.table.columnAt(pos.x())
        
        if item and item.data(Qt.ItemDataRole.UserRole):  # Wenn Stunde existiert
            lesson_id = item.data(Qt.ItemDataRole.UserRole)
            edit_action = menu.addAction("Bearbeiten")
            delete_action = menu.addAction("Löschen")
            
            action = menu.exec(self.table.viewport().mapToGlobal(pos))
            if not action:
                return
                
            if action == edit_action:
                self.lesson_clicked.emit(lesson_id)
            elif action == delete_action:
                self.delete_lesson(lesson_id)
                
        else:  # Leere Zelle
            if row >= 0 and col >= 0:  # Gültige Zelle
                add_action = menu.addAction("Stunde hinzufügen")
                
                action = menu.exec(self.table.viewport().mapToGlobal(pos))
                if action == add_action:
                    self.add_lesson(row, col)

    def update_view(self, week_start: QDate):
        """Aktualisiert die Ansicht für die gewählte Woche"""
        self.table.clearContents()
        self.current_week = week_start
        
        # Hole die Daten für jeden Tag der Woche
        current_date = week_start
        for day in range(5):  # Mo-Fr
            date_str = current_date.toString("yyyy-MM-dd")
            lessons = self.parent.db.get_lessons_by_date(date_str)
            
            # Füge Stunden in die entsprechenden Zellen ein
            for lesson in lessons:
                time = lesson['time']
                row = self.get_row_for_time(time)
                if row >= 0:
                    item = self.create_lesson_item(lesson)
                    self.table.setItem(row, day, item)
                    
            current_date = current_date.addDays(1)

    def create_lesson_item(self, lesson):
        """Erstellt ein TableWidgetItem für eine Unterrichtsstunde"""
        item = QTableWidgetItem()
        
        # Text formatieren
        text = f"{lesson['subject']}\n{lesson['course_name']}"
        if lesson.get('topic'):
            text += f"\n{lesson['topic']}"
            
        item.setText(text)
        item.setData(Qt.ItemDataRole.UserRole, lesson['id'])
        
        # Zentrieren und Mehrzeiligkeit erlauben
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
        
        # Hintergrundfarbe basierend auf Fach
        color = self.get_subject_color(lesson['subject'])
        item.setBackground(QBrush(color))
        
        return item

    def get_subject_color(self, subject):
        """Gibt eine Farbe für ein Fach zurück"""
        # Farbzuordnung für Fächer
        colors = {
            'Mathematik': QColor('#FFE5E5'),  # Hellrot
            'Deutsch': QColor('#E5FFE5'),     # Hellgrün
            'Englisch': QColor('#E5E5FF'),    # Hellblau
            'Geschichte': QColor('#FFE5FF'),   # Helllila
            'Biologie': QColor('#FFFFE5'),    # Hellgelb
            'Physik': QColor('#E5FFFF'),      # Helltürkis
            'Chemie': QColor('#FFE5E5'),      # Hellrot
            'Kunst': QColor('#FFE5FF'),       # Helllila
            'Musik': QColor('#E5FFE5'),       # Hellgrün
        }
        return colors.get(subject, QColor('#FFFFFF'))  # Weiß als Standard

    def get_row_for_time(self, time: str) -> int:
        """Ermittelt die Tabellenzeile für eine bestimmte Uhrzeit"""
        time_map = {
            "08:00": 0, "08:45": 1,
            "09:45": 2, "10:30": 3,
            "11:30": 4, "12:15": 5,
            "13:30": 6, "14:15": 7,
            "15:00": 8, "15:45": 9
        }
        return time_map.get(time, -1)

    def on_cell_clicked(self, row, col):
        """Handler für Klicks auf Tabellenzellen"""
        item = self.table.item(row, col)
        if item and item.data(Qt.ItemDataRole.UserRole):
            self.lesson_clicked.emit(item.data(Qt.ItemDataRole.UserRole))

    def on_cell_double_clicked(self, row, col):
        """Handler für Doppelklicks auf Tabellenzellen"""
        item = self.table.item(row, col)
        if item and item.data(Qt.ItemDataRole.UserRole):
            self.lesson_double_clicked.emit(item.data(Qt.ItemDataRole.UserRole))

    def add_lesson(self, row, col):
        """Fügt eine neue Stunde hinzu"""
        # Berechne Datum und Zeit aus Zeile/Spalte
        date = self.current_week.addDays(col)
        time = self.get_time_for_row(row)
        
        if time:
            from src.views.dialogs.lesson_dialog import LessonDialog
            dialog = LessonDialog(self.parent, date)
            if dialog.exec():
                lesson_data = dialog.get_data()
                self.parent.db.add_lesson(lesson_data)
                self.update_view(self.current_week)

    def get_time_for_row(self, row: int) -> str:
        """Ermittelt die Uhrzeit für eine bestimmte Zeile"""
        times = [
            "08:00", "08:45",
            "09:45", "10:30",
            "11:30", "12:15",
            "13:30", "14:15",
            "15:00", "15:45"
        ]
        return times[row] if 0 <= row < len(times) else None

    def delete_lesson(self, lesson_id: int):
        """Löscht eine Unterrichtsstunde"""
        from PyQt6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self,
            'Stunde löschen',
            'Möchten Sie diese Stunde wirklich löschen?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.parent.db.delete_lessons(lesson_id)
                self.update_view(self.current_week)
                self.parent.statusBar().showMessage("Stunde wurde gelöscht", 3000)
            except Exception as e:
                QMessageBox.critical(self, "Fehler", str(e))