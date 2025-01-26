# src/views/dialogs/grading_system_dialog.py

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                           QLineEdit, QDoubleSpinBox, QTextEdit, QTreeWidget,
                           QTreeWidgetItem, QPushButton, QDialogButtonBox, 
                           QMessageBox)
from PyQt6.QtCore import Qt

class GradingSystemDialog(QDialog):
    def __init__(self, parent=None, system_id=None, template_id=None, course_id=None):
        super().__init__(parent)
        self.parent = parent
        self.system_id = system_id
        self.template_id = template_id
        self.course_id = course_id
        self.mode = self._determine_mode()
        
        self.setWindowTitle(self._get_title())
        self.setup_ui()
        self.load_data()

    def _determine_mode(self):
        if self.system_id:
            return "system"
        elif self.template_id:
            return "template"
        elif self.course_id:
            return "course"
        return "system"  # Fallback

    def _get_title(self):
        if self.mode == "system":
            return "Notensystem " + ("bearbeiten" if self.system_id else "hinzufügen")
        elif self.mode == "template":
            return "Bewertungsvorlage bearbeiten"
        else:
            return "Kursbewertungen bearbeiten"

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        if self.mode == "system":
            self.setup_system_ui(layout)
        else:
            self.setup_types_ui(layout)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def setup_system_ui(self, layout):
        # Bestehender System-UI Code
        layout.addWidget(QLabel("Name:"))
        self.name = QLineEdit()
        self.name.setPlaceholderText("z.B. Unterstufe 1-6")
        layout.addWidget(self.name)
        
        range_layout = QHBoxLayout()
        range_layout.addWidget(QLabel("Minimale Note:"))
        self.min_grade = QDoubleSpinBox()
        self.min_grade.setRange(0, 15)
        self.min_grade.setDecimals(2)
        range_layout.addWidget(self.min_grade)
        
        range_layout.addWidget(QLabel("Maximale Note:"))
        self.max_grade = QDoubleSpinBox()
        self.max_grade.setRange(0, 15)
        self.max_grade.setDecimals(2)
        range_layout.addWidget(self.max_grade)
        
        layout.addLayout(range_layout)
        
        step_layout = QHBoxLayout()
        step_layout.addWidget(QLabel("Schrittgröße:"))
        self.step_size = QDoubleSpinBox()
        self.step_size.setRange(0.01, 1)
        self.step_size.setDecimals(2)
        self.step_size.setValue(0.33)
        step_layout.addWidget(self.step_size)
        step_layout.addStretch()
        
        layout.addLayout(step_layout)
        
        layout.addWidget(QLabel("Beschreibung (optional):"))
        self.description = QTextEdit()
        self.description.setMaximumHeight(100)
        layout.addWidget(self.description)

    def setup_types_ui(self, layout):
        # Baumansicht für Typen
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Name", "Gewichtung"])
        self.tree.setColumnWidth(0, 250)
        layout.addWidget(self.tree)

        # Buttons für Aktionen
        btn_layout = QHBoxLayout()
        
        add_root_btn = QPushButton("Haupttyp hinzufügen")
        add_root_btn.clicked.connect(self.add_root_type)
        btn_layout.addWidget(add_root_btn)
        
        add_sub_btn = QPushButton("Untertyp hinzufügen")
        add_sub_btn.clicked.connect(self.add_sub_type)
        btn_layout.addWidget(add_sub_btn)
        
        edit_btn = QPushButton("Bearbeiten")
        edit_btn.clicked.connect(self.edit_type)
        btn_layout.addWidget(edit_btn)
        
        delete_btn = QPushButton("Löschen")
        delete_btn.clicked.connect(self.delete_type)
        btn_layout.addWidget(delete_btn)
        
        layout.addLayout(btn_layout)

    def load_data(self):
        if self.mode == "system":
            self.load_system_data()
        else:
            self.load_types_data()

    def load_system_data(self):
        """Lädt die Daten eines bestehenden Systems"""
        try:
            if not self.system_id:
                return
                
            system = self.parent.db.get_grading_system(self.system_id)
            if system:
                self.name.setText(system['name'])
                self.min_grade.setValue(system['min_grade'])
                self.max_grade.setValue(system['max_grade'])
                self.step_size.setValue(system['step_size'])
                if system.get('description'):
                    self.description.setText(system['description'])
            else:
                raise ValueError(f"System mit ID {self.system_id} nicht gefunden")

        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Laden: {str(e)}")
            self.reject()

    def load_types_data(self):
        """Lädt die Bewertungstypen"""
        try:
            self.tree.clear()
            
            if self.mode == "template":
                items = self.parent.db.get_template_items(self.template_id)
            else:
                items = self.parent.db.get_assessment_types(self.course_id)
                
            # Erstelle Dictionary für schnellen Zugriff
            self.items_by_id = {item['id']: item for item in items}
            
            # Baue Baum auf
            for item in items:
                if not item['parent_type_id' if self.mode == "course" else 'parent_item_id']:
                    self.add_item_to_tree(item)

        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Laden: {str(e)}")

    def add_item_to_tree(self, item, parent=None):
        tree_item = QTreeWidgetItem(parent or self.tree)
        tree_item.setText(0, item['name'])
        tree_item.setText(1, str(item['default_weight' if self.mode == "template" else 'weight']))
        tree_item.setData(0, Qt.ItemDataRole.UserRole, item['id'])
        
        # Füge Kinder hinzu
        parent_key = 'parent_type_id' if self.mode == "course" else 'parent_item_id'
        for child in [i for i in self.items_by_id.values() if i.get(parent_key) == item['id']]:
            self.add_item_to_tree(child, tree_item)
            
        return tree_item

    def add_root_type(self):
        dialog = TypeDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            try:
                if self.mode == "template":
                    type_id = self.parent.db.add_template_item(
                        self.template_id,
                        data['name'],
                        None,
                        data['weight']
                    )
                else:
                    type_id = self.parent.db.add_assessment_type(
                        self.course_id,
                        data['name'],
                        None,
                        data['weight']
                    )
                
                self.load_types_data()
                
            except Exception as e:
                QMessageBox.critical(self, "Fehler", str(e))

    def add_sub_type(self):
        current = self.tree.currentItem()
        if not current:
            QMessageBox.warning(self, "Warnung", "Bitte wählen Sie einen übergeordneten Typ aus")
            return
            
        dialog = TypeDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            try:
                parent_id = current.data(0, Qt.ItemDataRole.UserRole)
                
                if self.mode == "template":
                    type_id = self.parent.db.add_template_item(
                        self.template_id,
                        data['name'],
                        parent_id,
                        data['weight']
                    )
                else:
                    type_id = self.parent.db.add_assessment_type(
                        self.course_id,
                        data['name'],
                        parent_id,
                        data['weight']
                    )
                
                self.load_types_data()
                
            except Exception as e:
                QMessageBox.critical(self, "Fehler", str(e))

    def edit_type(self):
        current = self.tree.currentItem()
        if not current:
            return
            
        type_id = current.data(0, Qt.ItemDataRole.UserRole)
        type_data = self.items_by_id[type_id]
        
        dialog = TypeDialog(self, type_data)
        if dialog.exec():
            data = dialog.get_data()
            try:
                if self.mode == "template":
                    self.parent.db.update_template_item(
                        type_id,
                        data['name'],
                        type_data['parent_item_id'],
                        data['weight']
                    )
                else:
                    self.parent.db.update_assessment_type(
                        type_id,
                        data['name'],
                        type_data['parent_type_id'],
                        data['weight']
                    )
                
                self.load_types_data()
                
            except Exception as e:
                QMessageBox.critical(self, "Fehler", str(e))

    def delete_type(self):
        current = self.tree.currentItem()
        if not current:
            return
            
        type_id = current.data(0, Qt.ItemDataRole.UserRole)
        
        reply = QMessageBox.question(
            self,
            "Löschen bestätigen",
            "Möchten Sie diesen Bewertungstyp wirklich löschen? "
            "Alle Untertypen werden ebenfalls gelöscht.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                if self.mode == "template":
                    self.parent.db.delete_template_item(type_id)
                else:
                    self.parent.db.delete_assessment_type(type_id)
                
                self.load_types_data()
                
            except Exception as e:
                QMessageBox.critical(self, "Fehler", str(e))

    def validate_and_accept(self):
        if self.mode == "system":
            self.validate_system()
        else:
            self.validate_types()

    def validate_system(self):
        try:
            name = self.name.text().strip()
            if not name:
                raise ValueError("Bitte geben Sie einen Namen ein")

            min_grade = self.min_grade.value()
            max_grade = self.max_grade.value()
            if min_grade >= max_grade:
                raise ValueError("Die minimale Note muss kleiner als die maximale Note sein")

            step_size = self.step_size.value()
            if step_size <= 0:
                raise ValueError("Die Schrittgröße muss größer als 0 sein")
                
            grade_range = max_grade - min_grade
            if step_size >= grade_range:
                raise ValueError("Die Schrittgröße muss kleiner als der Notenbereich sein")

            self.save_system()
            self.accept()

        except ValueError as e:
            QMessageBox.warning(self, "Eingabefehler", str(e))

    def validate_types(self):
        def check_weights(item):
            if not item:
                return True
                
            children = [self.tree.topLevelItem(i) if item is None 
                       else item.child(i) 
                       for i in range(item.childCount() if item else self.tree.topLevelItemCount())]
            
            if not children:
                return True
                
            total_weight = sum(float(child.text(1)) for child in children)
            if abs(total_weight - 1.0) > 0.01:  # Erlaube kleine Rundungsfehler
                return False
                
            return all(check_weights(child) for child in children)
        
        if not check_weights(None):
            reply = QMessageBox.question(
                self,
                "Ungültige Gewichtungen",
                "Die Gewichtungen innerhalb einer Ebene ergeben nicht 100%. "
                "Möchten Sie trotzdem fortfahren?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return
        
        self.accept()

    def save_system(self):
        try:
            data = {
                'name': self.name.text().strip(),
                'min_grade': self.min_grade.value(),
                'max_grade': self.max_grade.value(),
                'step_size': self.step_size.value(),
                'description': self.description.toPlainText().strip() or None
            }

            if self.system_id:
                self.parent.db.update_grading_system(self.system_id, **data)
            else:
                self.system_id = self.parent.db.add_grading_system(**data)

        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Speichern: {str(e)}")
            raise
        


class TypeDialog(QDialog):
    def __init__(self, parent=None, type_data=None):
        super().__init__(parent)
        self.type_data = type_data
        self.setWindowTitle("Bewertungstyp bearbeiten" if type_data else "Bewertungstyp hinzufügen")
        self.setup_ui()
        
        if type_data:
            self.load_type_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Name
        layout.addWidget(QLabel("Name:"))
        self.name = QLineEdit()
        layout.addWidget(self.name)
        
        # Gewichtung
        layout.addWidget(QLabel("Gewichtung:"))
        self.weight = QDoubleSpinBox()
        self.weight.setRange(0.01, 1.0)
        self.weight.setDecimals(2)
        self.weight.setValue(1.0)
        self.weight.setSingleStep(0.1)
        layout.addWidget(self.weight)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.validate_and_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def load_type_data(self):
        self.name.setText(self.type_data['name'])
        self.weight.setValue(
            self.type_data['default_weight' if 'default_weight' in self.type_data else 'weight']
        )

    def validate_and_accept(self):
        if not self.name.text().strip():
            QMessageBox.warning(self, "Fehler", "Bitte geben Sie einen Namen ein")
            return
            
        self.accept()

    def get_data(self):
        return {
            'name': self.name.text().strip(),
            'weight': self.weight.value()
        }