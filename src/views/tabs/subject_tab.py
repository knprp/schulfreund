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
            # Lade Fächer über Controller
            subjects = self.main_window.controllers.subject.get_all_subjects()
            
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
                try:
                    # Füge neues Fach über Controller hinzu
                    self.main_window.controllers.subject.add_subject(name.strip())
                except ValueError as e:
                    QMessageBox.warning(self, "Warnung", str(e))
                    return
                except Exception as e:
                    QMessageBox.critical(self, "Fehler", f"Fehler beim Hinzufügen des Fachs: {str(e)}")
                    return
                
                # Nach erfolgreichem Speichern
                self.refresh_subjects()
                self.main_window.statusBar().showMessage(
                    f"Fach '{name}' wurde hinzugefügt", 3000
                )
                
                # Benachrichtige offene Dialoge über die Änderung
                self.main_window.refresh_all()
                
        except Exception as e:
            QMessageBox.critical(self, "Fehler", 
                            f"Fehler beim Hinzufügen des Fachs: {str(e)}")

    def delete_subject(self):
        """Löscht das ausgewählte Fach."""
        try:
            current = self.table.currentRow()
            if current < 0:
                return
                    
            subject = self.table.item(current, 0).text()
            
            reply = QMessageBox.question(
                self,
                'Fach löschen',
                f'Möchten Sie das Fach "{subject}" wirklich löschen?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                try:
                    # Lösche Fach über Controller
                    self.main_window.controllers.subject.delete_subject(subject)
                except ValueError as e:
                    QMessageBox.warning(self, "Warnung", str(e))
                    return
                except Exception as e:
                    QMessageBox.critical(self, "Fehler", f"Fehler beim Löschen des Fachs: {str(e)}")
                    return
                    
                # Nach erfolgreichem Speichern
                self.refresh_subjects()
                self.main_window.statusBar().showMessage(
                    f"Fach '{subject}' wurde gelöscht", 3000
                )
                    
        except Exception as e:
            QMessageBox.critical(self, "Fehler", 
                            f"Fehler beim Löschen des Fachs: {str(e)}")