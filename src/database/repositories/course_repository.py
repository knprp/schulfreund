# src/database/repositories/course_repository.py

from typing import List, Dict, Any, Optional
from .base_repository import BaseRepository


class CourseRepository(BaseRepository):
    """Repository für Kurs-Operationen."""
    
    def add(self, name: str, type: str = "course", subject: Optional[str] = None,
            description: Optional[str] = None, color: Optional[str] = None,
            template_id: Optional[int] = None) -> int:
        """Fügt einen neuen Kurs hinzu.
        
        Args:
            name: Name des Kurses
            type: Typ ('class' oder 'course')
            subject: Optional, Fach
            description: Optional, Beschreibung
            color: Optional, Farbe (Hex-Code)
            template_id: Optional, ID der Bewertungstyp-Vorlage
            
        Returns:
            ID des neu erstellten Kurses
        """
        cursor = self.execute(
            """INSERT INTO courses (name, type, subject, description, color, template_id) 
               VALUES (?, ?, ?, ?, ?, ?)""",
            (name.strip(), type, subject, description, color, template_id)
        )
        return cursor.lastrowid
    
    def get_by_id(self, course_id: int) -> Optional[Dict[str, Any]]:
        """Holt einen Kurs anhand seiner ID.
        
        Args:
            course_id: ID des Kurses
            
        Returns:
            Dictionary mit Kursdaten oder None
        """
        cursor = self.execute(
            "SELECT * FROM courses WHERE id = ?",
            (course_id,)
        )
        row = cursor.fetchone()
        return self._dict_from_row(row)
    
    def get_all(self) -> List[Dict[str, Any]]:
        """Holt alle Kurse aus der Datenbank.
        
        Returns:
            Liste von Dictionaries mit Kursdaten, sortiert nach Name
        """
        cursor = self.execute(
            "SELECT id, name, type, subject FROM courses ORDER BY name"
        )
        return self._dicts_from_rows(cursor.fetchall())
    
    def update(self, course_id: int, name: str, type: str = None,
              subject: Optional[str] = None, description: Optional[str] = None,
              color: Optional[str] = None, template_id: Optional[int] = None) -> None:
        """Aktualisiert die Daten eines Kurses.
        
        Args:
            course_id: ID des Kurses
            name: Neuer Name
            type: Optional, neuer Typ
            subject: Optional, neues Fach
            description: Optional, neue Beschreibung
            color: Optional, neue Farbe
            template_id: Optional, neue Template-ID
        """
        # Baue UPDATE-Query dynamisch auf
        updates = ["name = ?"]
        params = [name.strip()]
        
        if type is not None:
            updates.append("type = ?")
            params.append(type)
        if subject is not None:
            updates.append("subject = ?")
            params.append(subject)
        if description is not None:
            updates.append("description = ?")
            params.append(description)
        if color is not None:
            updates.append("color = ?")
            params.append(color)
        if template_id is not None:
            updates.append("template_id = ?")
            params.append(template_id)
        
        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(course_id)
        
        query = f"UPDATE courses SET {', '.join(updates)} WHERE id = ?"
        self.execute(query, tuple(params))
    
    def delete(self, course_id: int) -> None:
        """Löscht einen Kurs aus der Datenbank.
        
        Args:
            course_id: ID des zu löschenden Kurses
        """
        self.execute(
            "DELETE FROM courses WHERE id = ?",
            (course_id,)
        )
    
    def get_by_semester(self, semester_id: int) -> List[Dict[str, Any]]:
        """Holt alle Kurse eines bestimmten Semesters.
        
        Args:
            semester_id: ID des Semesters
            
        Returns:
            Liste von Dictionaries mit Kursdaten inkl. Schüleranzahl
        """
        query = """
            SELECT 
                c.*,
                COUNT(DISTINCT sc.student_id) as student_count
            FROM courses c
            LEFT JOIN student_courses sc ON c.id = sc.course_id AND sc.semester_id = ?
            GROUP BY c.id
            ORDER BY c.name
        """
        cursor = self.execute(query, (semester_id,))
        return self._dicts_from_rows(cursor.fetchall())
