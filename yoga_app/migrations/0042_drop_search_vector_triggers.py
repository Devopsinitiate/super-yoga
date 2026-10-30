"""
Migration 0042: Drop the leftover search_vector triggers and functions.

Migration 0036 created PostgreSQL trigger functions/triggers that populate the
`search_vector` columns on Course/YogaPose/BreathingTechnique. Migration 0041
removed the columns and indexes but left the triggers in place, so every
INSERT/UPDATE failed with:

    psycopg2.errors.UndefinedColumn: record "new" has no field "search_vector"

This migration removes the triggers and their functions on PostgreSQL. It is a
no-op on other backends. The search_vector feature has been removed entirely;
search now relies on the SQL `icontains` fallback in SearchService.
"""
from django.db import migrations


_DROP_SQL = """
DROP TRIGGER IF EXISTS yoga_app_yogapose_search_vector_trigger ON yoga_app_yogapose;
DROP TRIGGER IF EXISTS yoga_app_breathing_search_vector_trigger ON yoga_app_breathingtechnique;
DROP TRIGGER IF EXISTS yoga_app_course_search_vector_trigger ON yoga_app_course;
DROP FUNCTION IF EXISTS yoga_app_yogapose_search_vector_update();
DROP FUNCTION IF EXISTS yoga_app_breathingtechnique_search_vector_update();
DROP FUNCTION IF EXISTS yoga_app_course_search_vector_update();
"""


class RunSQLPostgresOnly(migrations.RunSQL):
    """Runs SQL only on PostgreSQL; no-op elsewhere."""

    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        if schema_editor.connection.vendor != 'postgresql':
            return
        super().database_forwards(app_label, schema_editor, from_state, to_state)

    def database_backwards(self, app_label, schema_editor, from_state, to_state):
        if schema_editor.connection.vendor != 'postgresql':
            return
        super().database_backwards(app_label, schema_editor, from_state, to_state)


class Migration(migrations.Migration):

    dependencies = [
        ('yoga_app', '0041_remove_breathingtechnique_idx_breathing_search_vector_and_more'),
    ]

    operations = [
        RunSQLPostgresOnly(_DROP_SQL, reverse_sql=migrations.RunSQL.noop),
    ]
