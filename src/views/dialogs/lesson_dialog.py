# src/views/dialogs/lesson_dialog.py

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QComboBox, QTableWidget, QTableWidgetItem,
                           QDialogButtonBox, QCheckBox, QCalendarWidget,
                           QMessageBox, QPushButton, QHeaderView, QLineEdit)
from PyQt6.QtCore import QDate, Qt

class LessonDialog(QDialog):
    def __init__(self, parent=None, selected_date=None, lesson=None):
        super().__init__(parent)
        self.parent = parent
        self.selected_date = selected_date or QDate.currentDate()
        self.lesson = lesson
        self.subject_label = QLabel("-")
        self.setWindowTitle("Stunde bearbeiten" if lesson else "Stunde hinzufügen")
        self.setup_ui()
        
        if lesson:
            self.load_lesson_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Kurs/Klasse (Pflichtfeld)
        course_layout = QHBoxLayout()
        course_layout.addWidget(QLabel("Kurs/Klasse:*"))
        self.course = QComboBox()
        self.course.currentIndexChanged.connect(self.update_subject_display)
        self.load_courses()
        course_layout.addWidget(self.course)
        layout.addLayout(course_layout)
        
        # Anzeige des Fachs
        subject_layout = QHBoxLayout()
        subject_layout.addWidget(QLabel("Fach:"))
        subject_layout.addWidget(self.subject_label)
        layout.addLayout(subject_layout)

        # Topic/Thema
        topic_layout = QHBoxLayout()
        topic_layout.addWidget(QLabel("Thema:"))
        self.topic = QLineEdit()
        topic_layout.addWidget(self.topic)
        layout.addLayout(topic_layout)

        # Datum
        layout.addWidget(QLabel("Datum:"))
        self.calendar = QCalendarWidget()
        if self.selected_date:
            self.calendar.setSelectedDate(self.selected_date)
        self.calendar.clicked.connect(self.on_date_selected)
        layout.addWidget(self.calendar)

        # Stundenauswahl
        layout.addWidget(QLabel("Stunden:"))
        
        # Tabelle für Stundenauswahl
        self.lessons_table = QTableWidget()
        self.lessons_table.setColumnCount(2)
        self.lessons_table.setHorizontalHeaderLabels(["Zeit", "Auswahl"])
        
        # Spaltenbreiten anpassen
        header = self.lessons_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        
        # Lade verfügbare Stunden
        self.load_time_slots()
        self.mark_occupied_slots()  # Markiere belegte Slots initial
        layout.addWidget(self.lessons_table)

        # Button für Mehrfachauswahl
        select_layout = QHBoxLayout()
        select_all = QPushButton("Alle auswählen")
        select_all.clicked.connect(self.select_all_slots)
        select_layout.addWidget(select_all)
        
        select_none = QPushButton("Keine auswählen")
        select_none.clicked.connect(self.select_no_slots)
        select_layout.addWidget(select_none)
        
        mark_double = QPushButton("Als Doppelstunde markieren")
        mark_double.clicked.connect(self.mark_double_lesson)
        select_layout.addWidget(mark_double)
        
        layout.addLayout(select_layout)

        # Checkbox für wiederkehrende Termine - nur beim Erstellen
        if not self.lesson:
            self.recurring_checkbox = QCheckBox("Im gesamten Halbjahr wiederholen")
            layout.addWidget(self.recurring_checkbox)
        
        # Checkbox für "Alle folgenden auch ändern" - nur beim Bearbeiten
        elif self.lesson.get('recurring_hash'):
            self.update_following_checkbox = QCheckBox("Alle folgenden Stunden auch ändern")
            layout.addWidget(self.update_following_checkbox)

        # Pflichtfeld-Hinweis
        layout.addWidget(QLabel("* Pflichtfeld"))

        # Dialog-Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def load_time_slots(self):
        """Lädt die verfügbaren Zeitslots aus den Einstellungen"""
        try:
            # Direkter Zugriff über main window
            if hasattr(self.parent, "settings_tab") and \
            hasattr(self.parent.settings_tab, "timetable_settings"):
                
                time_slots = self.parent.settings_tab.timetable_settings.get_time_slots()
                
                self.lessons_table.setRowCount(len(time_slots))
                for row, (start_time, end_time, lesson_num) in enumerate(time_slots):
                    # Zeitslot
                    time_text = f"{start_time.toString('HH:mm')} - {end_time.toString('HH:mm')}"
                    self.lessons_table.setItem(row, 0, QTableWidgetItem(time_text))
                    
                    # Checkbox für Auswahl
                    checkbox = QCheckBox()
                    self.lessons_table.setCellWidget(row, 1, checkbox)
                    
            else:
                # Standardzeiten verwenden
                standard_times = [
                    "08:00 - 08:45", "08:45 - 09:30", 
                    "09:45 - 10:30", "10:30 - 11:15",
                    "11:30 - 12:15", "12:15 - 13:00",
                    "13:30 - 14:15", "14:15 - 15:00",
                    "15:00 - 15:45", "15:45 - 16:30"
                ]
                self.lessons_table.setRowCount(len(standard_times))
                for row, time in enumerate(standard_times):
                    self.lessons_table.setItem(row, 0, QTableWidgetItem(time))
                    checkbox = QCheckBox()
                    self.lessons_table.setCellWidget(row, 1, checkbox)
                
        except Exception as e:
            print(f"Fehler beim Laden der Stundenzeiten: {str(e)}")  # Debug-Ausgabe
            QMessageBox.warning(self, "Warnung", 
                            "Fehler beim Laden der Stundenzeiten. "
                            "Standardzeiten werden verwendet.")
                            
    def select_all_slots(self):
        """Wählt alle Zeitslots aus"""
        for row in range(self.lessons_table.rowCount()):
            checkbox = self.lessons_table.cellWidget(row, 1)
            if checkbox:
                checkbox.setChecked(True)

    def select_no_slots(self):
        """Hebt die Auswahl aller Zeitslots auf"""
        for row in range(self.lessons_table.rowCount()):
            checkbox = self.lessons_table.cellWidget(row, 1)
            if checkbox:
                checkbox.setChecked(False)

    def get_selected_slots(self):
        """Gibt die ausgewählten Zeitslots und ihre Duration zurück"""
        selected_slots = []
        for row in range(self.lessons_table.rowCount()):
            checkbox = self.lessons_table.cellWidget(row, 1)
            time_item = self.lessons_table.item(row, 0)
            if checkbox and checkbox.isChecked():
                time_text = time_item.text()
                start_time = time_text.split(" - ")[0].strip()
                # Prüfe ob es eine Doppelstunde ist
                is_double = time_item.background().color() == Qt.GlobalColor.yellow
                duration = 2 if is_double else 1
                selected_slots.append((start_time, duration))
        return selected_slots

    def check_time_conflicts(self, date, slots):
        """
        Prüft ob es Überschneidungen mit existierenden Stunden gibt.
        
        Args:
            date (QDate): Das zu prüfende Datum
            slots (list): Liste der zu prüfenden Zeitslots
            
        Returns:
            list: Liste von Konflikten, jeder Konflikt als Dict mit Zeitslot und existierender Stunde
        """
        date_str = date.toString("yyyy-MM-dd")
        existing_lessons = self.parent.db.get_lessons_by_date(date_str)
        
        conflicts = []
        for slot in slots:
            for lesson in existing_lessons:
                # Überspringe aktuelle Stunde beim Bearbeiten
                if self.lesson and lesson['id'] == self.lesson['id']:
                    continue
                    
                if lesson['time'] == slot:
                    conflicts.append({
                        'time': slot,
                        'existing_lesson': lesson
                    })
                    
        return conflicts

    def load_courses(self):
        """Lädt alle verfügbaren Kurse/Klassen"""
        try:
            print("Loading courses...") # Debug
            courses = self.parent.db.get_all_courses()
            print(f"Found courses: {courses}")  # Debug
            self.course.clear()
            self.course.addItem("Bitte wählen...", None)  # Standardauswahl
            for course in courses:
                display_text = f"{course['name']} ({course['type']})"
                print(f"Adding course: {display_text}")  # Debug
                self.course.addItem(display_text, course)
            self.update_subject_display()
        except Exception as e:
            print(f"Error: {e}")  # Debug
            QMessageBox.critical(self, "Fehler", f"Fehler beim Laden der Kurse: {str(e)}")

    def update_subject_display(self):
        """Aktualisiert die Anzeige des Fachs basierend auf der Kursauswahl"""
        course_data = self.course.currentData()
        if course_data and isinstance(course_data, dict) and course_data.get('subject'):
            self.subject_label.setText(course_data['subject'])
        else:
            self.subject_label.setText("-")

    def validate_and_accept(self):
        """Prüft die Eingaben vor dem Akzeptieren"""
        # Prüfe Kursauswahl
        course_data = self.course.currentData()
        if not course_data:
            QMessageBox.warning(self, "Fehler", "Bitte wählen Sie einen Kurs/eine Klasse aus!")
            return
        if not course_data.get('subject'):
            QMessageBox.warning(self, "Fehler", "Der gewählte Kurs hat kein zugeordnetes Fach!")
            return

        # Prüfe Stundenauswahl
        selected_slots = self.get_selected_slots()
        if not selected_slots:
            QMessageBox.warning(self, "Fehler", "Bitte wählen Sie mindestens eine Unterrichtsstunde aus!")
            return

        # Prüfe auf Konflikte
        conflicts = self.check_time_conflicts(self.calendar.selectedDate(), selected_slots)
        if conflicts:
            # Erstelle detaillierte Konfliktmeldung
            conflict_msg = "Folgende Überschneidungen wurden gefunden:\n\n"
            for conflict in conflicts:
                lesson = conflict['existing_lesson']
                conflict_msg += (f"{conflict['time']}: {lesson['subject']} "
                               f"({lesson['course_name']})\n")
            conflict_msg += "\nMöchten Sie trotzdem fortfahren?"
            
            reply = QMessageBox.question(
                self,
                'Zeitkonflikte gefunden',
                conflict_msg,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.No:
                return

        self.accept()

    def get_data(self):
        """Gibt die eingegebenen Daten zurück"""
        course_data = self.course.currentData()
        selected_slots = self.get_selected_slots()  # Gibt jetzt (time, duration) Tuples zurück
        
        # Basisdaten, die für alle Stunden gleich sind
        base_data = {
            'course_id': course_data['id'],
            'date': self.calendar.selectedDate().toString("yyyy-MM-dd"),
            'subject': course_data['subject'],
            'topic': self.topic.text().strip(),
        }
        
        # Liste für alle Stunden
        lessons_data = []
        
        # Erstelle für jede ausgewählte Stunde einen Eintrag
        for time_slot, duration in selected_slots:  # Tuple auspacken
            lesson_data = base_data.copy()
            lesson_data['time'] = time_slot
            lesson_data['duration'] = duration  # duration hinzufügen
            lessons_data.append(lesson_data)
        
        # Füge Flags für wiederkehrende Stunden oder Aktualisierung hinzu
        if not self.lesson:
            for data in lessons_data:
                data['is_recurring'] = getattr(self, 'recurring_checkbox', False) and \
                                    self.recurring_checkbox.isChecked()
        else:
            for data in lessons_data:
                data['update_all_following'] = getattr(self, 'update_following_checkbox', False) and \
                                            self.update_following_checkbox.isChecked()
        
        return lessons_data

    def mark_occupied_slots(self):
        """Markiert bereits belegte Zeitslots"""
        date_str = self.calendar.selectedDate().toString("yyyy-MM-dd")
        existing_lessons = self.parent.db.get_lessons_by_date(date_str)
        
        # Alle Slots zurücksetzen
        for row in range(self.lessons_table.rowCount()):
            time_item = self.lessons_table.item(row, 0)
            if time_item:
                time_item.setBackground(Qt.GlobalColor.white)
                checkbox = self.lessons_table.cellWidget(row, 1)
                if checkbox:
                    checkbox.setEnabled(True)
        
        # Belegte Slots markieren
        for row in range(self.lessons_table.rowCount()):
            time_text = self.lessons_table.item(row, 0).text()
            start_time = time_text.split(" - ")[0]
            
            for lesson in existing_lessons:
                # Überspringe aktuelle Stunde beim Bearbeiten
                if self.lesson and lesson['id'] == self.lesson['id']:
                    continue
                    
                if lesson['time'] == start_time:
                    # Zeitslot ist belegt
                    self.lessons_table.item(row, 0).setBackground(Qt.GlobalColor.lightGray)
                    checkbox = self.lessons_table.cellWidget(row, 1)
                    if checkbox:
                        checkbox.setEnabled(False)
                        checkbox.setChecked(False)
                    
                    # Tooltip mit Zusatzinformationen
                    tooltip = f"Belegt durch: {lesson['subject']} ({lesson['course_name']})"
                    self.lessons_table.item(row, 0).setToolTip(tooltip)
                    break

    def on_date_selected(self):
        """Handler für Datumsänderung"""
        self.select_no_slots()  # Alle Auswahlboxen zurücksetzen
        self.mark_occupied_slots()  # Neu markieren für das gewählte Datum

    def mark_double_lesson(self):
        """Markiert ausgewählte Stunde als Doppelstunde"""
        # Finde die erste ausgewählte Stunde
        selected_row = -1
        for row in range(self.lessons_table.rowCount()):
            checkbox = self.lessons_table.cellWidget(row, 1)
            if checkbox and checkbox.isChecked():
                selected_row = row
                break
        
        if selected_row == -1:
            QMessageBox.warning(self, "Fehler", 
                              "Bitte wählen Sie eine Stunde aus!")
            return
            
        if selected_row == self.lessons_table.rowCount() - 1:
            QMessageBox.warning(self, "Fehler", 
                              "Die letzte Stunde kann keine Doppelstunde sein!")
            return
            
        # Prüfe ob die nächste Stunde verfügbar ist
        next_checkbox = self.lessons_table.cellWidget(selected_row + 1, 1)
        if not next_checkbox or not next_checkbox.isEnabled():
            QMessageBox.warning(self, "Fehler", 
                              "Die nachfolgende Stunde ist nicht verfügbar!")
            return
            
        # Setze alle anderen Checkboxen zurück
        for row in range(self.lessons_table.rowCount()):
            if row != selected_row:
                checkbox = self.lessons_table.cellWidget(row, 1)
                if checkbox:
                    checkbox.setChecked(False)
                    
        # Markiere die Stunde visuell als Doppelstunde
        time_item = self.lessons_table.item(selected_row, 0)
        if time_item:
            time_item.setBackground(Qt.GlobalColor.yellow)
            time_item.setToolTip("Doppelstunde")
            # Deaktiviere die nächste Stunde
            next_checkbox.setEnabled(False)
            next_time_item = self.lessons_table.item(selected_row + 1, 0)
            if next_time_item:
                next_time_item.setBackground(Qt.GlobalColor.yellow)
                next_time_item.setToolTip("Teil der Doppelstunde")

    def load_lesson_data(self):
        """Lädt die Daten einer existierenden Stunde in den Dialog"""
        # Setze den korrekten Kurs
        for i in range(self.course.count()):
            course_data = self.course.itemData(i)
            if course_data and course_data.get('id') == self.lesson['course_id']:
                self.course.setCurrentIndex(i)
                break

        # Setze Thema
        self.topic.setText(self.lesson.get('topic', ''))

        # Setze Datum
        self.calendar.setSelectedDate(QDate.fromString(self.lesson['date'], "yyyy-MM-dd"))
        
        # Setze die entsprechende Stunde
        lesson_time = self.lesson['time']
        """Lädt die Daten einer existierenden Stunde in den Dialog"""
        print("Loading lesson data:", self.lesson)  # Debug print
        for row in range(self.lessons_table.rowCount()):
            time_text = self.lessons_table.item(row, 0).text()
            start_time = time_text.split(" - ")[0]
            if start_time == lesson_time:
                checkbox = self.lessons_table.cellWidget(row, 1)
                time_item = self.lessons_table.item(row, 0)
                
                # Prüfe ob es eine Doppelstunde ist
                if self.lesson.get('duration', 1) == 2:
                    # Markiere diese Stunde
                    if checkbox:
                        checkbox.setChecked(True)
                    if time_item:
                        time_item.setBackground(Qt.GlobalColor.yellow)
                        time_item.setToolTip("Doppelstunde")
                    
                    # Markiere die nächste Stunde als Teil der Doppelstunde
                    if row < self.lessons_table.rowCount() - 1:
                        next_checkbox = self.lessons_table.cellWidget(row + 1, 1)
                        next_time_item = self.lessons_table.item(row + 1, 0)
                        if next_checkbox:
                            next_checkbox.setEnabled(False)
                        if next_time_item:
                            next_time_item.setBackground(Qt.GlobalColor.yellow)
                            next_time_item.setToolTip("Teil der Doppelstunde")
                else:
                    # Normale Einzelstunde
                    if checkbox:
                        checkbox.setChecked(True)
                break