# src/database/repositories/assessment_template_repository.py

from typing import List, Dict, Any, Optional
from .base_repository import BaseRepository


class AssessmentTemplateRepository(BaseRepository):
    """Repository für Bewertungstyp-Vorlagen-Operationen."""
    
    def add(self, name: str, subject: str, 
           grading_system_id: int, description: str = None) -> int:
        """Fügt eine neue Bewertungstyp-Vorlage hinzu.
        
        Args:
            name: Name der Vorlage
            subject: Fach
            grading_system_id: ID des Notensystems
            description: Optional, Beschreibung
            
        Returns:
            ID der neu erstellten Vorlage
        """
        cursor = self.execute(
            """INSERT INTO assessment_type_templates 
               (name, subject, grading_system_id, description)
               VALUES (?, ?, ?, ?)""",
            (name, subject, grading_system_id, description)
        )
        return cursor.lastrowid
    
    def get_by_id(self, template_id: int) -> Optional[Dict[str, Any]]:
        """Holt eine einzelne Bewertungstyp-Vorlage.
        
        Args:
            template_id: ID der Vorlage
            
        Returns:
            Dictionary mit Vorlagendaten inkl. Notensystemname oder None
        """
        cursor = self.execute(
            """SELECT t.*, g.name as grading_system_name
            FROM assessment_type_templates t
            JOIN grading_systems g ON t.grading_system_id = g.id
            WHERE t.id = ?""",
            (template_id,)
        )
        row = cursor.fetchone()
        return self._dict_from_row(row)
    
    def get_all(self) -> List[Dict[str, Any]]:
        """Holt alle Bewertungsvorlagen mit zugehörigen Notensystemen.
        
        Returns:
            Liste von Dictionaries mit Vorlagendaten, sortiert nach Fach und Name
        """
        cursor = self.execute(
            """SELECT t.*, g.name as grading_system_name
            FROM assessment_type_templates t
            JOIN grading_systems g ON t.grading_system_id = g.id
            ORDER BY t.subject, t.name"""
        )
        return self._dicts_from_rows(cursor.fetchall())
    
    def get_by_subject(self, subject: str) -> List[Dict[str, Any]]:
        """Holt alle Vorlagen für ein bestimmtes Fach.
        
        Args:
            subject: Name des Faches
            
        Returns:
            Liste von Dictionaries mit Vorlagendaten inkl. Item-Anzahl
        """
        cursor = self.execute(
            """SELECT t.*, g.name as grading_system_name,
                      (SELECT COUNT(*) FROM template_items 
                       WHERE template_id = t.id) as item_count
               FROM assessment_type_templates t
               JOIN grading_systems g ON t.grading_system_id = g.id
               WHERE t.subject = ?
               ORDER BY t.name""",
            (subject,)
        )
        return self._dicts_from_rows(cursor.fetchall())
    
    def update(self, template_id: int, name: str, subject: str,
              grading_system_id: int, description: str = None) -> None:
        """Aktualisiert eine bestehende Vorlage.
        
        Args:
            template_id: ID der Vorlage
            name: Neuer Name
            subject: Neues Fach
            grading_system_id: Neue Notensystem-ID
            description: Optional, neue Beschreibung
        """
        self.execute(
            """UPDATE assessment_type_templates 
               SET name = ?, subject = ?, 
                   grading_system_id = ?, description = ?
               WHERE id = ?""",
            (name, subject, grading_system_id, description, template_id)
        )
    
    def delete(self, template_id: int) -> None:
        """Löscht eine Vorlage und alle ihre Items.
        
        Args:
            template_id: ID der zu löschenden Vorlage
        """
        # Zuerst die Template-Items löschen
        self.execute(
            "DELETE FROM template_items WHERE template_id = ?",
            (template_id,)
        )
        
        # Dann das Template selbst löschen
        self.execute(
            "DELETE FROM assessment_type_templates WHERE id = ?",
            (template_id,)
        )
    
    def add_item(self, template_id: int, name: str, 
                parent_item_id: int = None, default_weight: float = 1.0) -> int:
        """Fügt einen Bewertungstyp zu einer Vorlage hinzu.
        
        Args:
            template_id: ID der Vorlage
            name: Name des Bewertungstyps
            parent_item_id: Optional, ID des übergeordneten Items
            default_weight: Standard-Gewichtung
            
        Returns:
            ID des neu erstellten Items
        """
        cursor = self.execute(
            """INSERT INTO template_items 
               (template_id, name, parent_item_id, default_weight)
               VALUES (?, ?, ?, ?)""",
            (template_id, name, parent_item_id, default_weight)
        )
        return cursor.lastrowid
    
    def get_items(self, template_id: int) -> List[Dict[str, Any]]:
        """Holt alle Bewertungstypen einer Vorlage hierarchisch sortiert.
        
        Args:
            template_id: ID der Vorlage
            
        Returns:
            Liste von Dictionaries mit Item-Daten, hierarchisch sortiert
        """
        cursor = self.execute(
            """WITH RECURSIVE template_tree AS (
                -- Root items (ohne parent)
                SELECT id, name, parent_item_id, default_weight, 
                       0 as level, CAST(name as TEXT) as path
                FROM template_items
                WHERE template_id = ? AND parent_item_id IS NULL
                
                UNION ALL
                
                -- Child items
                SELECT i.id, i.name, i.parent_item_id, i.default_weight,
                       tt.level + 1, 
                       tt.path || '>' || i.name
                FROM template_items i
                JOIN template_tree tt ON i.parent_item_id = tt.id
            )
            SELECT * FROM template_tree
            ORDER BY path;""",
            (template_id,)
        )
        return self._dicts_from_rows(cursor.fetchall())
    
    def update_item(self, item_id: int, name: str, 
                   parent_item_id: int = None, 
                   default_weight: float = 1.0) -> None:
        """Aktualisiert ein Vorlagenelement.
        
        Args:
            item_id: ID des Items
            name: Neuer Name
            parent_item_id: Optional, neue Parent-ID
            default_weight: Neue Standard-Gewichtung
        """
        self.execute(
            """UPDATE template_items 
               SET name = ?, parent_item_id = ?, default_weight = ?
               WHERE id = ?""",
            (name, parent_item_id, default_weight, item_id)
        )
    
    def delete_item(self, item_id: int) -> None:
        """Löscht ein Vorlagenelement.
        
        Args:
            item_id: ID des zu löschenden Items
        """
        self.execute(
            "DELETE FROM template_items WHERE id = ?",
            (item_id,)
        )
