# src/views/week_view.py

from PyQt6.QtWidgets import (QWidget, QTableWidget, QTableWidgetItem, QHeaderView,
                           QVBoxLayout, QMenu, QStyledItemDelegate, QMessageBox, QStyle)
from PyQt6.QtCore import Qt, QDate, pyqtSignal, QSize
from PyQt6.QtGui import QColor, QBrush, QTextDocument, QAbstractTextDocumentLayout
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

        # Doppelklick aktivieren
        self.table.doubleClicked.connect(self.on_cell_double_clicked)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Navigator hinzufügen
        self.week_navigator = WeekNavigator(self)
        self.week_navigator.week_changed.connect(self.update_view)
        layout.addWidget(self.week_navigator)
        
        # Tabelle erstellen (bisheriger Code)
        self.table = QTableWidget()
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # HTML-Delegate setzen
        self.table.setItemDelegate(HTMLDelegate(self.table))
        
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

        self.update_view(self.week_navigator.current_week_start)

    def update_time_slots(self):
        """Aktualisiert die Zeilen und Zeitslots basierend auf den Einstellungen"""
        try:
            if hasattr(self.parent, "settings_tab") and \
            hasattr(self.parent.settings_tab, "timetable_settings") and \
            self.parent.settings_tab.timetable_settings is not None:
                
                time_slots = self.parent.settings_tab.timetable_settings.get_time_slots()
                
                # Liste für alle Zeilen (normale Stunden + Pausen)
                all_rows = []
                last_end_time = None
                
                for start_time, end_time, lesson_num in time_slots:
                    # Prüfe ob es eine Pause zum vorherigen Slot gibt
                    if last_end_time and start_time != last_end_time:
                        # Berechne Pausenlänge in Minuten
                        pause_minutes = last_end_time.secsTo(start_time) / 60
                        if pause_minutes >= 10:
                            # Füge Pausenzeile hinzu
                            pause_label = f"Pause ({int(pause_minutes)} Min.)"
                            all_rows.append({"label": pause_label, "is_pause": True, 
                                        "height": int(pause_minutes * 0.8)})
                    
                    # Füge normale Stundenzeile hinzu
                    time_label = f"{start_time.toString('HH:mm')} - {end_time.toString('HH:mm')}"
                    all_rows.append({"label": time_label, "is_pause": False, "height": 60})
                    
                    last_end_time = end_time
                
                # Tabelle aktualisieren
                self.table.setRowCount(len(all_rows))
                time_labels = []
                
                for row, data in enumerate(all_rows):
                    time_labels.append(data["label"])
                    self.table.setRowHeight(row, data["height"])
                    
                    # Pausen visuell kennzeichnen
                    if data["is_pause"]:
                        pause_item = QTableWidgetItem("")
                        pause_item.setBackground(QColor("#dee2e6"))
                        self.table.setItem(row, 0, pause_item)
                        # Verbinde alle Spalten zu einer
                        self.table.setSpan(row, 0, 1, self.table.columnCount())
                
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
        
        # Prüfe ob es eine Pausenzeile ist
        if row >= 0:
            header_text = self.table.verticalHeaderItem(row).text()
            if header_text.startswith("Pause"):
                return  # Kein Menü für Pausenzeilen
        
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
        
        self.table.clearContents()
        
        # Hole die Feiertage für diese Woche
        holidays = self.parent.holiday_manager.get_holidays_for_week(
            week_start.toPyDate()
        )
        
        # Erstelle ein Dict für schnellen Zugriff auf Feiertage
        holiday_dict = {h['date']: h for h in holidays}
        
        # Hole die Daten für jeden Tag der Woche
        current_date = week_start
        for day in range(5):  # Mo-Fr
            date_str = current_date.toString("yyyy-MM-dd")
            lessons = self.parent.controllers.lesson.get_lessons_by_date(date_str)
            
            # Prüfe ob der Tag ein Feiertag/Ferientag ist
            is_holiday = date_str in holiday_dict
            if is_holiday:
                holiday = holiday_dict[date_str]
                self.mark_holiday(day, holiday)
                
                # Markiere die Stunden als entfallen
                for lesson in lessons:
                    time = lesson['time']
                    row = self.get_row_for_time(time)
                    if row >= 0:
                        lesson['status'] = 'cancelled'  # Status auf cancelled setzen
                        # Grund für das Entfallen hinzufügen
                        reason = "Feiertag" if holiday['type'] == 'holiday' else "Ferien"
                        lesson['status_note'] = f"Entfällt wegen {reason}: {holiday['name']}"
                        item = self.create_lesson_item(lesson)
                        self.table.setItem(row, day, item)
                        
                        if lesson.get('duration', 1) == 2 and row < self.table.rowCount() - 1:
                            self.table.setSpan(row, day, 2, 1)
                            if self.table.item(row + 1, day):
                                self.table.takeItem(row + 1, day)
            else:
                # Normale Stunden anzeigen
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
            if not header_text.startswith("Pause"):  # Pausenzeilen ignorieren
                start_time = header_text.split(" - ")[0]
                if start_time == time:
                    return row
        return -1

    def create_lesson_item(self, lesson):
        """Erstellt ein TableWidgetItem für eine Unterrichtsstunde"""
        item = QTableWidgetItem()
        
        # Basis-Text formatieren
        text = f"<b>{lesson['subject']} {lesson['course_name']}</b>"
        if lesson.get('topic'):
            text += f"<br>{lesson['topic']}"

        # Status-spezifische Formatierung
        status = lesson.get('status', 'normal')
        if status == 'cancelled':
            # Deutlichere Markierung für entfallene Stunden
            text = (f"<div style='color: #999999;'>"  # Grauer Text
                f"<s>{text}</s>"          # Durchgestrichen
                f"<br>⛔ <small>{lesson.get('status_note', 'Entfällt')}</small>"  # Entfallen-Symbol und Grund
                f"</div>")
            # Sehr heller Hintergrund mit rötlichem Ton
            color = QColor(255, 240, 240)
            if lesson.get('course_color'):
                base_color = QColor(lesson['course_color'])
                color = QColor(
                    min(255, base_color.red() + 200),
                    min(255, base_color.green() + 180),
                    min(255, base_color.blue() + 180),
                40  # Sehr transparent
                )
        elif status == 'moved':
            # Kursiv mit Pfeil
            text = f"<i>{text} →</i>"
            if lesson.get('status_note'):
                text += f"<br><small>{lesson['status_note']}</small>"
            color = QColor('#FFFFD0')  # Hellgelb
        elif status == 'substituted':
            # Symbol für Vertretung
            text = f"🔄 {text}"
            if lesson.get('status_note'):
                text += f"<br><small>{lesson['status_note']}</small>"
            color = self.get_background_color(lesson)
        else:
            # Normale Stunde
            color = self.get_background_color(lesson)
                
        item.setText(text)
        item.setData(Qt.ItemDataRole.UserRole, lesson['id'])
        
        # Zentrieren und Mehrzeiligkeit erlauben
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
        
        # Hintergrundfarbe setzen
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

    def get_background_color(self, lesson):
        """Ermittelt die Hintergrundfarbe für eine Stunde"""
        if lesson.get('course_color'):
            color = QColor(lesson['course_color'])
        else:
            color = self.get_subject_color(lesson['subject'])
        
        # Standard-Alpha für normale Stunden
        color.setAlpha(40)
        return color

    def on_cell_double_clicked(self, index):
        """Handler für Doppelklick auf eine Zelle"""
        try:
            item = self.table.item(index.row(), index.column())
            if item and item.data(Qt.ItemDataRole.UserRole):
                lesson_id = item.data(Qt.ItemDataRole.UserRole)
                
                from src.views.dialogs.lesson_details_dialog import LessonDetailsDialog
                dialog = LessonDetailsDialog(self.parent, lesson_id)
                if dialog.exec():
                    # Nach Schließen des Dialogs View aktualisieren
                    self.update_view(self.week_navigator.current_week_start)
                    
        except Exception as e:
            QMessageBox.critical(
                self,
                "Fehler",
                f"Fehler beim Öffnen der Stundendetails: {str(e)}"
            )

    def mark_holiday(self, column: int, holiday: dict):
        """Markiert eine Spalte als Feiertag/Ferientag"""
        # Farben für verschiedene Arten von freien Tagen
        colors = {
            'holiday': QColor(255, 230, 230, 100),     # Hellrot mit Transparenz
            'vacation_day': QColor(230, 255, 230, 100), # Hellgrün mit Transparenz
            'school': QColor(230, 230, 255, 100)       # Hellblau mit Transparenz
        }
        
        # Icons für verschiedene Typen
        icons = {
            'holiday': "★",    # Stern für Feiertag
            'vacation_day': "☼", # Sonne für Ferien
            'school': "✎"      # Stift für Schulfrei
        }
        
        color = colors.get(holiday['type'], QColor("#FFFFFF"))
        icon = icons.get(holiday['type'], "")
        
        # Färbe die ganze Spalte ein
        for row in range(self.table.rowCount()):
            item = self.table.item(row, column)
            if not item:
                item = QTableWidgetItem()
                self.table.setItem(row, column, item)
            
            # Setze Hintergrundfarbe
            item.setBackground(color)
            
            # In der ersten Zeile den Namen anzeigen
            if row == 0:
                item.setText(f"{icon} {holiday['name']}")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                # Fett für Feiertage
                if holiday['type'] == 'holiday':
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)
                
                tooltip = (f"{'Feiertag' if holiday['type'] == 'holiday' else 'Ferien' if holiday['type'] == 'vacation_day' else 'Schulfrei'}\n"
                        f"{holiday['name']}")
                item.setToolTip(tooltip)
                
                # Zellen verbinden für bessere Lesbarkeit des Namens
                self.table.setSpan(0, column, 1, 1)



class HTMLDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.doc = QTextDocument(self)

    def paint(self, painter, option, index):
        painter.save()

        # Zeichne den Hintergrund
        background = index.data(Qt.ItemDataRole.BackgroundRole)
        if background:
            painter.fillRect(option.rect, background)
                
        # Setze den HTML-Content
        self.doc.setHtml(index.data())
        
        # Text-Ränder
        margin = 5
        text_rect = option.rect.adjusted(margin, margin, -margin, -margin)
        
        # Zentriere den Text vertikal
        clip_rect = text_rect
        text_height = self.doc.size().height()
        if text_height < text_rect.height():
            y_offset = int((text_rect.height() - text_height) // 2)
            text_rect.moveTop(text_rect.top() + y_offset)
            
        # Zeichne den Text
        painter.translate(text_rect.topLeft())
        painter.setClipRect(clip_rect.translated(-text_rect.topLeft()))
        self.doc.documentLayout().draw(painter, QAbstractTextDocumentLayout.PaintContext())
        
        painter.restore()

    def sizeHint(self, option, index):
        self.doc.setHtml(index.data())
        return QSize(self.doc.idealWidth(), self.doc.size().height())