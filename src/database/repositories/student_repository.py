# src/database/repositories/student_repository.py

from typing import List, Dict, Any, Optional
from .base_repository import BaseRepository


class StudentRepository(BaseRepository):
    """Repository für Schüler-Operationen."""
    
    def add(self, first_name: str, last_name: str) -> int:
        """Fügt einen neuen Schüler hinzu.
        
        Args:
            first_name: Vorname des Schülers
            last_name: Nachname des Schülers
            
        Returns:
            ID des neu erstellten Schülers
        """
        cursor = self.execute(
            "INSERT INTO students (first_name, last_name) VALUES (?, ?)",
            (first_name.strip(), last_name.strip())
        )
        return cursor.lastrowid
    
    def get_by_id(self, student_id: int) -> Optional[Dict[str, Any]]:
        """Holt einen Schüler anhand seiner ID.
        
        Args:
            student_id: ID des Schülers
            
        Returns:
            Dictionary mit Schülerdaten oder None
        """
        cursor = self.execute(
            "SELECT * FROM students WHERE id = ?",
            (student_id,)
        )
        row = cursor.fetchone()
        return self._dict_from_row(row)
    
    def get_all(self) -> List[Dict[str, Any]]:
        """Holt alle Schüler aus der Datenbank.
        
        Returns:
            Liste von Dictionaries mit Schülerdaten, sortiert nach Nachname
        """
        cursor = self.execute(
            "SELECT id, first_name, last_name FROM students ORDER BY last_name, first_name"
        )
        return self._dicts_from_rows(cursor.fetchall())
    
    def update(self, student_id: int, first_name: str, last_name: str) -> None:
        """Aktualisiert die Daten eines Schülers.
        
        Args:
            student_id: ID des Schülers
            first_name: Neuer Vorname
            last_name: Neuer Nachname
        """
        self.execute(
            "UPDATE students SET first_name = ?, last_name = ? WHERE id = ?",
            (first_name.strip(), last_name.strip(), student_id)
        )
    
    def delete(self, student_id: int) -> None:
        """Löscht einen Schüler aus der Datenbank.
        
        Args:
            student_id: ID des zu löschenden Schülers
        """
        self.execute(
            "DELETE FROM students WHERE id = ?",
            (student_id,)
        )
    
    def get_by_course(self, course_id: int, semester_id: int) -> List[Dict[str, Any]]:
        """Holt alle Schüler eines Kurses in einem bestimmten Semester.
        
        Args:
            course_id: ID des Kurses
            semester_id: ID des Semesters
            
        Returns:
            Liste von Dictionaries mit Schülerdaten
        """
        query = """
            SELECT
                s.id,
                s.first_name,
                s.last_name
            FROM students s
            JOIN student_courses sc ON s.id = sc.student_id
            WHERE sc.course_id = ?
            AND sc.semester_id = ?
            ORDER BY s.last_name, s.first_name
        """
        cursor = self.execute(query, (course_id, semester_id))
        return self._dicts_from_rows(cursor.fetchall())
    
    def add_to_course(self, student_id: int, course_id: int, semester_id: int) -> None:
        """Fügt einen Schüler zu einem Kurs hinzu.
        
        Args:
            student_id: ID des Schülers
            course_id: ID des Kurses
            semester_id: ID des Semesters
        """
        self.execute(
            """INSERT INTO student_courses (student_id, course_id, semester_id)
               VALUES (?, ?, ?)""",
            (student_id, course_id, semester_id)
        )
    
    def remove_from_course(self, student_id: int, course_id: int, semester_id: int) -> None:
        """Entfernt einen Schüler aus einem Kurs.
        
        Args:
            student_id: ID des Schülers
            course_id: ID des Kurses
            semester_id: ID des Semesters
        """
        self.execute(
            """DELETE FROM student_courses 
               WHERE student_id = ? AND course_id = ? AND semester_id = ?""",
            (student_id, course_id, semester_id)
        )
    
    def get_courses(self, student_id: int, semester_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Holt alle Kurse eines Schülers.
        
        Args:
            student_id: ID des Schülers
            semester_id: Optional, ID des Semesters zum Filtern
            
        Returns:
            Liste von Dictionaries mit Kursdaten
        """
        query = """
            SELECT c.*, sc.semester_id, sh.name as semester_name
            FROM student_courses sc
            JOIN courses c ON sc.course_id = c.id
            JOIN semester_history sh ON sc.semester_id = sh.id
            WHERE sc.student_id = ?
        """
        params = [student_id]
        
        if semester_id is not None:
            query += " AND sc.semester_id = ?"
            params.append(semester_id)
        
        query += " ORDER BY sh.start_date DESC, c.name"
        
        cursor = self.execute(query, tuple(params))
        return self._dicts_from_rows(cursor.fetchall())
