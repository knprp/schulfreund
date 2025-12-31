# src/database/repositories/base_repository.py

from typing import Optional, List, Dict, Any
from abc import ABC


class BaseRepository(ABC):
    """Basis-Klasse für alle Repository-Klassen.
    
    Stellt gemeinsame Funktionalität bereit und definiert die Schnittstelle
    zur Datenbank über den DatabaseManager.
    """
    
    def __init__(self, db_manager):
        """Initialisiert das Repository mit einem DatabaseManager.
        
        Args:
            db_manager: Instanz von DatabaseManager für Datenbankzugriffe
        """
        self.db = db_manager
    
    def execute(self, query: str, params: tuple = None):
        """Führt eine SQL-Query aus.
        
        Delegiert an den DatabaseManager.
        
        Args:
            query: SQL-Query-String
            params: Optional tuple mit Parametern für die Query
            
        Returns:
            Cursor-Objekt mit den Ergebnissen
        """
        return self.db.execute(query, params)
    
    def _dict_from_row(self, row) -> Optional[Dict[str, Any]]:
        """Konvertiert eine Datenbank-Zeile in ein Dictionary.
        
        Args:
            row: sqlite3.Row oder None
            
        Returns:
            Dictionary mit den Daten oder None
        """
        if row is None:
            return None
        return dict(row)
    
    def _dicts_from_rows(self, rows) -> List[Dict[str, Any]]:
        """Konvertiert mehrere Datenbank-Zeilen in eine Liste von Dictionaries.
        
        Args:
            rows: Liste von sqlite3.Row-Objekten
            
        Returns:
            Liste von Dictionaries
        """
        return [dict(row) for row in rows] if rows else []
