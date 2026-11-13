from django.core.management.base import BaseCommand, CommandError
from django.db import connection


class Command(BaseCommand):
    help = "Drop all application tables so the database can be migrated from scratch."

    def add_arguments(self, parser):
        parser.add_argument(
            "--no-input",
            action="store_true",
            help="Skip the confirmation prompt.",
        )

    def handle(self, *args, **options):
        if not options["no_input"]:
            confirmation = input(
                "This will delete all Django-managed tables and data. "
                "Type 'reset' to continue: "
            )
            if confirmation != "reset":
                raise CommandError("Database reset cancelled.")

        tables = connection.introspection.table_names()
        if connection.vendor == "postgresql":
            tables = [table for table in tables if table != "spatial_ref_sys"]
        quote_name = connection.ops.quote_name

        if not tables:
            self.stdout.write(self.style.SUCCESS("No Django-managed tables found."))
            return

        with connection.cursor() as cursor:
            if connection.vendor == "postgresql":
                quoted_tables = ", ".join(quote_name(table) for table in tables)
                cursor.execute(f"DROP TABLE {quoted_tables} CASCADE")
            else:
                for table in tables:
                    cursor.execute(f"DROP TABLE {quote_name(table)}")

        self.stdout.write(self.style.SUCCESS(f"Dropped {len(tables)} application tables."))
