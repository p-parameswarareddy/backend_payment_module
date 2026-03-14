import os
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Apply schema.sql to the database"

    def handle(self, *args, **options):
        # manage.py lives at BASE_DIR, so use that directly
        base_dir = os.path.dirname(os.path.abspath('manage.py'))
        schema_path = os.path.join(base_dir, 'schema.sql')

        if not os.path.exists(schema_path):
            self.stderr.write(self.style.ERROR(f"schema.sql not found at: {schema_path}"))
            return

        self.stdout.write(f"Reading schema from: {schema_path}")

        with open(schema_path, 'r') as f:
            sql = f.read()

        with connection.cursor() as cursor:
            cursor.execute(sql)

        self.stdout.write(self.style.SUCCESS("Schema applied successfully!"))