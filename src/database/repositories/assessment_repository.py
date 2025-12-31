# src/database/repositories/assessment_repository.py

from typing import List, Dict, Any, Optional
from .base_repository import BaseRepository


class AssessmentRepository(BaseRepository):
    """Repository für Bewertungs-/Noten-Operationen."""
    
    def add_or_update(self, data: dict) -> int:
        """Fügt eine neue Bewertung/Note hinzu oder aktualisiert eine bestehende.
        
        Args:
            data: Dictionary mit Bewertungsdaten:
                - student_id: ID des Schülers
                - course_id: ID des Kurses
                - assessment_type_id: ID des Bewertungstyps
                - lesson_id: Optional, ID der Stunde
                - grade: Note
                - date: Datum im Format "YYYY-MM-DD"
                - topic: Optional, Thema
                - comment: Optional, Kommentar
                - weight: Optional, Gewichtung (Standard: 1.0)
                
        Returns:
            ID der Bewertung
        """
        # Prüfe ob bereits eine Note existiert
        cursor = self.execute(
            """SELECT id FROM assessments 
            WHERE student_id = ? AND lesson_id = ?""",
            (data['student_id'], data.get('lesson_id'))
        )
        existing = cursor.fetchone()
        
        if existing:
            # Update existierende Note
            self.execute(
                """UPDATE assessments 
                SET grade = ?, assessment_type_id = ?, 
                    course_id = ?, date = ?, 
                    topic = ?, comment = ?, weight = ?
                WHERE student_id = ? AND lesson_id = ?""",
                (data['grade'], 
                 data['assessment_type_id'],
                 data['course_id'],
                 data['date'],
                 data.get('topic'),
                 data.get('comment'),
                 data.get('weight', 1.0),
                 data['student_id'],
                 data.get('lesson_id'))
            )
            return existing['id']
        else:
            # Füge neue Note hinzu
            cursor = self.execute(
                """INSERT INTO assessments 
                (student_id, course_id, assessment_type_id, grade,
                    date, lesson_id, topic, comment, weight)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (data['student_id'], 
                 data['course_id'],
                 data['assessment_type_id'], 
                 data['grade'],
                 data['date'],
                 data.get('lesson_id'),
                 data.get('topic'),
                 data.get('comment'),
                 data.get('weight', 1.0))
            )
            return cursor.lastrowid
    
    def delete(self, student_id: int, lesson_id: int) -> None:
        """Löscht eine Note für einen Schüler in einer bestimmten Stunde.
        
        Args:
            student_id: ID des Schülers
            lesson_id: ID der Stunde
        """
        self.execute(
            """DELETE FROM assessments 
            WHERE student_id = ? AND lesson_id = ?""",
            (student_id, lesson_id)
        )
    
    def get_by_student_and_course(self, student_id: int, course_id: int) -> List[Dict[str, Any]]:
        """Holt alle Noten eines Schülers in einem Kurs.
        
        Args:
            student_id: ID des Schülers
            course_id: ID des Kurses
            
        Returns:
            Liste von Dictionaries mit Notendaten, sortiert nach Datum (neueste zuerst)
        """
        cursor = self.execute(
            """SELECT a.*, t.name as type_name, t.weight as type_weight
               FROM assessments a
               JOIN assessment_types t ON a.assessment_type_id = t.id
               WHERE a.student_id = ? AND a.course_id = ?
               ORDER BY a.date DESC""",
            (student_id, course_id)
        )
        return self._dicts_from_rows(cursor.fetchall())
    
    def get_by_lesson(self, student_id: int, lesson_id: int) -> Optional[Dict[str, Any]]:
        """Holt die Note eines Schülers für eine bestimmte Stunde.
        
        Args:
            student_id: ID des Schülers
            lesson_id: ID der Stunde
            
        Returns:
            Dictionary mit Notendaten oder None
        """
        cursor = self.execute(
            """SELECT * FROM assessments 
            WHERE student_id = ? AND lesson_id = ?""",
            (student_id, lesson_id)
        )
        row = cursor.fetchone()
        return self._dict_from_row(row)
    
    def get_by_course(self, course_id: int, assessment_type_id: int = None) -> List[Dict[str, Any]]:
        """Holt alle Noten eines Kurses, optional gefiltert nach Bewertungstyp.
        
        Args:
            course_id: ID des Kurses
            assessment_type_id: Optional, ID des Bewertungstyps
            
        Returns:
            Liste von Dictionaries mit Notendaten
        """
        if assessment_type_id:
            cursor = self.execute(
                """SELECT a.*, s.first_name, s.last_name, t.name as type_name
                   FROM assessments a
                   JOIN students s ON a.student_id = s.id
                   JOIN assessment_types t ON a.assessment_type_id = t.id
                   WHERE a.course_id = ? AND a.assessment_type_id = ?
                   ORDER BY s.last_name, s.first_name, a.date DESC""",
                (course_id, assessment_type_id)
            )
        else:
            cursor = self.execute(
                """SELECT a.*, s.first_name, s.last_name, t.name as type_name
                   FROM assessments a
                   JOIN students s ON a.student_id = s.id
                   JOIN assessment_types t ON a.assessment_type_id = t.id
                   WHERE a.course_id = ?
                   ORDER BY s.last_name, s.first_name, t.name, a.date DESC""",
                (course_id,)
            )
        return self._dicts_from_rows(cursor.fetchall())
    
    def calculate_final_grade(self, student_id: int, course_id: int) -> Optional[float]:
        """Berechnet die Gesamtnote eines Schülers in einem Kurs.
        
        Args:
            student_id: ID des Schülers
            course_id: ID des Kurses
            
        Returns:
            Gewichtete Durchschnittsnote oder None wenn keine Noten vorhanden
        """
        # Prüfe ob der Schüler überhaupt Noten hat
        cursor = self.execute(
            """SELECT COUNT(*) as count 
            FROM assessments 
            WHERE student_id = ? AND course_id = ?""",
            (student_id, course_id)
        )
        if cursor.fetchone()['count'] == 0:
            return None
        
        # Hole alle Bewertungstypen und deren Gewichtungen
        from .assessment_type_repository import AssessmentTypeRepository
        type_repo = AssessmentTypeRepository(self.db)
        types = type_repo.get_by_course(course_id)
        if not types:
            return None
        
        # Berechne gewichtete Durchschnitte für jeden Typ
        def calculate_type_average(type_id):
            cursor = self.execute(
                """SELECT AVG(grade) as avg_grade
                   FROM assessments
                   WHERE student_id = ? AND course_id = ? 
                         AND assessment_type_id = ?""",
                (student_id, course_id, type_id)
            )
            result = cursor.fetchone()
            return result['avg_grade'] if result else None
        
        # Nur Root-Level Typen (ohne parent) für Endnote
        root_types = [t for t in types if not t.get('parent_type_id')]
        
        weighted_sum = 0
        weight_sum = 0
        
        for type_data in root_types:
            avg = calculate_type_average(type_data['id'])
            if avg is not None:
                weighted_sum += avg * type_data['weight']
                weight_sum += type_data['weight']
        
        return round(weighted_sum / weight_sum, 2) if weight_sum > 0 else None
    
    def get_student_course_grades(self, student_id: int) -> Dict[int, Dict[str, Any]]:
        """Holt die Gesamtnoten eines Schülers für alle seine Kurse.
        
        Args:
            student_id: ID des Schülers
            
        Returns:
            Dictionary mit Kurs-ID als Key und {'name': str, 'final_grade': float} als Value
        """
        # Hole alle Kurse des Schülers
        cursor = self.execute("""
            SELECT DISTINCT c.id, c.name
            FROM courses c
            JOIN student_courses sc ON c.id = sc.course_id
            WHERE sc.student_id = ?
            ORDER BY c.name
        """, (student_id,))
        
        courses = cursor.fetchall()
        
        # Berechne Noten für jeden Kurs
        course_grades = {}
        for course in courses:
            final_grade = self.calculate_final_grade(student_id, course['id'])
            if final_grade is not None:
                course_grades[course['id']] = {
                    'name': course['name'],
                    'final_grade': final_grade
                }
        
        return course_grades
    
    def get_by_assessment_type(self, student_id: int, course_id: int) -> List[Dict[str, Any]]:
        """Holt die Durchschnittsnoten pro Assessment Type für einen bestimmten Kurs.
        
        Args:
            student_id: ID des Schülers
            course_id: ID des Kurses
            
        Returns:
            Liste von Dictionaries mit Assessment Type Informationen und Noten
        """
        cursor = self.execute("""
            WITH RECURSIVE TypeHierarchy AS (
                -- Root types
                SELECT 
                    id, name, weight, parent_type_id,
                    name as path,
                    0 as level
                FROM assessment_types
                WHERE course_id = ? AND parent_type_id IS NULL
                
                UNION ALL
                
                -- Child types
                SELECT 
                    t.id, t.name, t.weight, t.parent_type_id,
                    th.path || ' > ' || t.name,
                    th.level + 1
                FROM assessment_types t
                JOIN TypeHierarchy th ON t.parent_type_id = th.id
            ),
            TypeGrades AS (
                SELECT 
                    th.*,
                    ROUND(AVG(a.grade * a.weight) / AVG(a.weight), 2) as average_grade,
                    COUNT(a.id) as grade_count
                FROM TypeHierarchy th
                LEFT JOIN assessments a ON th.id = a.assessment_type_id 
                    AND a.student_id = ?
                GROUP BY th.id
            )
            SELECT * FROM TypeGrades
            ORDER BY path
        """, (course_id, student_id))
        
        return self._dicts_from_rows(cursor.fetchall())
