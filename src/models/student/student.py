# src/models/student.py

from datetime import datetime
from typing import List, Optional
from .remarks import StudentRemark

class Student:
    def __init__(self, id: Optional[int] = None, name: str = "", created_at: Optional[str] = None):
        self.id = id
        self.name = name
        self.created_at = created_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def create(db, name: str) -> 'Student':
        """Erstellt einen neuen Schüler in der Datenbank."""
        if not name or not name.strip():
            raise ValueError("Der Name darf nicht leer sein")
            
        cursor = db.execute(
            "INSERT INTO students (name, created_at) VALUES (?, ?)",
            (name.strip(), datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        return Student(cursor.lastrowid, name)

    @staticmethod
    def get_by_id(db, student_id: int) -> Optional['Student']:
        """Lädt einen Schüler anhand seiner ID."""
        cursor = db.execute(
            "SELECT id, name, created_at FROM students WHERE id = ?",
            (student_id,)
        )
        row = cursor.fetchone()
        if row:
            return Student(row['id'], row['name'], row['created_at'])
        return None

    @staticmethod
    def get_all(db) -> List['Student']:
        """Lädt alle Schüler aus der Datenbank."""
        cursor = db.execute(
            "SELECT id, name, created_at FROM students ORDER BY name"
        )
        return [Student(row['id'], row['name'], row['created_at']) 
                for row in cursor.fetchall()]

    def update(self, db) -> None:
        """Aktualisiert die Schülerdaten in der Datenbank."""
        if not self.id:
            raise ValueError("Schüler hat keine ID")
        if not self.name or not self.name.strip():
            raise ValueError("Der Name darf nicht leer sein")
            
        db.execute(
            "UPDATE students SET name = ? WHERE id = ?",
            (self.name.strip(), self.id)
        )

    def delete(self, db) -> None:
        """Löscht den Schüler aus der Datenbank."""
        if not self.id:
            raise ValueError("Schüler hat keine ID")
            
        db.execute("DELETE FROM students WHERE id = ?", (self.id,))

    def get_grades(self, db) -> list:
        """Holt alle Noten des Schülers."""
        if not self.id:
            raise ValueError("Schüler hat keine ID")
            
        cursor = db.execute('''
            SELECT g.*, l.subject, l.date, c.area, c.description
            FROM grades g
            JOIN lessons l ON g.lesson_id = l.id
            JOIN competencies c ON g.competency_id = c.id
            WHERE g.student_id = ?
            ORDER BY l.date DESC
        ''', (self.id,))
        return [dict(row) for row in cursor.fetchall()]

    def get_grade_statistics(self, db) -> dict:
        """Berechnet Notenstatistiken für den Schüler."""
        if not self.id:
            raise ValueError("Schüler hat keine ID")
            
        cursor = db.execute('''
            SELECT 
                l.subject,
                COUNT(*) as count,
                ROUND(AVG(g.grade * g.weight), 2) as weighted_average,
                MIN(g.grade) as best_grade,
                MAX(g.grade) as worst_grade
            FROM grades g
            JOIN lessons l ON g.lesson_id = l.id
            WHERE g.student_id = ?
            GROUP BY l.subject
        ''', (self.id,))

    def add_remark(self, db, text: str, type: str = "general", 
                lesson_id: Optional[int] = None) -> StudentRemark:
        """Fügt eine neue Bemerkung für den Schüler hinzu."""
        if not self.id:
            raise ValueError("Schüler hat keine ID")
        return StudentRemark.create(db, self.id, text, type, lesson_id)

    def get_remarks(self, db, type: Optional[str] = None) -> List[StudentRemark]:
        """Holt alle Bemerkungen des Schülers, optional gefiltert nach Typ."""
        if not self.id:
            raise ValueError("Schüler hat keine ID")
        return StudentRemark.get_for_student(db, self.id, type)

    def get_latest_remarks(self, db, limit: int = 5) -> List[StudentRemark]:
        """Holt die neuesten Bemerkungen des Schülers."""
        if not self.id:
            raise ValueError("Schüler hat keine ID")
            
        cursor = db.execute(
            """SELECT * FROM student_remarks 
            WHERE student_id = ? 
            ORDER BY created_at DESC LIMIT ?""",
            (self.id, limit)
        )
        return [StudentRemark(
            id=row['id'],
            student_id=row['student_id'],
            lesson_id=row['lesson_id'],
            remark_text=row['remark_text'],
            type=row['type'],
            created_at=row['created_at']
        ) for row in cursor.fetchall()]
        
        return {row['subject']: dict(row) for row in cursor.fetchall()}

    def __str__(self) -> str:
        return f"{self.name}"

    def __repr__(self) -> str:
        return f"Student(id={self.id}, name='{self.name}')"

