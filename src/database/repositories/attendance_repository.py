# src/database/repositories/attendance_repository.py

from typing import List
from .base_repository import BaseRepository


class AttendanceRepository(BaseRepository):
    """Repository für Anwesenheits-Operationen."""
    
    def mark_absent(self, lesson_id: int, student_id: int) -> None:
        """Markiert einen Schüler als abwesend für eine Stunde.
        
        Args:
            lesson_id: ID der Stunde
            student_id: ID des Schülers
        """
        self.execute(
            """INSERT OR REPLACE INTO student_attendance 
            (student_id, lesson_id)
            VALUES (?, ?)""",
            (student_id, lesson_id)
        )
    
    def mark_present(self, lesson_id: int, student_id: int) -> None:
        """Löscht einen Abwesenheitseintrag (= Schüler war anwesend).
        
        Args:
            lesson_id: ID der Stunde
            student_id: ID des Schülers
        """
        self.execute(
            "DELETE FROM student_attendance WHERE lesson_id = ? AND student_id = ?",
            (lesson_id, student_id)
        )
    
    def get_absent_students(self, lesson_id: int) -> List[int]:
        """Holt die IDs aller abwesenden Schüler für eine Stunde.
        
        Args:
            lesson_id: ID der Stunde
            
        Returns:
            Liste von Schüler-IDs
        """
        cursor = self.execute(
            "SELECT student_id FROM student_attendance WHERE lesson_id = ?",
            (lesson_id,)
        )
        return [row['student_id'] for row in cursor.fetchall()]
