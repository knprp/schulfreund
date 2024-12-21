# src/views/tabs/competency_tab.py

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                           QTableWidget, QTableWidgetItem, QHeaderView,
                           QMessageBox, QMenu)
from PyQt6.QtCore import Qt
from src.views.dialogs.competency_dialog import CompetencyDialog

class CompetencyTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setup_ui()
        self.refresh_competencies()

    def setup_ui(self):
        """Erstellt die Benutzeroberfläche des Kompetenz-Tabs"""
        layout = QVBoxLayout(self)
        
        # Tabelle für Kompetenzen
        self.competencies_table = QTableWidget()
        self.competencies_table.setColumnCount(3)
        self.competencies_table.setHorizontalHeaderLabels(['Fach', 'Bereich', 'Beschreibung'])
        
        # Spaltenbreiten anpassen
        header = self.competencies_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        
        # Keine Bearbeitung direkt in der Tabelle
        self.competencies_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.competencies_table)
        
        # Button-Layout
        button_layout = QHBoxLayout()
        
        # Hinzufügen-Button
        btn_add = QPushButton("Kompetenz hinzufügen")
        btn_add.clicked.connect(self.add_competency)
        button_layout.addWidget(btn_add)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # Kontext-Menü für die Tabelle
        self.competencies_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.competencies_table.customContextMenuRequested.connect(self.show_context_menu)

    def add_competency(self):
        """Öffnet den Dialog zum Hinzufügen einer neuen Kompetenz"""
        try:
            dialog = CompetencyDialog(self)
            if dialog.exec():
                data = dialog.get_data()
                self.parent.db.add_competency(data)
                self.refresh_competencies()
                self.parent.statusBar().showMessage(
                    f"Kompetenz wurde hinzugefügt", 3000
                )
        except Exception as e:
            QMessageBox.critical(self, "Fehler", str(e))

    def edit_competency(self, comp_id):
        """Öffnet den Dialog zum Bearbeiten einer Kompetenz"""
        try:
            comp = self.parent.db.get_competency(comp_id)
            if comp:
                dialog = CompetencyDialog(self, comp)
                if dialog.exec():
                    data = dialog.get_data()
                    self.parent.db.update_competency(comp_id, data)
                    self.refresh_competencies()
                    self.parent.statusBar().showMessage(
                        f"Kompetenz wurde aktualisiert", 3000
                    )
        except Exception as e:
            QMessageBox.critical(self, "Fehler", str(e))

    def delete_competency(self, comp_id):
        """Löscht eine Kompetenz nach Bestätigung"""
        try:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Question)
            msg.setText("Möchten Sie diese Kompetenz wirklich löschen?")
            msg.setInformativeText("Dies kann nicht rückgängig gemacht werden.")
            msg.setStandardButtons(
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if msg.exec() == QMessageBox.StandardButton.Yes:
                self.parent.db.delete_competency(comp_id)
                self.refresh_competencies()
                self.parent.statusBar().showMessage(
                    "Kompetenz wurde gelöscht", 3000
                )
        except Exception as e:
            QMessageBox.critical(self, "Fehler", str(e))

    def show_context_menu(self, pos):
        """Zeigt das Kontext-Menü für die Tabelle"""
        item = self.competencies_table.itemAt(pos)
        if item is None:
            return
            
        menu = QMenu()
        edit_action = menu.addAction("Bearbeiten")
        delete_action = menu.addAction("Löschen")
        
        action = menu.exec(self.competencies_table.viewport().mapToGlobal(pos))
        if not action:
            return
            
        row = self.competencies_table.row(item)
        comp_id = self.competencies_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        
        if action == edit_action:
            self.edit_competency(comp_id)
        elif action == delete_action:
            self.delete_competency(comp_id)

    def refresh_competencies(self):
        """Aktualisiert die Tabelle mit allen Kompetenzen"""
        try:
            self.competencies_table.setRowCount(0)
            competencies = self.parent.db.get_all_competencies()
            
            for comp in competencies:
                row = self.competencies_table.rowCount()
                self.competencies_table.insertRow(row)
                
                # ID als UserRole im ersten Item speichern
                item = QTableWidgetItem(comp['subject'])
                item.setData(Qt.ItemDataRole.UserRole, comp['id'])
                self.competencies_table.setItem(row, 0, item)
                
                self.competencies_table.setItem(row, 1, QTableWidgetItem(comp['area']))
                self.competencies_table.setItem(row, 2, QTableWidgetItem(comp['description']))
                
        except Exception as e:
            QMessageBox.critical(
                self, "Fehler", 
                f"Fehler beim Laden der Kompetenzen: {str(e)}"
            )