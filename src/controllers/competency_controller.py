# src/controllers/competency_controller.py

"""
Controller für Kompetenz-Operationen.

Kapselt Business-Logik für Kompetenz-Verwaltung.
"""

from typing import Dict, Any, Optional, List
from .base_controller import BaseController


class CompetencyController(BaseController):
    """Controller für Kompetenz-Operationen."""
    
    def get_competency(self, competency_id: int) -> Optional[Dict[str, Any]]:
        """Holt eine Kompetenz anhand ihrer ID.
        
        Args:
            competency_id: ID der Kompetenz
            
        Returns:
            Dictionary mit Kompetenzdaten oder None
        """
        return self.competency_repo.get_by_id(competency_id)
    
    def get_all_competencies(self) -> List[Dict[str, Any]]:
        """Holt alle Kompetenzen aus der Datenbank.
        
        Returns:
            Liste von Dictionaries mit Kompetenzdaten
        """
        return self.competency_repo.get_all()
    
    def get_competencies_by_subject(self, subject: str) -> List[Dict[str, Any]]:
        """Holt alle Kompetenzen für ein bestimmtes Fach.
        
        Args:
            subject: Name des Fachs
            
        Returns:
            Liste von Dictionaries mit Kompetenzdaten
        """
        return self.competency_repo.get_by_subject(subject)
    
    def add_competency(self, subject: str, area: str, description: str) -> int:
        """Fügt eine neue Kompetenz hinzu.
        
        Args:
            subject: Fach
            area: Kompetenzbereich
            description: Beschreibung der Kompetenz
            
        Returns:
            ID der neu erstellten Kompetenz
        """
        return self.competency_repo.add(subject, area, description)
    
    def update_competency(self, competency_id: int, subject: str, area: str, description: str) -> None:
        """Aktualisiert eine Kompetenz.
        
        Args:
            competency_id: ID der Kompetenz
            subject: Neues Fach
            area: Neuer Kompetenzbereich
            description: Neue Beschreibung
        """
        self.competency_repo.update(competency_id, subject, area, description)
    
    def delete_competency(self, competency_id: int) -> None:
        """Löscht eine Kompetenz.
        
        Args:
            competency_id: ID der zu löschenden Kompetenz
        """
        self.competency_repo.delete(competency_id)
