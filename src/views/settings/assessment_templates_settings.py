# src/views/settings/assessment_templates_settings.py

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                           QTreeWidget, QTreeWidgetItem, QLabel, 
                           QHeaderView, QMessageBox, QGroupBox)
from PyQt6.QtCore import Qt
from src.views.dialogs.assessment_type_dialog import AssessmentTypeDialog
from src.views.dialogs.assessment_template_dialog import AssessmentTemplateDialog

class AssessmentTemplatesSettings(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setup_ui()
        self.load_templates()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Gruppierung für Vorlagen
        group = QGroupBox("Bewertungsvorlagen")
        group_layout = QVBoxLayout()

        # Baumartige Ansicht für Vorlagen und ihre Bewertungstypen
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels([
            "Name", "Fach", "Notensystem", "Beschreibung"
        ])
        header = self.tree.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.tree.itemSelectionChanged.connect(self.update_button_states)
        group_layout.addWidget(self.tree)

        # Button-Leiste
        button_layout = QHBoxLayout()
        
        self.add_template_btn = QPushButton("Neue Vorlage")
        self.add_template_btn.clicked.connect(self.add_template)
        button_layout.addWidget(self.add_template_btn)
        
        self.add_type_btn = QPushButton("Bewertungstyp hinzufügen")
        self.add_type_btn.clicked.connect(self.add_type)
        button_layout.addWidget(self.add_type_btn)
        
        self.edit_btn = QPushButton("Bearbeiten")
        self.edit_btn.clicked.connect(self.edit_item)
        button_layout.addWidget(self.edit_btn)
        
        self.delete_btn = QPushButton("Löschen")
        self.delete_btn.clicked.connect(self.delete_item)
        button_layout.addWidget(self.delete_btn)
        
        button_layout.addStretch()
        group_layout.addLayout(button_layout)

        group.setLayout(group_layout)
        layout.addWidget(group)
        layout.addStretch()

    def update_button_states(self):
        """Aktiviert/Deaktiviert Buttons basierend auf Auswahl"""
        selected = self.tree.selectedItems()
        has_selection = len(selected) > 0
        
        self.edit_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)
        
        # Add_type nur aktivieren wenn eine Vorlage oder ein Typ ausgewählt ist
        self.add_type_btn.setEnabled(has_selection)

    def load_templates(self):
        """Lädt alle Vorlagen und ihre Bewertungstypen in die Baumansicht"""
        self.tree.clear()
        
        try:
            # Hole alle Vorlagen
            templates = self.parent.db.get_all_assessment_templates()
            
            for template in templates:
                # Erstelle Template-Item
                template_item = QTreeWidgetItem([
                    template['name'],
                    template['subject'],
                    template.get('grading_system_name', '-'),
                    template.get('description', '')
                ])
                template_item.setData(0, Qt.ItemDataRole.UserRole, 
                                    {'id': template['id'], 'type': 'template'})
                
                # Hole und füge Bewertungstypen hinzu
                items = self.parent.db.get_template_items(template['id'])
                self._add_template_items(template_item, items)
                
                self.tree.addTopLevelItem(template_item)
                template_item.setExpanded(True)
                
        except Exception as e:
            QMessageBox.critical(self, "Fehler", 
                            f"Fehler beim Laden der Vorlagen: {str(e)}")

    def _add_template_items(self, parent_item: QTreeWidgetItem, items: list, 
                        parent_id: int = None):
        """Fügt Bewertungstypen rekursiv zur Baumstruktur hinzu"""
        # Filtere Items für aktuelle Ebene
        level_items = [i for i in items if i['parent_item_id'] == parent_id]
        
        for item in level_items:
            # Erstelle Item
            tree_item = QTreeWidgetItem([
                item['name'],
                '',  # Fach leer bei Typen
                f"Gewichtung: {item['default_weight']}",
                ''   # Keine Beschreibung bei Typen
            ])
            tree_item.setData(0, Qt.ItemDataRole.UserRole, 
                            {'id': item['id'], 'type': 'type'})
            
            # Füge zum parent hinzu
            parent_item.addChild(tree_item)
            
            # Rekursiv für Kinder
            self._add_template_items(tree_item, items, item['id'])
            tree_item.setExpanded(True)

    def add_template(self):
        """Öffnet Dialog zum Erstellen einer neuen Vorlage"""
        dialog = AssessmentTemplateDialog(self.parent)
        if dialog.exec():
            try:
                data = dialog.get_data()
                self.parent.db.add_assessment_template(**data)
                self.load_templates()
            except Exception as e:
                QMessageBox.critical(self, "Fehler",
                                f"Fehler beim Speichern der Vorlage: {str(e)}")

    def edit_item(self):
        """Bearbeitet die ausgewählte Vorlage oder den Bewertungstyp"""
        selected = self.tree.selectedItems()
        if not selected:
            return
            
        item = selected[0]
        item_data = item.data(0, Qt.ItemDataRole.UserRole)
        
        if item_data['type'] == 'template':
            # Vorlage bearbeiten
            try:
                template = self.parent.db.get_assessment_template(item_data['id'])
                if template:
                    dialog = AssessmentTemplateDialog(self.parent, template)
                    if dialog.exec():
                        data = dialog.get_data()
                        self.parent.db.update_assessment_template(item_data['id'], **data)
                        self.load_templates()
            except Exception as e:
                QMessageBox.critical(self, "Fehler",
                                f"Fehler beim Bearbeiten der Vorlage: {str(e)}")
        else:
            # Bewertungstyp bearbeiten (später implementieren)
            pass

    def add_type(self):
        """Öffnet Dialog zum Hinzufügen eines Bewertungstyps"""
        selected = self.tree.selectedItems()
        if not selected:
            return

        item = selected[0]
        item_data = item.data(0, Qt.ItemDataRole.UserRole)
        
        if item_data['type'] == 'template':
            template_id = item_data['id']
        else:  # type ist ein Bewertungstyp
            template_id = item.parent().data(0, Qt.ItemDataRole.UserRole)['id']
            
        parent_id = item_data['id'] if item_data['type'] == 'type' else None

        try:
            dialog = AssessmentTypeDialog(self.parent, template_id, parent_id)
            if dialog.exec():
                data = dialog.get_data()
                self.parent.db.add_template_item(template_id, **data)
                self.load_templates()
        except Exception as e:
            QMessageBox.critical(self, "Fehler",
                            f"Fehler beim Hinzufügen des Bewertungstyps: {str(e)}")

    def delete_item(self):
        """Löscht die ausgewählte Vorlage oder den Bewertungstyp"""
        selected = self.tree.selectedItems()
        if not selected:
            return

        item = selected[0]
        item_data = item.data(0, Qt.ItemDataRole.UserRole)
        
        # Bestätigungsdialog 
        msg = ("Vorlage" if item_data['type'] == 'template' else "Bewertungstyp")
        reply = QMessageBox.question(
            self,
            'Löschen bestätigen',
            f'Möchten Sie diesen {msg} wirklich löschen?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                if item_data['type'] == 'template':
                    self.parent.db.delete_assessment_template(item_data['id'])
                else:
                    self.parent.db.delete_template_item(item_data['id']) 
                self.load_templates()
            except Exception as e:
                QMessageBox.critical(self, "Fehler",
                                    f"Fehler beim Löschen: {str(e)}")