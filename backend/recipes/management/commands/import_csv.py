import csv
from django.core.management.base import BaseCommand
from django.shortcuts import get_object_or_404
from django.apps import apps
from django.db import connections

MODELS_FIELDS = {}


class Command(BaseCommand):
    help = 'Импорт данных из CSV файла в модель'

    def add_arguments(self, parser):
        parser.add_argument('path', type=str, help="Путь к CSV файлу")
        parser.add_argument('app_name', type=str, help="Имя приложения")
        parser.add_argument('model_name', type=str, help="Имя модели")

    def handle(self, *args, **options):
        file_path = options['path']
        app_name = options['app_name']
        model_name = options['model_name']
        model = apps.get_model(app_name, model_name)

        with connections['default'].cursor() as cursor:
            with open(file_path, newline='', encoding='utf-8') as csvfile:
                data_reader = csv.DictReader(csvfile)
                fieldnames = data_reader.fieldnames

                placeholders = ", ".join(["%s"] * len(fieldnames))
                columns = ", ".join(fieldnames)
                sql_query = f'''INSERT INTO {model._meta.db_table}
                  ({columns}) VALUES ({placeholders})'''

                data_to_insert = []
                for row in data_reader:
                    processed_row = [
                        (
                            get_object_or_404(
                                MODELS_FIELDS[field], pk=value
                            ) if field in MODELS_FIELDS else value)
                        for field, value in row.items()
                    ]
                    data_to_insert.append(processed_row)

                cursor.executemany(sql_query, data_to_insert)
