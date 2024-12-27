# src/views/settings/timetable_settings.py

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QTimeEdit, QSpinBox, QPushButton, QTableWidget,
                           QTableWidgetItem, QHeaderView, QMessageBox)
from PyQt6.QtCore import QTime

class TimetableSettings(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Erste Stunde
        first_lesson_layout = QHBoxLayout()
        first_lesson_layout.addWidget(QLabel("Beginn erste Stunde:"))
        self.first_lesson_time = QTimeEdit()
        self.first_lesson_time.setDisplayFormat("HH:mm")
        first_lesson_layout.addWidget(self.first_lesson_time)
        layout.addLayout(first_lesson_layout)

        # Stundenlänge
        lesson_duration_layout = QHBoxLayout()
        lesson_duration_layout.addWidget(QLabel("Dauer einer Unterrichtsstunde:"))
        self.lesson_duration = QSpinBox()
        self.lesson_duration.setMinimum(30)
        self.lesson_duration.setMaximum(90)
        self.lesson_duration.setSuffix(" Minuten")
        lesson_duration_layout.addWidget(self.lesson_duration)
        layout.addLayout(lesson_duration_layout)

        # Pausen-Tabelle
        layout.addWidget(QLabel("Pausen:"))
        self.breaks_table = QTableWidget(10, 2)  # 10 mögliche Pausen
        self.breaks_table.setHorizontalHeaderLabels(["Nach Stunde", "Dauer (Minuten)"])
        header = self.breaks_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        
        # Füge Spinboxen für die Pauseneinstellungen hinzu
        for row in range(10):
            # Nach Stunde
            lesson_spin = QSpinBox()
            lesson_spin.setRange(1, 10)
            lesson_spin.setValue(row + 1)
            self.breaks_table.setCellWidget(row, 0, lesson_spin)
            
            # Pausendauer
            duration_spin = QSpinBox()
            duration_spin.setRange(0, 60)
            duration_spin.setSuffix(" min")
            self.breaks_table.setCellWidget(row, 1, duration_spin)

        layout.addWidget(self.breaks_table)

        # Speichern-Button
        save_button = QPushButton("Einstellungen speichern")
        save_button.clicked.connect(self.save_settings)
        layout.addWidget(save_button)

    def load_settings(self):
        """Lädt die aktuellen Einstellungen aus der Datenbank"""
        try:
            # Hole Grundeinstellungen
            cursor = self.parent.db.execute(
                "SELECT first_lesson_start, lesson_duration FROM timetable_settings WHERE id = 1"
            )
            settings = cursor.fetchone()
            
            if settings:
                # Setze Startzeit
                time = QTime.fromString(settings['first_lesson_start'], "HH:mm")
                self.first_lesson_time.setTime(time)
                
                # Setze Stundenlänge
                self.lesson_duration.setValue(settings['lesson_duration'])
            
            # Hole Pausen
            cursor = self.parent.db.execute(
                "SELECT after_lesson, duration FROM breaks ORDER BY after_lesson"
            )
            breaks = cursor.fetchall()
            
            # Setze Pausenwerte
            for row, break_info in enumerate(breaks):
                lesson_spin = self.breaks_table.cellWidget(row, 0)
                duration_spin = self.breaks_table.cellWidget(row, 1)
                
                lesson_spin.setValue(break_info['after_lesson'])
                duration_spin.setValue(break_info['duration'])
                
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Laden der Einstellungen: {str(e)}")

    def save_settings(self):
        """Speichert die Einstellungen in der Datenbank"""
        try:
            # Speichere Grundeinstellungen
            self.parent.db.execute(
                """INSERT OR REPLACE INTO timetable_settings 
                   (id, first_lesson_start, lesson_duration) 
                   VALUES (1, ?, ?)""",
                (self.first_lesson_time.time().toString("HH:mm"),
                 self.lesson_duration.value())
            )
            
            # Lösche alte Pausen
            self.parent.db.execute("DELETE FROM breaks")
            
            # Speichere neue Pausen
            for row in range(10):
                lesson_spin = self.breaks_table.cellWidget(row, 0)
                duration_spin = self.breaks_table.cellWidget(row, 1)
                
                # Nur Pausen mit Dauer > 0 speichern
                if duration_spin.value() > 0:
                    self.parent.db.execute(
                        "INSERT INTO breaks (after_lesson, duration) VALUES (?, ?)",
                        (lesson_spin.value(), duration_spin.value())
                    )
            
            QMessageBox.information(self, "Erfolg", "Einstellungen wurden gespeichert")
            
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Speichern der Einstellungen: {str(e)}")
            
    def get_time_slots(self):
        """Berechnet alle Zeitslots basierend auf den Einstellungen"""
        slots = []
        current_time = QTime.fromString(self.first_lesson_time.time().toString("HH:mm"), "HH:mm")
        lesson_duration = self.lesson_duration.value()
        
        for lesson in range(1, 11):  # 10 mögliche Stunden
            start_time = current_time
            end_time = current_time.addSecs(lesson_duration * 60)
            slots.append((start_time, end_time, lesson))
            
            # Finde Pause nach dieser Stunde
            break_duration = 0
            for row in range(10):
                lesson_spin = self.breaks_table.cellWidget(row, 0)
                duration_spin = self.breaks_table.cellWidget(row, 1)
                if lesson_spin.value() == lesson and duration_spin.value() > 0:
                    break_duration = duration_spin.value()
                    break
            
            # Addiere Stundenlänge und eventuelle Pause
            current_time = end_time.addSecs(break_duration * 60)
        
        return slots