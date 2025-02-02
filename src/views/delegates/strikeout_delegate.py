# src/views/delegates/strikeout_delegate.py

from PyQt6.QtWidgets import QStyledItemDelegate
from PyQt6.QtGui import QPen, QPainter, QColor
from PyQt6.QtCore import Qt, QRect

class StrikeoutDelegate(QStyledItemDelegate):
    def __init__(self, parent=None, db=None):
        super().__init__(parent)
        self.db = db
        # Farben für verschiedene Zustände
        self.cancelled_color = QColor(255, 0, 0, 128)  # Halbtransparentes Rot
        self.cancelled_text_color = QColor(150, 150, 150)  # Grau für Text
        self.cancelled_bg_color = QColor(245, 245, 245)  # Sehr helles Grau

    def paint(self, painter: QPainter, option, index):
        # Debug print
        print(f"Paint called for row {index.row()}, column {index.column()}")
        
        # Prüfe ob die Stunde ausgefallen ist
        first_item = self.parent().item(index.row(), 0)
        if first_item and first_item.data(Qt.ItemDataRole.UserRole):
            lesson_id = first_item.data(Qt.ItemDataRole.UserRole)
            print(f"Found lesson_id: {lesson_id}")  # Debug print
            lesson = self.db.get_lesson(lesson_id)
            print(f"Lesson status: {lesson.get('status') if lesson else 'None'}")  # Debug print
            
            if lesson and lesson.get('status') == 'cancelled':
                    # Zeichne Hintergrund
                    painter.fillRect(option.rect, self.cancelled_bg_color)
                    
                    # Text in Grau zeichnen
                    option.palette.setColor(option.palette.ColorRole.Text, self.cancelled_text_color)

            # Normal zeichnen lassen
            super().paint(painter, option, index)

            # Nach dem normalen Zeichnen die diagonale Linie für ausgefallene Stunden
            if first_item and first_item.data(Qt.ItemDataRole.UserRole):
                lesson_id = first_item.data(Qt.ItemDataRole.UserRole)
                lesson = self.db.get_lesson(lesson_id)
                
                if lesson and lesson.get('status') == 'cancelled':
                    painter.save()
                    
                    # Konfiguriere den Stift
                    pen = QPen(self.cancelled_color)
                    pen.setWidth(2)
                    painter.setPen(pen)
                    
                    # Zeichne die Linie
                    rect = option.rect
                    painter.drawLine(rect.topLeft(), rect.bottomRight())
                    
                    painter.restore()