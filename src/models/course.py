# src/models/course.py

from datetime import datetime
from typing import List, Optional, Dict

class Course:
    def __init__(self, id: Optional[int] = None, name: str = "", 
                 type: str = "course", subject: Optional[str] = None,
                 description: Optional[str] = None):
        self.id = id
        self.name = name
        self.type = type
        self.subject = subject
        self.description = description

    @staticmethod
    def create(db, name: str, type: str = "course", subject: Optional[str] = None,
               description: Optional[str] = None) -> 'Course':
        """Erstellt einen neuen Kurs in der Datenbank."""
        if not name or not name.strip():
            raise ValueError("Der Name darf nicht leer sein")
        if type not in ["class", "course"]:
            raise ValueError("Typ muss 'class' oder 'course' sein")
            
        cursor = db.execute(
            """INSERT INTO courses (name, type, subject, description) 
               VALUES (?, ?, ?, ?)""",
            (name.strip(), type, subject, description)
        )
        return Course(cursor.lastrowid, name, type, subject, description)

    @staticmethod
    def get_by_id(db, course_id: int) -> Optional['Course']:
        """Lädt einen Kurs anhand seiner ID."""
        cursor = db.execute(
            "SELECT * FROM courses WHERE id = ?",
            (course_id,)
        )
        row = cursor.fetchone()
        if row:
            return Course(
                id=row['id'],
                name=row['name'],
                type=row['type'],
                subject=row['subject'],
                description=row['description']
            )
        return None

    def add_student(self, db, student_id: int, start_date: str, end_date: str) -> None:
        """Fügt einen Schüler zum Kurs hinzu."""
        if not self.id:
            raise ValueError("Kurs hat keine ID")
            
        db.execute(
            """INSERT INTO student_courses (student_id, course_id, start_date, end_date)
               VALUES (?, ?, ?, ?)""",
            (student_id, self.id, start_date, end_date)
        )

    def get_students(self, db, date: Optional[str] = None) -> List[Dict]:
        """Holt alle Schüler des Kurses, optional zu einem bestimmten Datum."""
        if not self.id:
            raise ValueError("Kurs hat keine ID")
            
        query = """
            SELECT s.*, sc.start_date, sc.end_date
            FROM students s
            JOIN student_courses sc ON s.id = sc.student_id
            WHERE sc.course_id = ?
        """
        params = [self.id]
        
        if date:
            query += " AND sc.start_date <= ? AND sc.end_date >= ?"
            params.extend([date, date])
            
        cursor = db.execute(query, tuple(params))
        return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def get_all(db) -> List['Course']:
        """Lädt alle Kurse aus der Datenbank."""
        cursor = db.execute(
            "SELECT * FROM courses ORDER BY name"
        )
        return [Course(
            id=row['id'],
            name=row['name'],
            type=row['type'],
            subject=row['subject'],
            description=row['description']
        ) for row in cursor.fetchall()]

    def update(self, db) -> None:
        """Aktualisiert die Kursdaten in der Datenbank."""
        if not self.id:
            raise ValueError("Kurs hat keine ID")
            
        db.execute(
            """UPDATE courses 
               SET name = ?, type = ?, subject = ?, description = ?,
                   updated_at = CURRENT_TIMESTAMP
               WHERE id = ?""",
            (self.name, self.type, self.subject, self.description, self.id)
        )

    def delete(self, db) -> None:
        """Löscht den Kurs aus der Datenbank."""
        if not self.id:
            raise ValueError("Kurs hat keine ID")
            
        db.execute("DELETE FROM courses WHERE id = ?", (self.id,))

    def __str__(self) -> str:
        return f"{self.name} ({self.type})"

    def __repr__(self) -> str:
        return f"Course(id={self.id}, name='{self.name}', type='{self.type}')"