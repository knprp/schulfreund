# src/controllers/subject_controller.py

"""
Controller für Fach-Operationen.

Kapselt Business-Logik für Fach-Verwaltung.
"""

from typing import Dict, Any, Optional, List
from .base_controller import BaseController


class SubjectController(BaseController):
    """Controller für Fach-Operationen."""
    
    def get_all_subjects(self) -> List[Dict[str, Any]]:
        """Holt alle Fächer mit Kursanzahl und Standardvorlage.
        
        Returns:
            Liste von Dictionaries mit Fachdaten
        """
        cursor = self.db.execute("""
            SELECT 
                s.name,
                COUNT(DISTINCT c.id) as course_count,
                att.name as template_name
            FROM subjects s
            LEFT JOIN courses c ON s.name = c.subject
            LEFT JOIN assessment_type_templates att ON (
                att.subject = s.name AND
                att.id = (
                    SELECT id FROM assessment_type_templates
                    WHERE subject = s.name
                    ORDER BY created_at DESC
                    LIMIT 1
                )
            )
            GROUP BY s.name
            ORDER BY s.name
        """)
        rows = cursor.fetchall()
        return [dict(row) for row in rows] if rows else []
    
    def add_subject(self, name: str) -> None:
        """Fügt ein neues Fach hinzu.
        
        Args:
            name: Name des Fachs
        """
        # Prüfe ob Fach bereits existiert
        cursor = self.db.execute(
            "SELECT name FROM subjects WHERE name = ?",
            (name.strip(),)
        )
        existing = cursor.fetchone()
        
        if existing:
            raise ValueError(f"Das Fach '{name}' existiert bereits!")
        
        # Füge neues Fach ein
        self.db.execute(
            "INSERT INTO subjects (name) VALUES (?)",
            (name.strip(),)
        )
    
    def delete_subject(self, name: str) -> None:
        """Löscht ein Fach.
        
        Args:
            name: Name des Fachs
            
        Raises:
            ValueError: Wenn das Fach noch verwendet wird
        """
        # Prüfe ob das Fach in Vorlagen verwendet wird
        cursor = self.db.execute(
            "SELECT COUNT(*) as count FROM assessment_type_templates WHERE subject = ?",
            (name,)
        )
        template_count = cursor.fetchone()['count']
        
        if template_count > 0:
            raise ValueError(
                f"Das Fach '{name}' wird noch von {template_count} Vorlage(n) "
                "verwendet und kann nicht gelöscht werden!"
            )
        
        # Prüfe ob das Fach in Kursen verwendet wird
        cursor = self.db.execute(
            "SELECT COUNT(*) as count FROM courses WHERE subject = ?",
            (name,)
        )
        course_count = cursor.fetchone()['count']
        
        if course_count > 0:
            raise ValueError(
                f"Das Fach '{name}' wird noch von {course_count} Kurs(en) "
                "verwendet und kann nicht gelöscht werden!"
            )
        
        # Lösche Fach
        self.db.execute(
            "DELETE FROM subjects WHERE name = ?",
            (name,)
        )
    
    def subject_exists(self, name: str) -> bool:
        """Prüft ob ein Fach existiert.
        
        Args:
            name: Name des Fachs
            
        Returns:
            True wenn das Fach existiert, sonst False
        """
        cursor = self.db.execute(
            "SELECT name FROM subjects WHERE name = ?",
            (name.strip(),)
        )
        return cursor.fetchone() is not None
