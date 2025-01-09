# src/views/settings/semester_settings.py

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QLabel, QDateEdit, QGroupBox, QMessageBox, 
                           QLineEdit, QTextEdit, QDialog,
                           QDialogButtonBox, QListWidget, QListWidgetItem)
from PyQt6.QtCore import QDate, Qt

class SemesterHistoryDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("Halbjahr zur Historie hinzufügen")
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Datumsfelder
        self.start_date = QDateEdit()
        self.end_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.end_date.setCalendarPopup(True)
        
        layout.addWidget(QLabel("Start:"))
        layout.addWidget(self.start_date)
        layout.addWidget(QLabel("Ende:"))
        layout.addWidget(self.end_date)
        
        # Name (optional)
        layout.addWidget(QLabel("Name (optional):"))
        self.name = QLineEdit()
        layout.addWidget(self.name)
        
        # Notizen (optional)
        layout.addWidget(QLabel("Notizen (optional):"))
        self.notes = QTextEdit()
        layout.addWidget(self.notes)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

class SemesterSettings(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setup_ui()
        self.load_semester_settings()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Aktives Halbjahr Gruppe
        active_group = QGroupBox("Aktives Halbjahr")
        active_layout = QVBoxLayout()
        
        # Start-Datum
        start_layout = QHBoxLayout()
        start_layout.addWidget(QLabel("Start:"))
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.dateChanged.connect(lambda date: self.end_date.setMinimumDate(date))
        start_layout.addWidget(self.start_date)
        active_layout.addLayout(start_layout)

        # End-Datum
        end_layout = QHBoxLayout()
        end_layout.addWidget(QLabel("Ende:"))
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.dateChanged.connect(lambda date: self.start_date.setMaximumDate(date))
        end_layout.addWidget(self.end_date)
        active_layout.addLayout(end_layout)
        
        # Schnellauswahl-Buttons
        quick_select_layout = QHBoxLayout()
        first_semester_btn = QPushButton("1. Halbjahr")
        first_semester_btn.clicked.connect(lambda: self.set_semester_dates(1))
        quick_select_layout.addWidget(first_semester_btn)
        
        second_semester_btn = QPushButton("2. Halbjahr")
        second_semester_btn.clicked.connect(lambda: self.set_semester_dates(2))
        quick_select_layout.addWidget(second_semester_btn)
        active_layout.addLayout(quick_select_layout)
        
        # Optional: Name für das Halbjahr
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Bezeichnung:"))
        self.semester_name = QLineEdit()
        name_layout.addWidget(self.semester_name)
        active_layout.addLayout(name_layout)
        
        # Speichern-Button
        save_btn = QPushButton("Speichern")
        save_btn.clicked.connect(self.save_semester_settings)
        active_layout.addWidget(save_btn)
        
        active_group.setLayout(active_layout)
        layout.addWidget(active_group)
        
        # Historie-Gruppe
        history_group = QGroupBox("Halbjahres-Historie")
        history_layout = QVBoxLayout()
        
        # Liste der gespeicherten Halbjahre
        self.history_list = QListWidget()
        self.history_list.itemDoubleClicked.connect(self.load_semester_from_history)
        history_layout.addWidget(self.history_list)
        
        # Buttons für die Historie
        history_btn_layout = QHBoxLayout()
        
        load_btn = QPushButton("Laden")
        load_btn.clicked.connect(self.load_selected_semester)
        history_btn_layout.addWidget(load_btn)
        
        delete_btn = QPushButton("Löschen")
        delete_btn.clicked.connect(self.delete_selected_semester)
        history_btn_layout.addWidget(delete_btn)
        
        history_layout.addLayout(history_btn_layout)
        history_group.setLayout(history_layout)
        layout.addWidget(history_group)
        
        layout.addStretch()
        
        # Initial Historie laden
        self.refresh_history_list()

    def save_semester_settings(self):
        """Speichert die Semester-Einstellungen und fügt sie zur Historie hinzu"""
        try:
            start_date = self.start_date.date().toString("yyyy-MM-dd")
            end_date = self.end_date.date().toString("yyyy-MM-dd")
            name = self.semester_name.text().strip()
            
            if start_date >= end_date:
                raise ValueError("Das Startdatum muss vor dem Enddatum liegen")
                
            if self.check_semester_overlap(start_date, end_date):
                raise ValueError("Das neue Semester überschneidet sich mit einem existierenden Semester")
                
            # Speichern als aktives Halbjahr
            self.parent.db.save_semester_dates(start_date, end_date)
            
            # Automatisch zur Historie hinzufügen
            self.parent.db.save_semester_to_history(start_date, end_date, name)
            
            self.refresh_history_list()
            self.parent.statusBar().showMessage("Halbjahr wurde gespeichert", 3000)
            
            # Aktualisiere die Semester-Anzeige
            self.parent.status_display.update_semester_display()
            
            # Aktualisiere andere Tabs
            if hasattr(self.parent, 'refresh_all'):
                self.parent.refresh_all()
                
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Speichern der Einstellungen: {str(e)}")

    def refresh_history_list(self):
        """Aktualisiert die Liste der Halbjahre in der Historie"""
        self.history_list.clear()
        try:
            history = self.parent.db.get_semester_history()
            for semester in history:
                display_text = semester['name'] if semester['name'] else f"{semester['start_date']} - {semester['end_date']}"
                item = QListWidgetItem(display_text)
                item.setData(Qt.ItemDataRole.UserRole, semester)
                self.history_list.addItem(item)
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Laden der Historie: {str(e)}")

    def load_selected_semester(self):
        """Lädt das ausgewählte Halbjahr aus der Historie"""
        current_item = self.history_list.currentItem()
        if current_item:
            semester_data = current_item.data(Qt.ItemDataRole.UserRole)
            self.start_date.setDate(QDate.fromString(semester_data['start_date'], "yyyy-MM-dd"))
            self.end_date.setDate(QDate.fromString(semester_data['end_date'], "yyyy-MM-dd"))
            self.semester_name.setText(semester_data.get('name', ''))
            
            # Speichere das geladene Semester als aktives Semester
            self.parent.db.save_semester_dates(semester_data['start_date'], semester_data['end_date'])
            
            # Aktualisiere die Anzeige über das StatusDisplay
            self.parent.status_display.update_semester_display()
            self.parent.statusBar().showMessage("Halbjahr aus Historie geladen", 3000)

    def delete_selected_semester(self):
        """Löscht das ausgewählte Halbjahr aus der Historie"""
        current_item = self.history_list.currentItem()
        if current_item:
            semester_data = current_item.data(Qt.ItemDataRole.UserRole)
            reply = QMessageBox.question(
                self,
                'Halbjahr löschen',
                f'Möchten Sie das Halbjahr "{current_item.text()}" wirklich aus der Historie löschen?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                try:
                    self.parent.db.delete_semester_from_history(semester_data['id'])
                    self.refresh_history_list()
                    self.parent.statusBar().showMessage("Halbjahr wurde aus der Historie gelöscht", 3000)
                except Exception as e:
                    QMessageBox.critical(self, "Fehler", f"Fehler beim Löschen: {str(e)}")

    def load_semester_from_history(self, item):
        """Handler für Doppelklick auf ein Halbjahr in der Historie"""
        self.load_selected_semester()

    def set_semester_dates(self, semester: int):
        """Setzt die Daten für das gewählte Halbjahr"""
        current_date = QDate.currentDate()
        current_year = current_date.year()
        
        if semester == 1:  # Erstes Halbjahr (August - Januar)
            self.start_date.setDate(QDate(current_year, 8, 1))
            self.end_date.setDate(QDate(current_year + 1, 1, 31))
        else:  # Zweites Halbjahr (Februar - Juli)
            self.start_date.setDate(QDate(current_year, 2, 1))
            self.end_date.setDate(QDate(current_year, 7, 31))

    def load_semester_settings(self):
        """Lädt die Semester-Einstellungen aus der Datenbank"""
        try:
            settings = self.parent.db.get_semester_dates()
            if settings:
                self.start_date.setDate(QDate.fromString(settings['semester_start'], "yyyy-MM-dd"))
                self.end_date.setDate(QDate.fromString(settings['semester_end'], "yyyy-MM-dd"))
            else:
                # Setze Standardwerte für das aktuelle Halbjahr
                current_month = QDate.currentDate().month()
                self.set_semester_dates(1 if current_month >= 8 else 2)
                
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Laden der Einstellungen: {str(e)}")

    def check_semester_overlap(self, start_date, end_date):
        """Prüft, ob sich ein Semester mit existierenden Semestern überschneidet"""
        history = self.parent.db.get_semester_history()
        for semester in history:
            if (start_date <= semester['end_date'] and 
                end_date >= semester['start_date']):
                return True
        return False