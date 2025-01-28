# src/views/tabs/subject_tab.py

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                           QListWidget, QTableWidget, QTableWidgetItem,
                           QMessageBox, QInputDialog, QLabel)
from PyQt6.QtCore import Qt

class SubjectTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent  # Hauptfenster direkt speichern
        self.setup_ui()
        # self.refresh_subjects()


    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Toolbar mit Buttons
        toolbar = QHBoxLayout()
        
        # Button zum Hinzufügen
        add_btn = QPushButton("Fach hinzufügen")
        add_btn.clicked.connect(self.add_subject)
        toolbar.addWidget(add_btn)
        
        # Button zum Löschen
        delete_btn = QPushButton("Fach löschen")
        delete_btn.clicked.connect(self.delete_subject)
        toolbar.addWidget(delete_btn)
        
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        # Tabelle für Fächer
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels([
            "Name", "Kurse", "Standardvorlage"
        ])
        
        # Spaltenbreiten
        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, header.ResizeMode.Stretch)
        header.setSectionResizeMode(1, header.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, header.ResizeMode.Stretch)
        
        layout.addWidget(self.table)
        
        # Info-Label
        info_label = QLabel(
            "Hier können Sie Fächer verwalten. Diese erscheinen dann "
            "in der Fächerauswahl bei der Kurserstellung."
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

    def showEvent(self, event):
        """Wird aufgerufen wenn der Tab angezeigt wird"""
        super().showEvent(event)
        self.refresh_subjects()  # Stattdessen hier laden

    def refresh_subjects(self):
        """Aktualisiert die Fächerliste"""
        try:
            # Korrekter DB-Zugriff
            subjects = self.main_window.db.execute("""
                SELECT 
                    s.name,
                    COUNT(DISTINCT c.id) as course_count,
                    att.name as template_name
                FROM subjects s
                LEFT JOIN courses c ON s.name = c.subject
                LEFT JOIN assessment_type_templates att ON (
                    att.subject = s.name AND
                    att.id = (
                        SELECT id FROM assessment_type_templates
                        WHERE subject = s.name
                        ORDER BY created_at DESC
                        LIMIT 1
                    )
                )
                GROUP BY s.name
                ORDER BY s.name
            """).fetchall()
            
            self.table.setRowCount(len(subjects))
            for row, subject in enumerate(subjects):
                # Name
                self.table.setItem(row, 0, QTableWidgetItem(subject['name']))
                # Anzahl Kurse
                self.table.setItem(row, 1, QTableWidgetItem(str(subject['course_count'])))
                # Vorlage
                template = subject['template_name'] or "Keine"
                self.table.setItem(row, 2, QTableWidgetItem(template))
                
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Laden der Fächer: {str(e)}")

    def add_subject(self):
        """Fügt ein neues Fach hinzu"""
        try:
            name, ok = QInputDialog.getText(self, 
                'Neues Fach', 'Name des Fachs:')
            
            if ok and name.strip():
                # Prüfe ob Fach bereits existiert
                existing = self.main_window.db.execute(  # Hier korrigiert
                    "SELECT name FROM subjects WHERE name = ?",
                    (name.strip(),)
                ).fetchone()
                
                if existing:
                    QMessageBox.warning(self, "Warnung", 
                                    "Dieses Fach existiert bereits!")
                    return
                    
                # Füge neues Fach ein
                self.main_window.db.execute(  # Hier korrigiert
                    "INSERT INTO subjects (name) VALUES (?)",
                    (name.strip(),)
                )
                
                # Nach erfolgreichem Speichern
                self.refresh_subjects()
                self.main_window.statusBar().showMessage(
                    f"Fach '{name}' wurde hinzugefügt", 3000
                )
                
                # Alle offenen CourseDialoge aktualisieren
                for window in self.main_window.findChildren(CourseDialog):
                    window.reload_subjects()
                    
                
        except Exception as e:
            QMessageBox.critical(self, "Fehler", 
                            f"Fehler beim Hinzufügen des Fachs: {str(e)}")

    def delete_subject(self):
        """Löscht das ausgewählte Fach"""
        try:
            current = self.table.currentRow()
            if current < 0:
                return
                
            subject = self.table.item(current, 0).text()
            courses = int(self.table.item(current, 1).text())
            
            if courses > 0:
                QMessageBox.warning(self, "Warnung",
                    f"Das Fach '{subject}' wird noch von {courses} Kurs(en) verwendet "
                    "und kann nicht gelöscht werden!")
                return
                
            reply = QMessageBox.question(
                self,
                'Fach löschen',
                f'Möchten Sie das Fach "{subject}" wirklich löschen?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.main_window.db.execute(  # Hier korrigiert
                    "DELETE FROM subjects WHERE name = ?",
                    (subject,)
                )
                
            # Nach erfolgreichem Speichern
            self.refresh_subjects()
            self.main_window.statusBar().showMessage(
                f"Fach '{name}' wurde hinzugefügt", 3000
            )
            
            # Alle offenen CourseDialoge aktualisieren
            for window in self.main_window.findChildren(CourseDialog):
                window.reload_subjects()
                
        except Exception as e:
            QMessageBox.critical(self, "Fehler", 
                            f"Fehler beim Hinzufügen des Fachs: {str(e)}")