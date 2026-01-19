# src/models/student.py

from datetime import datetime
from typing import List, Optional
from .remarks import StudentRemark

class Student:
    def __init__(self, id: Optional[int] = None, first_name: str = "", 
                 last_name: str = "", created_at: Optional[str] = None):
        self.id = id
        self.first_name = first_name
        self.last_name = last_name
        self.created_at = created_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def create(db, first_name: str, last_name: str) -> 'Student':
        """Erstellt einen neuen Schüler in der Datenbank."""
        if not first_name.strip() or not last_name.strip():
            raise ValueError("Vor- und Nachname dürfen nicht leer sein")
            
        cursor = db.execute(
            "INSERT INTO students (first_name, last_name, created_at) VALUES (?, ?, ?)",
            (first_name.strip(), last_name.strip(), 
             datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        return Student(cursor.lastrowid, first_name, last_name)

    @staticmethod
    def get_by_id(db, student_id: int) -> Optional['Student']:
        """Lädt einen Schüler anhand seiner ID."""
        cursor = db.execute(
            "SELECT id, first_name, last_name, created_at FROM students WHERE id = ?",
            (student_id,)
        )
        row = cursor.fetchone()
        if row:
            return Student(row['id'], row['first_name'], row['last_name'], row['created_at'])
        return None

    @staticmethod
    def get_all(db) -> List['Student']:
        """Lädt alle Schüler aus der Datenbank, sortiert nach Nachname."""
        cursor = db.execute(
            "SELECT id, first_name, last_name, created_at FROM students ORDER BY last_name, first_name"
        )
        return [Student(row['id'], row['first_name'], row['last_name'], row['created_at']) 
                for row in cursor.fetchall()]

    def update(self, db) -> None:
        """Aktualisiert die Schülerdaten in der Datenbank."""
        if not self.id:
            raise ValueError("Schüler hat keine ID")
        if not self.first_name.strip() or not self.last_name.strip():
            raise ValueError("Vor- und Nachname dürfen nicht leer sein")
            
        db.execute(
            "UPDATE students SET first_name = ?, last_name = ? WHERE id = ?",
            (self.first_name.strip(), self.last_name.strip(), self.id)
        )

    def delete(self, db) -> None:
        """Löscht den Schüler aus der Datenbank."""
        if not self.id:
            raise ValueError("Schüler hat keine ID")
        
        print(f"DEBUG: Versuche Schüler mit ID {self.id} zu löschen")    
        db.execute("DELETE FROM students WHERE id = ?", (self.id,))
        print(f"DEBUG: Schüler gelöscht. Prüfe ob noch in student_courses...")

        # Debug: Prüfe ob noch Einträge existieren
        cursor = db.execute(
            "SELECT COUNT(*) as count FROM student_courses WHERE student_id = ?", 
            (self.id,)
        )
        result = cursor.fetchone()
        print(f"DEBUG: Anzahl Einträge in student_courses für ID {self.id}: {result['count']}")

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

    def add_course(self, db, course_id: int, semester_id: int) -> None:
        """Fügt eine Kurszuordnung für den Schüler hinzu."""
        if not self.id:
            raise ValueError("Schüler hat keine ID")
                
        db.execute(
            """INSERT INTO student_courses (student_id, course_id, semester_id)
            VALUES (?, ?, ?)""",
            (self.id, course_id, semester_id)
        )

    def remove_course(self, db, course_id: int, semester_id: int) -> None:
        """Entfernt eine Kurszuordnung."""
        if not self.id:
            raise ValueError("Schüler hat keine ID")
                
        db.execute(
            """DELETE FROM student_courses 
            WHERE student_id = ? AND course_id = ? AND semester_id = ?""",
            (self.id, course_id, semester_id)
        )

    def get_courses(self, db, semester_id: Optional[int] = None) -> list:
        """Holt alle Kurszuordnungen des Schülers, optional gefiltert nach Semester."""
        if not self.id:
            raise ValueError("Schüler hat keine ID")
                
        query = """
            SELECT c.*, sc.semester_id, sh.name as semester_name
            FROM student_courses sc
            JOIN courses c ON sc.course_id = c.id
            JOIN semester_history sh ON sc.semester_id = sh.id
            WHERE sc.student_id = ?
        """
        params = [self.id]
        
        if semester_id is not None:
            query += " AND sc.semester_id = ?"
            params.append(semester_id)
                
        query += " ORDER BY sh.start_date DESC, c.name"
                
        cursor = db.execute(query, tuple(params))
        return [dict(row) for row in cursor.fetchall()]

    def get_current_courses(self, db) -> list[dict]:
        """Holt alle aktuellen Kurse des Schülers im aktiven Halbjahr."""
        if not self.id:
            raise ValueError("Schüler hat keine ID")
        
        # Aktives Halbjahr aus den Einstellungen holen
        semester = db.semesters.get_current()
        if not semester:
            return []
            
        cursor = db.execute("""
            SELECT c.id, c.name, c.type, sh.id as semester_id
            FROM student_courses sc 
            JOIN courses c ON sc.course_id = c.id
            JOIN semester_history sh ON sc.semester_id = sh.id
            WHERE sc.student_id = ? 
            AND sh.start_date = ? 
            AND sh.end_date = ?
            ORDER BY c.name
            """, (self.id, semester['semester_start'], semester['semester_end']))
        
        return [dict(row) for row in cursor.fetchall()]

    def get_full_name(self) -> str:
        """Gibt den vollständigen Namen im Format 'Vorname Nachname' zurück."""
        return f"{self.first_name} {self.last_name}"

    def __str__(self) -> str:
        return self.get_full_name()

    def __repr__(self) -> str:
        return f"Student(id={self.id}, first_name='{self.first_name}', last_name='{self.last_name}')"