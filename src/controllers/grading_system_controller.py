# src/controllers/grading_system_controller.py

"""
Controller für Notensystem-Operationen.

Kapselt Business-Logik für Notensystem-Verwaltung.
"""

from typing import Dict, Any, Optional, List
from .base_controller import BaseController


class GradingSystemController(BaseController):
    """Controller für Notensystem-Operationen."""
    
    def get_grading_system(self, system_id: int) -> Optional[Dict[str, Any]]:
        """Holt ein Notensystem anhand seiner ID.
        
        Args:
            system_id: ID des Notensystems
            
        Returns:
            Dictionary mit Notensystemdaten oder None
        """
        return self.grading_system_repo.get_by_id(system_id)
    
    def get_all_grading_systems(self) -> List[Dict[str, Any]]:
        """Holt alle Notensysteme.
        
        Returns:
            Liste von Dictionaries mit Notensystemdaten
        """
        return self.grading_system_repo.get_all()
    
    def add_grading_system(self, name: str, min_grade: float, max_grade: float,
                          step_size: float, description: Optional[str] = None) -> int:
        """Fügt ein neues Notensystem hinzu.
        
        Args:
            name: Name des Notensystems
            min_grade: Minimale Note
            max_grade: Maximale Note
            step_size: Schrittweite (z.B. 0.33 für 1-6 mit + und -)
            description: Optional, Beschreibung
            
        Returns:
            ID des neu erstellten Notensystems
        """
        return self.grading_system_repo.add(name, min_grade, max_grade, step_size, description)
    
    def update_grading_system(self, system_id: int, name: str, min_grade: float,
                             max_grade: float, step_size: float,
                             description: Optional[str] = None) -> None:
        """Aktualisiert ein Notensystem.
        
        Args:
            system_id: ID des Notensystems
            name: Neuer Name
            min_grade: Neue minimale Note
            max_grade: Neue maximale Note
            step_size: Neue Schrittweite
            description: Optional, neue Beschreibung
        """
        self.grading_system_repo.update(system_id, name, min_grade, max_grade, step_size, description)
    
    def delete_grading_system(self, system_id: int) -> None:
        """Löscht ein Notensystem.
        
        Args:
            system_id: ID des zu löschenden Notensystems
        """
        self.grading_system_repo.delete(system_id)
    
    def get_grading_system_for_course(self, course_id: int) -> Optional[Dict[str, Any]]:
        """Holt das Notensystem für einen Kurs.
        
        Args:
            course_id: ID des Kurses
            
        Returns:
            Dictionary mit Notensystemdaten oder None
        """
        return self.grading_system_repo.get_by_course(course_id)
