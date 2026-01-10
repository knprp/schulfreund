# src/views/delegates/strikeout_delegate.py

from PyQt6.QtWidgets import QStyledItemDelegate
from PyQt6.QtGui import QPen, QPainter, QColor
from PyQt6.QtCore import Qt, QRect

class StrikeoutDelegate(QStyledItemDelegate):
    def __init__(self, parent=None, db=None, main_window=None):
        super().__init__(parent)
        self.db = db
        self.main_window = main_window
        self.cancelled_color = QColor(255, 0, 0, 128)  # Halbtransparentes Rot
        self.cancelled_text_color = QColor(150, 150, 150)  # Grau für Text
        self.cancelled_bg_color = QColor(245, 245, 245)  # Sehr helles Grau

    def paint(self, painter: QPainter, option, index):
        # Prüfe ob die Stunde ausgefallen ist
        first_item = self.parent().item(index.row(), 0)
        if first_item and first_item.data(Qt.ItemDataRole.UserRole):
            lesson_id = first_item.data(Qt.ItemDataRole.UserRole)
            if self.main_window:
                lesson = self.main_window.controllers.lesson.get_lesson(lesson_id)
            else:
                lesson = self.db.get_lesson(lesson_id)
            
            if lesson and lesson.get('status') == 'cancelled':
                # Zeichne Hintergrund
                painter.fillRect(option.rect, self.cancelled_bg_color)
                
                # Text in Grau zeichnen
                option.palette.setColor(option.palette.ColorRole.Text, self.cancelled_text_color)

        # Normal zeichnen lassen
        super().paint(painter, option, index)

        # Linie nur in der ersten Spalte über die gesamte Breite zeichnen
        if index.column() == 0:
            if first_item and first_item.data(Qt.ItemDataRole.UserRole):
                lesson_id = first_item.data(Qt.ItemDataRole.UserRole)
                if self.main_window:
                lesson = self.main_window.controllers.lesson.get_lesson(lesson_id)
            else:
                lesson = self.db.get_lesson(lesson_id)
                
                if lesson and lesson.get('status') == 'cancelled':
                    painter.save()
                    
                    # Berechne die tatsächliche Breite durch Addition der Spaltenbreiten
                    table = self.parent()
                    row_width = sum(table.columnWidth(i) for i in range(table.columnCount()))
                    
                    # Erstelle ein Rechteck über die gesamte Zeile
                    rect = option.rect
                    rect.setWidth(row_width)
                    
                    # Zeichne die diagonale Linie
                    pen = QPen(self.cancelled_color)
                    pen.setWidth(2)
                    painter.setPen(pen)
                    painter.drawLine(rect.topLeft(), rect.bottomRight())
                    
                    painter.restore()