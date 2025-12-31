# src/database/repositories/competency_repository.py

from typing import List, Dict, Any, Optional
from .base_repository import BaseRepository


class CompetencyRepository(BaseRepository):
    """Repository für Kompetenz-Operationen."""
    
    def add(self, subject: str, area: str, description: str) -> int:
        """Fügt eine neue Kompetenz hinzu.
        
        Args:
            subject: Fach
            area: Kompetenzbereich
            description: Beschreibung der Kompetenz
            
        Returns:
            ID der neu erstellten Kompetenz
        """
        cursor = self.execute(
            "INSERT INTO competencies (subject, area, description) VALUES (?, ?, ?)",
            (subject, area, description)
        )
        return cursor.lastrowid
    
    def get_by_id(self, competency_id: int) -> Optional[Dict[str, Any]]:
        """Holt eine einzelne Kompetenz.
        
        Args:
            competency_id: ID der Kompetenz
            
        Returns:
            Dictionary mit Kompetenzdaten oder None
        """
        cursor = self.execute(
            "SELECT * FROM competencies WHERE id = ?",
            (competency_id,)
        )
        row = cursor.fetchone()
        return self._dict_from_row(row)
    
    def get_all(self) -> List[Dict[str, Any]]:
        """Holt alle Kompetenzen aus der Datenbank.
        
        Returns:
            Liste von Dictionaries mit Kompetenzdaten, sortiert nach Fach und Bereich
        """
        cursor = self.execute(
            "SELECT id, subject, area, description FROM competencies ORDER BY subject, area"
        )
        return self._dicts_from_rows(cursor.fetchall())
    
    def get_by_subject(self, subject: str) -> List[Dict[str, Any]]:
        """Holt alle Kompetenzen für ein bestimmtes Fach.
        
        Args:
            subject: Name des Faches
            
        Returns:
            Liste von Dictionaries mit Kompetenzdaten, sortiert nach Bereich
        """
        cursor = self.execute(
            "SELECT * FROM competencies WHERE subject = ? ORDER BY area",
            (subject,)
        )
        return self._dicts_from_rows(cursor.fetchall())
    
    def update(self, competency_id: int, subject: str, area: str, description: str) -> None:
        """Aktualisiert eine Kompetenz.
        
        Args:
            competency_id: ID der Kompetenz
            subject: Neues Fach
            area: Neuer Kompetenzbereich
            description: Neue Beschreibung
        """
        self.execute(
            """UPDATE competencies 
            SET subject = ?, area = ?, description = ? 
            WHERE id = ?""",
            (subject, area, description, competency_id)
        )
    
    def delete(self, competency_id: int) -> None:
        """Löscht eine Kompetenz.
        
        Löscht auch alle zugehörigen Verknüpfungen zu Unterrichtsstunden.
        
        Args:
            competency_id: ID der zu löschenden Kompetenz
        """
        # Zugehörige Zuordnungen löschen
        self.execute(
            "DELETE FROM lesson_competencies WHERE competency_id = ?",
            (competency_id,)
        )
        # Kompetenz selbst löschen
        self.execute(
            "DELETE FROM competencies WHERE id = ?",
            (competency_id,)
        )
