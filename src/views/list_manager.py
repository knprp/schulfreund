from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6.QtWidgets import QMessageBox, QMenu
from PyQt6.QtCore import Qt, QDate, QDateTime, QTime
from datetime import datetime, timedelta


class ListManager:
    """Verwaltet die Logik und Inhalte der Listen in der Kalenderansicht."""
    
    def __init__(self, parent):
        self.parent = parent
        self.calendar_container = parent.calendar_container
        self.setup_models()
        self.connect_models()
        self.setup_connections()
        # Initiale Aktualisierung mit aktuellem Datum
        self.update_all(QDate.currentDate())

    def setup_models(self):
        """Erstellt die Datenmodelle für die Listen"""
        # Nur noch focus und events als Models, da day_schedule eigenes Model hat
        self.focus_model = QStandardItemModel()
        self.events_model = QStandardItemModel()

    def connect_models(self):
        """Verbindet die Modelle mit den ListView-Widgets"""
        self.calendar_container.focus_list.setModel(self.focus_model)
        self.calendar_container.events_list.setModel(self.events_model)

    def setup_connections(self):
        """Richtet alle Signal-Verbindungen ein"""
        # Kontext-Menü für Tagesliste
        day_schedule = self.calendar_container.day_schedule
        day_schedule.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        day_schedule.customContextMenuRequested.connect(self.show_lesson_context_menu)
        
        # Add-Button
        self.calendar_container.add_lesson_btn.clicked.connect(self.add_day_lesson)

    def update_all(self, date):
        """Aktualisiert alle Listen für das ausgewählte Datum"""
        self.update_day_list(date)
        self.update_focus_list(date)
        self.update_events_list(date)

    def update_day_list(self, date):
        """Aktualisiert die Liste der Unterrichtsstunden für das ausgewählte Datum"""
        try:
            current_datetime = QDateTime.currentDateTime()
            current_time = current_datetime.time()
            is_today = date == QDate.currentDate()
            
            # Hole Stunden und Zeitslots
            lessons = self.parent.db.get_lessons_by_date(date.toString("yyyy-MM-dd"))
            time_slots = self.get_time_slots()
            
            day_schedule = self.calendar_container.day_schedule
            day_schedule.clear_schedule()
            
            if not lessons:
                day_schedule.add_lesson(
                    "---", "---", "---",
                    "Keine Stunden für diesen Tag", "---"
                )
                return

            # Erstelle ein Dictionary für schnellen Zugriff auf die Slots
            slot_dict = {}
            for i, (start, end, number) in enumerate(time_slots):
                slot_dict[start.toString("HH:mm")] = (start, end, i)  # i statt number!
                
            for lesson in lessons:
                start_time_str = lesson['time']
                if start_time_str not in slot_dict:
                    print(f"Warnung: Keine Slot-Konfiguration für Zeit {start_time_str}")
                    continue
                    
                start_time, base_end_time, slot_index = slot_dict[start_time_str]
                duration = lesson.get('duration', 1)
                
                # Bei Doppelstunden: Ende der zweiten Stunde verwenden
                target_slot = slot_index + duration - 1
                if duration > 1 and target_slot < len(time_slots):
                    _, end_time, _ = time_slots[target_slot]
                else:
                    end_time = base_end_time
                    
                time_slot = f"{start_time.toString('HH:mm')} - {end_time.toString('HH:mm')}"
                
                # Prüfe ob die Stunde vergangen ist
                is_past = False
                if date < QDate.currentDate():
                    is_past = True
                elif is_today and current_time > end_time:
                    is_past = True
                    
                # Statusbestimmung
                if is_past:
                    if lesson.get('topic'):
                        continue
                    status = "kein Thema"
                elif is_today and current_time >= start_time:
                    status = "aktuell"
                else:
                    status = "kommend"
                
                course_name = lesson.get('course_name', '')
                subject = lesson.get('subject', '')
                topic = lesson.get('topic', '')
                
                day_schedule.add_lesson(
                    time_slot,
                    course_name,
                    subject,
                    topic,
                    status,
                    lesson['id']
                )
            
            day_schedule.model.sort(0)
            
        except Exception as e:
            QMessageBox.critical(
                self.parent,
                "Fehler",
                f"Fehler beim Laden der Stunden: {str(e)}"
            )

    def update_focus_list(self, date):
        """Aktualisiert die 'Achte heute auf'-Liste"""
        pass  # Implementierung folgt

    def update_events_list(self, date):
        """Aktualisiert die Liste der wichtigen Ereignisse"""
        pass  # Implementierung folgt

    def add_day_lesson(self):
        """Fügt neue Unterrichtsstunde(n) für das ausgewählte Datum hinzu."""
        try:
            from src.views.dialogs.lesson_dialog import LessonDialog
            selected_date = self.calendar_container.get_selected_date()
            dialog = LessonDialog(self.parent, selected_date)
            if dialog.exec():
                lessons_data = dialog.get_data()  # Jetzt eine Liste von Stunden
                
                # Erstelle jede ausgewählte Stunde
                for lesson_data in lessons_data:
                    self.parent.db.add_lesson(lesson_data)
                
                self.update_day_list(selected_date)
                
                # Statusmeldung anpassen
                if len(lessons_data) == 1:
                    msg = "Unterrichtsstunde wurde hinzugefügt"
                else:
                    msg = f"{len(lessons_data)} Unterrichtsstunden wurden hinzugefügt"
                self.parent.statusBar().showMessage(msg, 3000)
                
        except Exception as e:
            QMessageBox.critical(
                self.parent, 
                "Fehler", 
                f"Fehler beim Hinzufügen der Stunde(n): {str(e)}"
            )

    def add_lesson_at_position(self, date: QDate, time: str):
        """Fügt eine neue Stunde zu einer bestimmten Zeit an einem bestimmten Datum hinzu"""
        try:
            from src.views.dialogs.lesson_dialog import LessonDialog
            dialog = LessonDialog(self.parent, selected_date=date)
            
            # Setze die entsprechende Stunde
            for row in range(dialog.lessons_table.rowCount()):
                time_item = dialog.lessons_table.item(row, 0)
                if time_item:
                    item_time = time_item.text().split(" - ")[0]
                    if item_time == time:
                        checkbox = dialog.lessons_table.cellWidget(row, 1)
                        if checkbox:
                            checkbox.setChecked(True)
                        break
            
            if dialog.exec():
                lessons_data = dialog.get_data()
                for lesson_data in lessons_data:
                    self.parent.db.add_lesson(lesson_data)
                
                # Aktualisiere Kalenderansichten
                self.update_all(date)
                
                # Update week view wenn nötig
                if hasattr(self.calendar_container, 'week_view'):
                    week_view = self.calendar_container.stack.widget(1)  # WeekView ist im zweiten Slot
                    if week_view:
                        week_view.update_view(week_view.week_navigator.current_week_start)
                
                self.parent.statusBar().showMessage("Stunde wurde hinzugefügt", 3000)
                
        except Exception as e:
            QMessageBox.critical(self.parent, "Fehler", f"Fehler beim Hinzufügen der Stunde: {str(e)}")

    def edit_lesson(self, lesson_id):
        """Bearbeitet existierende Unterrichtsstunde(n)"""
        try:
            lesson = self.parent.db.get_lesson(lesson_id)
            if lesson:
                from src.views.dialogs.lesson_dialog import LessonDialog
                dialog = LessonDialog(
                    parent=self.parent,
                    selected_date=QDate.fromString(lesson['date'], "yyyy-MM-dd"),
                    lesson=lesson
                )
                if dialog.exec():
                    lessons_data = dialog.get_data()
                    
                    # Bei Bearbeitung erwarten wir normalerweise nur eine Stunde
                    update_data = lessons_data[0]
                    update_all_following = update_data.pop('update_all_following', False)
                    
                    # Aktualisiere die Stunde(n)
                    self.parent.db.update_lesson(
                        lesson_id, 
                        update_data, 
                        update_all_following
                    )
                    
                    # Aktualisiere Tagesliste
                    self.update_day_list(self.calendar_container.get_selected_date())

                    # Aktualisiere WeekView falls vorhanden
                    if hasattr(self.calendar_container, 'week_view'):
                        current_week = self.calendar_container.week_view.week_navigator.current_week_start
                        self.calendar_container.week_view.update_view(current_week)
                    
                    msg = "Alle folgenden Stunden wurden aktualisiert" if update_all_following \
                          else "Stunde wurde aktualisiert"
                    self.parent.statusBar().showMessage(msg, 3000)
                    
        except Exception as e:
            QMessageBox.critical(self.parent, 
                               "Fehler", 
                               f"Fehler beim Bearbeiten: {str(e)}")

    def show_lesson_context_menu(self, pos):
        """Zeigt das Kontext-Menü für eine Unterrichtsstunde"""
        # Hole die lesson_id von der TableView
        day_schedule = self.calendar_container.day_schedule
        lesson_id = day_schedule.get_lesson_id_at_position(pos)
        
        if lesson_id is None:
            return
                
        menu = QMenu()
        edit_action = menu.addAction("Bearbeiten")
        delete_action = menu.addAction("Löschen")
        
        action = menu.exec(day_schedule.viewport().mapToGlobal(pos))
        if not action:
            return
        
        if action == edit_action:
            self.edit_lesson(lesson_id)
        elif action == delete_action:
            self.delete_lesson(lesson_id)

    def delete_lesson(self, lesson_id):
        """Löscht eine oder mehrere Unterrichtsstunden"""
        try:
            lesson = self.parent.db.get_lesson(lesson_id)
            if not lesson:
                return
                
            from src.views.dialogs.delete_lesson_dialog import DeleteLessonDialog    
            dialog = DeleteLessonDialog(self.parent, lesson)
            
            if dialog.exec():
                delete_all = dialog.get_delete_all()
                self.parent.db.delete_lessons(lesson_id, delete_all)
                self.update_day_list(self.calendar_container.get_selected_date())
                
                msg = "Alle folgenden Stunden wurden gelöscht" if delete_all else "Stunde wurde gelöscht"
                self.parent.statusBar().showMessage(msg, 3000)
                
        except Exception as e:
            QMessageBox.critical(self.parent, "Fehler", f"Fehler beim Löschen: {str(e)}")

    def get_time_slots(self):
        """Berechnet die Zeitslots für den Tag basierend auf den Einstellungen."""
        settings = self.parent.db.get_time_settings()
        if not settings:
            # Standard-Einstellungen wenn nichts konfiguriert
            return [(QTime(8, 0), QTime(8, 45), 1)]
            
        slots = []
        current_time = QTime.fromString(settings['first_lesson_start'], "HH:mm")
        lesson_duration = settings['lesson_duration']
        breaks = dict(settings['breaks'])
        
        for lesson in range(1, 11):  # 10 mögliche Stunden
            start_time = current_time
            end_time = current_time.addSecs(lesson_duration * 60)
            slots.append((start_time, end_time, lesson))
            
            # Addiere Pause wenn vorhanden
            break_duration = breaks.get(lesson, 0)
            current_time = end_time.addSecs(break_duration * 60)
            
        return slots