from PyQt6.QtWidgets import (QWidget, QTableWidget, QTableWidgetItem, QHeaderView,
                           QVBoxLayout, QMenu, QMessageBox)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QColor, QBrush
from .week_navigator import WeekNavigator

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
        
        # Navigator hinzufügen
        self.week_navigator = WeekNavigator(self)
        self.week_navigator.week_changed.connect(self.update_view)
        layout.addWidget(self.week_navigator)
        
        # Tabelle erstellen (bisheriger Code)
        self.table = QTableWidget()
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # Rest des bisherigen setup_ui Codes...
        self.table.setColumnCount(5)
        weekdays = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag']
        self.table.setHorizontalHeaderLabels(weekdays)
        
        self.update_time_slots()
        
        header = self.table.horizontalHeader()
        for i in range(5):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
        
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
        
        layout.addWidget(self.table)

    def update_time_slots(self):
        """Aktualisiert die Zeilen und Zeitslots basierend auf den Einstellungen"""
        try:
            print("Checking for settings...")
            print(f"Has settings_tab: {hasattr(self.parent, 'settings_tab')}")
            print(f"Parent type: {type(self.parent)}")
            if hasattr(self.parent, "settings_tab"):
                print(f"Has settings_tabs: {hasattr(self.parent.settings_tab, 'settings_tabs')}")
                print(f"Has timetable_settings: {hasattr(self.parent.settings_tab, 'timetable_settings')}")
            
            if hasattr(self.parent, "settings_tab") and \
               hasattr(self.parent.settings_tab, "timetable_settings") and \
               self.parent.settings_tab.timetable_settings is not None:
                
                time_slots = self.parent.settings_tab.timetable_settings.get_time_slots()
                self.table.setRowCount(len(time_slots))
                
                # Zeitslots als Zeilenüberschriften setzen
                time_labels = []
                for start_time, end_time, lesson_num in time_slots:
                    time_label = f"{start_time.toString('HH:mm')} - {end_time.toString('HH:mm')}"
                    time_labels.append(time_label)
                    # Zeilenhöhe anpassen (60 Pixel pro Stunde)
                    self.table.setRowHeight(lesson_num - 1, 60)
                
                self.table.setVerticalHeaderLabels(time_labels)
                
            else:
                # Fallback auf Standardzeiten
                standard_times = [
                    "08:00 - 08:45", "08:45 - 09:30", 
                    "09:45 - 10:30", "10:30 - 11:15",
                    "11:30 - 12:15", "12:15 - 13:00",
                    "13:30 - 14:15", "14:15 - 15:00",
                    "15:00 - 15:45", "15:45 - 16:30"
                ]
                self.table.setRowCount(len(standard_times))
                self.table.setVerticalHeaderLabels(standard_times)
                for i in range(len(standard_times)):
                    self.table.setRowHeight(i, 60)
                
        except Exception as e:
            print(f"Fehler beim Aktualisieren der Zeitslots: {str(e)}")

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
                if hasattr(self.parent, 'list_manager'):
                    self.parent.list_manager.edit_lesson(lesson_id)
                    self.update_view(self.week_navigator.current_week_start)
            elif action == delete_action:
                if hasattr(self.parent, 'list_manager'):
                    self.parent.list_manager.delete_lesson(lesson_id)
                    self.update_view(self.week_navigator.current_week_start)
                    
        else:  # Leere Zelle
            if row >= 0 and col >= 0:  # Gültige Zelle
                add_action = menu.addAction("Stunde hinzufügen")
                
                action = menu.exec(self.table.viewport().mapToGlobal(pos))
                if action == add_action:
                    self.add_lesson_at_position(row, col)

    def add_lesson_at_position(self, row, col):
        """Fügt eine neue Stunde an der gewählten Position hinzu"""
        try:
            # Datum bestimmen: Montag + Anzahl Tage der Spalte
            date = self.week_navigator.current_week_start.addDays(col)
            
            # Zeit aus der Zeilenbeschriftung extrahieren
            time_label = self.table.verticalHeaderItem(row).text()
            time = time_label.split(" - ")[0]  # Nehme nur die Startzeit
            
            # Delegation an ListManager
            if hasattr(self.parent, 'list_manager'):
                self.parent.list_manager.add_lesson_at_position(date, time)
                # Die View wird vom ListManager aktualisiert, wir müssen hier nichts tun
                    
        except Exception as e:
            QMessageBox.critical(self.parent, "Fehler", f"Fehler beim Hinzufügen der Stunde: {str(e)}")

    def update_view(self, week_start: QDate):
        """Aktualisiert die Ansicht für die gewählte Woche"""
        # Existierende Methode anpassen, um week_start zu verwenden
        self.table.clearContents()
        
        # Hole die Daten für jeden Tag der Woche
        current_date = week_start  # Statt direkt week_start zu setzen
        for day in range(5):  # Mo-Fr
            date_str = current_date.toString("yyyy-MM-dd")
            lessons = self.parent.db.get_lessons_by_date(date_str)
            
            # Rest des bisherigen update_view Codes...
            for lesson in lessons:
                time = lesson['time']
                row = self.get_row_for_time(time)
                if row >= 0:
                    item = self.create_lesson_item(lesson)
                    self.table.setItem(row, day, item)
                    
                    if lesson.get('duration', 1) == 2 and row < self.table.rowCount() - 1:
                        self.table.setSpan(row, day, 2, 1)
                        if self.table.item(row + 1, day):
                            self.table.takeItem(row + 1, day)
                    
            current_date = current_date.addDays(1)

    def get_row_for_time(self, time: str) -> int:
        """Ermittelt die Tabellenzeile für eine bestimmte Uhrzeit"""
        for row in range(self.table.rowCount()):
            header_text = self.table.verticalHeaderItem(row).text()
            start_time = header_text.split(" - ")[0]
            if start_time == time:
                return row
        return -1

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