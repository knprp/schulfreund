# src/models/student/remarks.py

from datetime import datetime
from typing import List, Optional, Dict

class StudentRemark:
    """Repräsentiert eine einzelne Bemerkung für einen Schüler."""
    
    def __init__(self, id: Optional[int] = None, student_id: int = None,
                 lesson_id: Optional[int] = None, remark_text: str = "",
                 type: str = "general", created_at: Optional[str] = None):
        self.id = id
        self.student_id = student_id
        self.lesson_id = lesson_id
        self.remark_text = remark_text
        self.type = type
        self.created_at = created_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def create(db, student_id: int, remark_text: str, type: str = "general",
               lesson_id: Optional[int] = None) -> 'StudentRemark':
        """Erstellt eine neue Bemerkung in der Datenbank."""
        if not remark_text or not remark_text.strip():
            raise ValueError("Der Text darf nicht leer sein")
            
        cursor = db.execute(
            """INSERT INTO student_remarks 
               (student_id, lesson_id, remark_text, type, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            (student_id, lesson_id, remark_text.strip(), type,
             datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        return StudentRemark(cursor.lastrowid, student_id, lesson_id, 
                           remark_text, type)

    @staticmethod
    def get_by_id(db, remark_id: int) -> Optional['StudentRemark']:
        """Lädt eine Bemerkung anhand ihrer ID."""
        cursor = db.execute(
            "SELECT * FROM student_remarks WHERE id = ?",
            (remark_id,)
        )
        row = cursor.fetchone()
        if row:
            return StudentRemark(
                id=row['id'],
                student_id=row['student_id'],
                lesson_id=row['lesson_id'],
                remark_text=row['remark_text'],
                type=row['type'],
                created_at=row['created_at']
            )
        return None

    @staticmethod
    def get_for_student(db, student_id: int, 
                       type: Optional[str] = None) -> List['StudentRemark']:
        """Lädt alle Bemerkungen eines Schülers, optional gefiltert nach Typ."""
        query = "SELECT * FROM student_remarks WHERE student_id = ?"
        params = [student_id]
        
        if type:
            query += " AND type = ?"
            params.append(type)
            
        query += " ORDER BY created_at DESC"
        
        cursor = db.execute(query, tuple(params))
        return [StudentRemark(
            id=row['id'],
            student_id=row['student_id'],
            lesson_id=row['lesson_id'],
            remark_text=row['remark_text'],
            type=row['type'],
            created_at=row['created_at']
        ) for row in cursor.fetchall()]

    def update(self, db) -> None:
        """Aktualisiert die Bemerkung in der Datenbank."""
        if not self.id:
            raise ValueError("Bemerkung hat keine ID")
        if not self.remark_text or not self.remark_text.strip():
            raise ValueError("Der Text darf nicht leer sein")
            
        db.execute(
            """UPDATE student_remarks 
               SET remark_text = ?, type = ?, lesson_id = ?
               WHERE id = ?""",
            (self.remark_text.strip(), self.type, self.lesson_id, self.id)
        )

    def delete(self, db) -> None:
        """Löscht die Bemerkung aus der Datenbank."""
        if not self.id:
            raise ValueError("Bemerkung hat keine ID")
            
        db.execute("DELETE FROM student_remarks WHERE id = ?", (self.id,))

    def __str__(self) -> str:
        return f"{self.created_at}: {self.remark_text}"

    def __repr__(self) -> str:
        return (f"StudentRemark(id={self.id}, student_id={self.student_id}, "
                f"type='{self.type}', text='{self.remark_text}')")