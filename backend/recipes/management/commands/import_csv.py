import csv
from django.core.management.base import BaseCommand
from django.apps import apps


class Command(BaseCommand):
    help = 'Импорт данных из CSV файла в модель'

    def add_arguments(self, parser):
        parser.add_argument('path', type=str, help="Путь к CSV файлу")
        parser.add_argument('app_name', type=str, help="Имя приложения")
        parser.add_argument('model_name', type=str, help="Имя модели")

    def handle(self, *args, **options):
        model = apps.get_model(options['app_name'], options['model_name'])

        # Определить список доступных полей модели
        model_fields = {field.name for field in model._meta.fields}

        # Открыть и прочитать CSV файл
        with open(options['path'], newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            headers = ['name', 'measurement_unit']
            for row in reader:
                filtered_data = dict(zip(headers, row))
                # Фильтровать данные только по доступным полям модели
                filtered_data = {
                    key: value for key, value in filtered_data.items(
                    ) if key in model_fields}

                try:
                    # Создать объект модели
                    model.objects.create(**filtered_data)
                except Exception as e:
                    self.stderr.write(f'Ошибка при создании объекта: {e}')

        self.stdout.write(self.style.SUCCESS('Данные успешно импортированы!'))
