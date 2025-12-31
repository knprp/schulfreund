# src/database/repositories/assessment_type_repository.py

from typing import List, Dict, Any
from .base_repository import BaseRepository


class AssessmentTypeRepository(BaseRepository):
    """Repository für Bewertungstyp-Operationen."""
    
    def add(self, course_id: int, name: str, 
           parent_type_id: int = None, weight: float = 1.0) -> int:
        """Fügt einen neuen Bewertungstyp hinzu.
        
        Args:
            course_id: ID des Kurses
            name: Name des Bewertungstyps
            parent_type_id: Optional, ID des übergeordneten Typs
            weight: Gewichtung (Standard: 1.0)
            
        Returns:
            ID des neu erstellten Bewertungstyps
        """
        cursor = self.execute(
            """INSERT INTO assessment_types 
               (course_id, name, parent_type_id, weight)
               VALUES (?, ?, ?, ?)""",
            (course_id, name, parent_type_id, weight)
        )
        return cursor.lastrowid
    
    def get_by_course(self, course_id: int) -> List[Dict[str, Any]]:
        """Holt alle Bewertungstypen eines Kurses hierarchisch sortiert.
        
        Args:
            course_id: ID des Kurses
            
        Returns:
            Liste von Dictionaries mit Bewertungstypdaten, hierarchisch sortiert
        """
        cursor = self.execute(
            """WITH RECURSIVE type_tree AS (
                -- Root types (ohne parent)
                SELECT id, name, parent_type_id, weight, 
                       0 as level, CAST(name as TEXT) as path
                FROM assessment_types
                WHERE course_id = ? AND parent_type_id IS NULL
                
                UNION ALL
                
                -- Child types
                SELECT t.id, t.name, t.parent_type_id, t.weight,
                       tt.level + 1, 
                       tt.path || '>' || t.name
                FROM assessment_types t
                JOIN type_tree tt ON t.parent_type_id = tt.id
            )
            SELECT * FROM type_tree
            ORDER BY path;""",
            (course_id,)
        )
        return self._dicts_from_rows(cursor.fetchall())
    
    def delete(self, type_id: int) -> None:
        """Löscht einen Bewertungstyp und alle zugehörigen Untertypen.
        
        Prüft ob der Typ bereits für Bewertungen verwendet wurde.
        
        Args:
            type_id: ID des zu löschenden Bewertungstyps
            
        Raises:
            ValueError: Wenn der Typ bereits für Bewertungen verwendet wurde
        """
        # Prüfe ob der Typ bereits für Bewertungen verwendet wurde
        cursor = self.execute(
            "SELECT COUNT(*) as count FROM assessments WHERE assessment_type_id = ?",
            (type_id,)
        )
        result = cursor.fetchone()
        if result['count'] > 0:
            raise ValueError(
                "Dieser Bewertungstyp wurde bereits für Noten verwendet und "
                "kann nicht gelöscht werden."
            )
        
        # Lösche rekursiv alle untergeordneten Typen
        # Dies funktioniert dank ON DELETE CASCADE in der Datenbank
        self.execute(
            "DELETE FROM assessment_types WHERE id = ?",
            (type_id,)
        )
    
    def create_from_template(self, course_id: int, template_id: int) -> None:
        """Erstellt Bewertungstypen für einen Kurs basierend auf einer Vorlage.
        
        Args:
            course_id: ID des Kurses
            template_id: ID der Bewertungstyp-Vorlage
            
        Raises:
            ValueError: Wenn die Vorlage keine Bewertungstypen enthält
        """
        from .assessment_template_repository import AssessmentTemplateRepository
        template_repo = AssessmentTemplateRepository(self.db)
        template_items = template_repo.get_items(template_id)
        
        if not template_items:
            raise ValueError("Die ausgewählte Vorlage enthält noch keine Bewertungstypen.")
        
        # Dictionary zum Speichern der ID-Zuordnungen
        id_mapping = {}
        
        # Items der Reihe nach einfügen (sind bereits hierarchisch sortiert)
        for item in template_items:
            # Wenn es ein Parent-Item gibt, nutze die gemappte ID
            parent_id = None
            if item.get('parent_item_id'):
                parent_id = id_mapping.get(item['parent_item_id'])
            
            # Füge neuen Assessment Type hinzu
            new_id = self.add(
                course_id=course_id,
                name=item['name'],
                parent_type_id=parent_id,
                weight=item.get('default_weight', 1.0)
            )
            
            # Speichere ID-Zuordnung
            id_mapping[item['id']] = new_id
