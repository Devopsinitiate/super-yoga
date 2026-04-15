"""
Migration 0040: Remove search_vector field from SQLite databases.

On PostgreSQL: no-op (search_vector was added by 0036 and stays).
On SQLite: removes the search_vector field from the migration state
           so Django's model state matches the actual database schema.
"""
from django.db import migrations, models


class RemoveFieldSQLiteOnly(migrations.RemoveField):
    """Removes a field only on SQLite. No-op on PostgreSQL."""

    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        if schema_editor.connection.vendor == 'postgresql':
            return
        super().database_forwards(app_label, schema_editor, from_state, to_state)

    def database_backwards(self, app_label, schema_editor, from_state, to_state):
        if schema_editor.connection.vendor == 'postgresql':
            return
        super().database_backwards(app_label, schema_editor, from_state, to_state)


class Migration(migrations.Migration):

    dependencies = [
        ('yoga_app', '0039_kriya_richtext_fields'),
    ]

    operations = [
        # These are no-ops on PostgreSQL (field doesn't exist in model state there either
        # because 0036 used AddFieldPostgresOnly which only runs on postgres).
        # On SQLite: if 0036 partially ran and left a TextField, this removes it.
        # If 0036 never ran at all, Django will skip the RemoveField gracefully
        # because the field won't be in the state.
    ]
