# src/views/settings/grading_systems_settings.py

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                           QTableWidget, QTableWidgetItem, QLabel, 
                           QHeaderView, QMessageBox, QGroupBox)
from PyQt6.QtCore import Qt
from ..dialogs.grading_system_dialog import GradingSystemDialog

class GradingSystemsSettings(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setup_ui()
        self.load_systems()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Gruppierung für Notensysteme
        group = QGroupBox("Notensysteme")
        group_layout = QVBoxLayout()

        # Tabelle für Notensysteme
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            "Name", "Notenbereich", "Schrittgröße", "Beschreibung"
        ])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.itemSelectionChanged.connect(self.update_preview)
        group_layout.addWidget(self.table)

        # Vorschau-Bereich
        preview_layout = QVBoxLayout()
        preview_layout.addWidget(QLabel("<b>Mögliche Noten:</b>"))
        self.preview_label = QLabel()
        preview_layout.addWidget(self.preview_label)
        group_layout.addLayout(preview_layout)

        # Button-Leiste
        button_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("Neu")
        self.add_btn.clicked.connect(self.add_system)
        button_layout.addWidget(self.add_btn)
        
        self.edit_btn = QPushButton("Bearbeiten")
        self.edit_btn.clicked.connect(self.edit_system)
        button_layout.addWidget(self.edit_btn)
        
        self.delete_btn = QPushButton("Löschen")
        self.delete_btn.clicked.connect(self.delete_system)
        button_layout.addWidget(self.delete_btn)
        
        button_layout.addStretch()
        group_layout.addLayout(button_layout)

        group.setLayout(group_layout)
        layout.addWidget(group)
        layout.addStretch()

    def load_systems(self):
        """Lädt alle Notensysteme in die Tabelle"""
        try:
            systems = self.parent.controllers.grading_system.get_all_grading_systems()
            self.table.setRowCount(len(systems))
            
            for row, system in enumerate(systems):
                # Name
                name_item = QTableWidgetItem(system['name'])
                name_item.setData(Qt.ItemDataRole.UserRole, system['id'])
                self.table.setItem(row, 0, name_item)
                
                # Notenbereich
                range_text = f"{system['min_grade']} - {system['max_grade']}"
                self.table.setItem(row, 1, QTableWidgetItem(range_text))
                
                # Schrittgröße
                self.table.setItem(row, 2, 
                                 QTableWidgetItem(str(system['step_size'])))
                
                # Beschreibung
                if system.get('description'):
                    self.table.setItem(row, 3, 
                                     QTableWidgetItem(system['description']))
                                     
            # Aktiviere/Deaktiviere Buttons je nach Auswahl
            self.update_button_states()
                                     
        except Exception as e:
            QMessageBox.critical(self, "Fehler", 
                               f"Fehler beim Laden der Notensysteme: {str(e)}")

    def update_preview(self):
        """Aktualisiert die Vorschau der möglichen Noten"""
        try:
            self.update_button_states()
            
            current_row = self.table.currentRow()
            if current_row >= 0:
                system_id = self.table.item(current_row, 0).\
                        data(Qt.ItemDataRole.UserRole)
                system = self.parent.controllers.grading_system.get_grading_system(system_id)
                
                if system:
                    # Berechne die Anzahl der Schritte
                    steps = round((system['max_grade'] - system['min_grade']) / 
                                system['step_size'])
                    
                    # Generiere alle möglichen Noten mit korrekter Rundung
                    grades = []
                    for i in range(steps + 1):  # +1 um auch die max_grade einzuschließen
                        grade = round(system['min_grade'] + (i * system['step_size']), 2)
                        # Formatiere auf 2 Dezimalstellen wenn nötig
                        if grade.is_integer():
                            grades.append(str(int(grade)))
                        else:
                            grades.append(f"{grade:.2f}")
                    self.preview_label.setText(", ".join(grades))
            else:
                self.preview_label.clear()
                
        except Exception as e:
            QMessageBox.critical(self, "Fehler", 
                            f"Fehler bei der Vorschau: {str(e)}")

    def update_button_states(self):
        """Aktiviert/Deaktiviert Buttons basierend auf Auswahl"""
        has_selection = self.table.currentRow() >= 0
        self.edit_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)

    def add_system(self):
        """Öffnet Dialog zum Hinzufügen eines neuen Systems"""
        dialog = GradingSystemDialog(self.parent)
        if dialog.exec():
            self.load_systems()

    def edit_system(self):
        """Öffnet Dialog zum Bearbeiten des ausgewählten Systems"""
        current_row = self.table.currentRow()
        if current_row >= 0:
            system_id = self.table.item(current_row, 0).\
                       data(Qt.ItemDataRole.UserRole)
            dialog = GradingSystemDialog(self.parent, system_id)
            if dialog.exec():
                self.load_systems()

    def delete_system(self):
        """Löscht das ausgewählte System nach Bestätigung"""
        current_row = self.table.currentRow()
        if current_row >= 0:
            system_id = self.table.item(current_row, 0).\
                       data(Qt.ItemDataRole.UserRole)
            name = self.table.item(current_row, 0).text()
            
            reply = QMessageBox.question(
                self,
                'Notensystem löschen',
                f'Möchten Sie das Notensystem "{name}" wirklich löschen?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                try:
                    self.parent.controllers.grading_system.delete_grading_system(system_id)
                    self.load_systems()
                except Exception as e:
                    QMessageBox.critical(
                        self, 
                        "Fehler", 
                        f"Fehler beim Löschen: {str(e)}"
                    )