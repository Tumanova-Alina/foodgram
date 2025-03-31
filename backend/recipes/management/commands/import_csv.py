import csv
from django.core.management.base import BaseCommand
# from django.shortcuts import get_object_or_404
from django.apps import apps
# from django.db import connections

# MODELS_FIELDS = {}


class Command(BaseCommand):
    help = 'Импорт данных из CSV файла в модель'

    def add_arguments(self, parser):
        parser.add_argument('path', type=str, help="Путь к CSV файлу")
        parser.add_argument('app_name', type=str, help="Имя приложения")
        parser.add_argument('model_name', type=str, help="Имя модели")

    def handle(self, *args, **options):
        # file_path = options['path']
        # app_name = options['app_name']
        # model_name = options['model_name']
        # model = apps.get_model(app_name, model_name)

        # with connections['default'].cursor() as cursor:
        #     with open(file_path, newline='', encoding='utf-8') as csvfile:
        #         data_reader = csv.DictReader(csvfile)
        #         fieldnames = data_reader.fieldnames

        #         placeholders = ", ".join(["%s"] * len(fieldnames))
        #         columns = ", ".join(fieldnames)
        #         sql_query = f'''INSERT INTO {model._meta.db_table}
        #           ({columns}) VALUES ({placeholders})'''

        #         data_to_insert = []
        #         for row in data_reader:
        #             processed_row = [
        #                 (
        #                     get_object_or_404(
        #                         MODELS_FIELDS[field], pk=value
        #                     ) if field in MODELS_FIELDS else value)
        #                 for field, value in row.items()
        #             ]
        #             data_to_insert.append(processed_row)

        #         cursor.executemany(sql_query, data_to_insert)
        model = apps.get_model(options['app_name'], options['model_name'])

        # Определить список доступных полей модели
        model_fields = {field.name for field in model._meta.fields}

        # Открыть и прочитать CSV файл
        with open(options['path'], newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # Фильтровать данные только по доступным полям модели
                filtered_data = {
                    key: value for key, value in row.items(
                    ) if key in model_fields}

                try:
                    # Создать объект модели
                    model.objects.create(**filtered_data)
                except Exception as e:
                    self.stderr.write(f'Ошибка при создании объекта: {e}')

        self.stdout.write(self.style.SUCCESS('Данные успешно импортированы!'))
