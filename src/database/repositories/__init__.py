# src/database/repositories/__init__.py

"""
Repository-Pattern Implementierung für Schulfreund.

Alle Repository-Klassen erben von BaseRepository und kapseln
die Datenbankzugriffe für spezifische Entitäten.
"""

from .base_repository import BaseRepository
from .student_repository import StudentRepository
from .course_repository import CourseRepository
from .lesson_repository import LessonRepository
from .competency_repository import CompetencyRepository
from .assessment_repository import AssessmentRepository
from .assessment_type_repository import AssessmentTypeRepository
from .assessment_template_repository import AssessmentTemplateRepository
from .grading_system_repository import GradingSystemRepository
from .semester_repository import SemesterRepository
from .holiday_repository import HolidayRepository
from .attendance_repository import AttendanceRepository
from .settings_repository import SettingsRepository

__all__ = [
    'BaseRepository',
    'StudentRepository',
    'CourseRepository',
    'LessonRepository',
    'CompetencyRepository',
    'AssessmentRepository',
    'AssessmentTypeRepository',
    'AssessmentTemplateRepository',
    'GradingSystemRepository',
    'SemesterRepository',
    'HolidayRepository',
    'AttendanceRepository',
    'SettingsRepository',
]
