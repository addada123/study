#!/bin/sh
echo "Setting up development environment..."

echo "Waiting for db"
python manage.py wait_for_db

echo "Apply database migrations"
python manage.py makemigrations
python manage.py migrate

# python manage.py populate_db

echo "Start development server"
python manage.py runserver 0.0.0.0:8000

