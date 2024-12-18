from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, 
                           QDialogButtonBox, QCheckBox)

class DeleteLessonDialog(QDialog):
    def __init__(self, parent=None, lesson=None):
        super().__init__(parent)
        self.parent = parent
        self.lesson = lesson
        self.setWindowTitle("Stunde löschen")
        self.delete_all = False
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Basis-Nachricht
        msg = "Möchten Sie diese Stunde wirklich löschen?"
        
        # Bei wiederkehrenden Stunden
        if self.lesson and self.lesson.get('recurring_hash'):
            msg += "\nDies ist eine wiederkehrende Stunde."
            self.all_checkbox = QCheckBox("Alle folgenden Stunden auch löschen")
            layout.addWidget(self.all_checkbox)
            
        layout.addWidget(QLabel(msg))
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Yes | 
            QDialogButtonBox.StandardButton.No
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
    def get_delete_all(self):
        """Gibt zurück, ob alle folgenden Stunden gelöscht werden sollen"""
        if hasattr(self, 'all_checkbox'):
            return self.all_checkbox.isChecked()
        return False