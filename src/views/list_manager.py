# src/views/list_manager.py

from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6.QtWidgets import QMessageBox, QMenu
from PyQt6.QtCore import Qt, QTime, QDate
from datetime import datetime, timedelta
from src.views.dialogs.lesson_dialog import LessonDialog

class ListManager:
    def __init__(self, parent):
        self.parent = parent
        # Erstelle Datenmodelle für die drei Listen
        self.day_model = QStandardItemModel()
        self.focus_model = QStandardItemModel()
        self.events_model = QStandardItemModel()
        
        # Weise die Modelle den ListView-Widgets zu
        self.parent.listView_tag.setModel(self.day_model)
        self.parent.listView_fokus.setModel(self.focus_model)
        self.parent.listView_ereignisse.setModel(self.events_model)
        
    def update_day_list(self, date):
        """Aktualisiert die Liste der Unterrichtsstunden für das ausgewählte Datum"""
        self.day_model.clear()
        try:
            lessons = self.parent.db.get_lessons_by_date(date.toString("yyyy-MM-dd"))
            if lessons:
                for lesson in lessons:
                    item = QStandardItem(f"{lesson['time']} - {lesson['subject']}: {lesson['topic']}")
                    item.setData(lesson['id'], Qt.ItemDataRole.UserRole)  # Speichere lesson_id für spätere Verwendung
                    self.day_model.appendRow(item)
            else:
                self.day_model.appendRow(QStandardItem("Keine Stunden für diesen Tag"))
        except Exception as e:
            QMessageBox.critical(self.parent, "Fehler", f"Fehler beim Laden der Stunden: {str(e)}")
            
    def update_focus_list(self, date):
        """Aktualisiert die 'Achte heute auf'-Liste basierend auf Schülern und ihren Leistungen"""
        self.focus_model.clear()
        try:
            # Hole alle Schüler mit schlechten Noten in den letzten 30 Tagen
            date_30_days_ago = (datetime.strptime(date.toString("yyyy-MM-dd"), "%Y-%m-%d") - 
                               timedelta(days=30)).strftime("%Y-%m-%d")
            
            query = """
                SELECT DISTINCT s.name, g.grade, c.subject
                FROM students s
                JOIN grades g ON s.id = g.student_id
                JOIN lessons l ON g.lesson_id = l.id
                JOIN competencies c ON g.competency_id = c.id
                WHERE l.date >= ? AND l.date <= ?
                AND g.grade >= 4
                ORDER BY g.grade DESC, s.name
            """
            
            students_to_watch = self.parent.db.execute(query, (date_30_days_ago, date.toString("yyyy-MM-dd")))
            
            if students_to_watch:
                for student in students_to_watch:
                    item = QStandardItem(
                        f"{student['name']} - {student['subject']} (Note {student['grade']})"
                    )
                    self.focus_model.appendRow(item)
            else:
                self.focus_model.appendRow(QStandardItem("Keine besonderen Beobachtungen"))
                
        except Exception as e:
            QMessageBox.critical(self.parent, "Fehler", f"Fehler beim Laden der Beobachtungsliste: {str(e)}")
            
    def update_events_list(self, date):
        """Aktualisiert die Liste wichtiger Ereignisse"""
        self.events_model.clear()
        try:
            # Hole alle wichtigen Ereignisse für die nächsten 14 Tage
            end_date = (datetime.strptime(date.toString("yyyy-MM-dd"), "%Y-%m-%d") + 
                       timedelta(days=14)).strftime("%Y-%m-%d")
            
            # Klausuren (als Beispiel - Sie müssten noch eine exams-Tabelle erstellen)
            query = """
                SELECT date, subject, topic, 'Klausur' as type
                FROM lessons 
                WHERE date >= ? AND date <= ?
                AND topic LIKE '%Klausur%'
                UNION
                SELECT date, subject, topic, 'Test' as type
                FROM lessons
                WHERE date >= ? AND date <= ?
                AND topic LIKE '%Test%'
                ORDER BY date
            """
            
            events = self.parent.db.execute(query, 
                (date.toString("yyyy-MM-dd"), end_date, 
                 date.toString("yyyy-MM-dd"), end_date))
            
            if events:
                for event in events:
                    event_date = datetime.strptime(event['date'], "%Y-%m-%d").strftime("%d.%m.")
                    item = QStandardItem(
                        f"{event_date} - {event['type']}: {event['subject']} ({event['topic']})"
                    )
                    self.events_model.appendRow(item)
            else:
                self.events_model.appendRow(QStandardItem("Keine anstehenden Ereignisse"))
                
        except Exception as e:
            QMessageBox.critical(self.parent, "Fehler", f"Fehler beim Laden der Ereignisse: {str(e)}")
    
    def update_all(self, date):
        """Aktualisiert alle Listen auf einmal"""
        self.update_day_list(date)
        self.update_focus_list(date)
        self.update_events_list(date)

    def add_day_lesson(self, selected_date):
        """Fügt eine neue Unterrichtsstunde für das ausgewählte Datum hinzu."""
        try:
            dialog = LessonDialog(self.parent, selected_date)
            if dialog.exec():
                lesson_data = dialog.get_data()
                self.parent.db.add_lesson(lesson_data)
                self.update_day_list(selected_date)
                self.parent.statusBar().showMessage(
                    f"Unterrichtsstunde wurde hinzugefügt", 3000
                )
        except Exception as e:
            QMessageBox.critical(
                self.parent, 
                "Fehler", 
                f"Fehler beim Hinzufügen der Stunde: {str(e)}"
            )

    def show_lesson_context_menu(self, pos):
        index = self.parent.listView_tag.indexAt(pos)
        if not index.isValid():
            return
            
        menu = QMenu()
        edit_action = menu.addAction("Bearbeiten")
        delete_action = menu.addAction("Löschen")
        
        action = menu.exec(self.parent.listView_tag.viewport().mapToGlobal(pos))
        
        if action:
            item = self.day_model.itemFromIndex(index)
            lesson_id = item.data(Qt.ItemDataRole.UserRole)
            
            if action == edit_action:
                self.edit_lesson(lesson_id)
            elif action == delete_action:
                self.delete_lesson(lesson_id)

    def edit_lesson(self, lesson_id):
        """Bearbeitet eine existierende Unterrichtsstunde"""
        try:
            lesson = self.parent.db.get_lesson(lesson_id)
            if lesson:
                dialog = LessonDialog(self.parent, QDate.fromString(lesson['date'], "yyyy-MM-dd"))
                
                # Setze den korrekten Kurs
                for i in range(dialog.course.count()):
                    course_data = dialog.course.itemData(i)
                    if course_data and course_data.get('id') == lesson['course_id']:
                        dialog.course.setCurrentIndex(i)
                        break
                
                # Setze die Uhrzeit
                dialog.time.setTime(QTime.fromString(lesson['time'], "HH:mm"))
                
                if dialog.exec():
                    updated_data = dialog.get_data()
                    self.parent.db.update_lesson(lesson_id, updated_data)
                    self.update_day_list(self.parent.calendarWidget.selectedDate())
                    self.parent.statusBar().showMessage(f"Unterrichtsstunde wurde aktualisiert", 3000)
                    
        except Exception as e:
            QMessageBox.critical(self.parent, "Fehler", f"Fehler beim Bearbeiten: {str(e)}")


    def delete_lesson(self, lesson_id):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Question)
        msg.setText("Möchten Sie diese Unterrichtsstunde wirklich löschen?")
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if msg.exec() == QMessageBox.StandardButton.Yes:
            try:
                self.parent.db.delete_lesson(lesson_id)
                self.update_day_list(self.parent.calendarWidget.selectedDate())
            except Exception as e:
                QMessageBox.critical(self.parent, "Fehler", f"Fehler beim Löschen: {str(e)}")