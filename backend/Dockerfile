FROM python:3.9

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip

RUN pip install --no-cache-dir -r requirements.txt

RUN pip install gunicorn

COPY . .

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "foodgram_backend.wsgi:application"]