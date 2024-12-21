# src/views/dialogs/__init__.py

from .student_dialog import StudentDialog
from .competency_dialog import CompetencyDialog
from .lesson_dialog import LessonDialog
from .delete_lesson_dialog import DeleteLessonDialog

__all__ = [
    'StudentDialog',
    'CompetencyDialog',
    'LessonDialog',
    'DeleteLessonDialog'
]