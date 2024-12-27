from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6.QtWidgets import QMessageBox, QMenu
from PyQt6.QtCore import Qt, QDate
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
        self.day_model = QStandardItemModel()
        self.focus_model = QStandardItemModel()
        self.events_model = QStandardItemModel()

    def connect_models(self):
        """Verbindet die Modelle mit den ListView-Widgets"""
        self.calendar_container.lessons_list.setModel(self.day_model)
        self.calendar_container.focus_list.setModel(self.focus_model)
        self.calendar_container.events_list.setModel(self.events_model)

    def setup_connections(self):
        """Richtet alle Signal-Verbindungen ein"""
        # Kontext-Menü für Tagesliste
        lessons_list = self.calendar_container.lessons_list
        lessons_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        lessons_list.customContextMenuRequested.connect(self.show_lesson_context_menu)
        
        # Add-Button
        self.calendar_container.add_lesson_btn.clicked.connect(self.add_day_lesson)

    def update_all(self, date):
        """Aktualisiert alle Listen für das ausgewählte Datum"""
        self.update_day_list(date)
        self.update_focus_list(date)
        self.update_events_list(date)

    def update_day_list(self, date):
        """Aktualisiert die Tagesliste"""
        self.day_model.clear()
        try:
            lessons = self.parent.db.get_lessons_by_date(date.toString("yyyy-MM-dd"))
            if lessons:
                for lesson in lessons:
                    item = QStandardItem(
                        f"{lesson['time']} - {lesson['subject']}: {lesson.get('topic', '')}"
                    )
                    item.setData(lesson['id'], Qt.ItemDataRole.UserRole)
                    self.day_model.appendRow(item)
            else:
                self.day_model.appendRow(QStandardItem("Keine Stunden für diesen Tag"))
        except Exception as e:
            QMessageBox.critical(self.parent, "Fehler", f"Fehler beim Laden der Stunden: {str(e)}")

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
        list_view = self.calendar_container.lessons_list
        index = list_view.indexAt(pos)
        if not index.isValid():
            return
            
        menu = QMenu()
        edit_action = menu.addAction("Bearbeiten")
        delete_action = menu.addAction("Löschen")
        
        action = menu.exec(list_view.viewport().mapToGlobal(pos))
        if not action:
            return
            
        item = self.day_model.itemFromIndex(index)
        lesson_id = item.data(Qt.ItemDataRole.UserRole)
        
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