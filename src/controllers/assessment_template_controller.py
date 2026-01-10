# src/controllers/assessment_template_controller.py

"""
Controller für Bewertungstyp-Vorlagen-Operationen.

Kapselt Business-Logik für Bewertungstyp-Vorlagen-Verwaltung.
"""

from typing import Dict, Any, Optional, List
from .base_controller import BaseController


class AssessmentTemplateController(BaseController):
    """Controller für Bewertungstyp-Vorlagen-Operationen."""
    
    def get_template(self, template_id: int) -> Optional[Dict[str, Any]]:
        """Holt eine Vorlage anhand ihrer ID.
        
        Args:
            template_id: ID der Vorlage
            
        Returns:
            Dictionary mit Vorlagendaten oder None
        """
        return self.assessment_template_repo.get_by_id(template_id)
    
    def get_all_templates(self) -> List[Dict[str, Any]]:
        """Holt alle Vorlagen.
        
        Returns:
            Liste von Dictionaries mit Vorlagendaten
        """
        return self.assessment_template_repo.get_all()
    
    def get_templates_by_subject(self, subject: str) -> List[Dict[str, Any]]:
        """Holt alle Vorlagen für ein bestimmtes Fach.
        
        Args:
            subject: Name des Fachs
            
        Returns:
            Liste von Dictionaries mit Vorlagendaten
        """
        return self.assessment_template_repo.get_by_subject(subject)
    
    def add_template(self, name: str, subject: str, grading_system_id: int,
                    description: Optional[str] = None) -> int:
        """Fügt eine neue Vorlage hinzu.
        
        Args:
            name: Name der Vorlage
            subject: Fach
            grading_system_id: ID des Notensystems
            description: Optional, Beschreibung
            
        Returns:
            ID der neu erstellten Vorlage
        """
        return self.assessment_template_repo.add(name, subject, grading_system_id, description)
    
    def update_template(self, template_id: int, name: str, subject: str,
                       grading_system_id: int, description: Optional[str] = None) -> None:
        """Aktualisiert eine Vorlage.
        
        Args:
            template_id: ID der Vorlage
            name: Neuer Name
            subject: Neues Fach
            grading_system_id: Neue Notensystem-ID
            description: Optional, neue Beschreibung
        """
        self.assessment_template_repo.update(template_id, name, subject, grading_system_id, description)
    
    def delete_template(self, template_id: int) -> None:
        """Löscht eine Vorlage.
        
        Args:
            template_id: ID der zu löschenden Vorlage
        """
        self.assessment_template_repo.delete(template_id)
    
    def get_template_items(self, template_id: int) -> List[Dict[str, Any]]:
        """Holt alle Bewertungstypen einer Vorlage.
        
        Args:
            template_id: ID der Vorlage
            
        Returns:
            Liste von Dictionaries mit Item-Daten
        """
        return self.assessment_template_repo.get_items(template_id)
    
    def add_template_item(self, template_id: int, name: str,
                         parent_item_id: Optional[int] = None,
                         default_weight: float = 1.0) -> int:
        """Fügt einen Bewertungstyp zu einer Vorlage hinzu.
        
        Args:
            template_id: ID der Vorlage
            name: Name des Bewertungstyps
            parent_item_id: Optional, ID des übergeordneten Items
            default_weight: Standard-Gewichtung
            
        Returns:
            ID des neu erstellten Items
        """
        return self.assessment_template_repo.add_item(template_id, name, parent_item_id, default_weight)
    
    def update_template_item(self, item_id: int, name: str,
                            parent_item_id: Optional[int] = None,
                            default_weight: float = 1.0) -> None:
        """Aktualisiert ein Vorlagenelement.
        
        Args:
            item_id: ID des Items
            name: Neuer Name
            parent_item_id: Optional, neue Parent-ID
            default_weight: Neue Standard-Gewichtung
        """
        self.assessment_template_repo.update_item(item_id, name, parent_item_id, default_weight)
    
    def delete_template_item(self, item_id: int) -> None:
        """Löscht ein Vorlagenelement.
        
        Args:
            item_id: ID des zu löschenden Items
        """
        self.assessment_template_repo.delete_item(item_id)
