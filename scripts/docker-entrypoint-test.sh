#!/bin/sh
set -e

timestamp=$(date +"%d-%m-%Y_%H.%M-%Z")
filename="coverage-report(${timestamp}).txt"
directory="coverage_reports"


echo "Setting up test environment..."

echo "Waiting for db"
python manage.py wait_for_db

echo "Apply database migrations"
python manage.py makemigrations
python manage.py migrate

echo "Testing..."

if [ ! -d "$directory" ]; then
    mkdir "$directory"
    echo "Directory '$directory' created."
else
    echo "Directory '$directory' already exists."
fi

pytest --cov=. > $directory/$filename
echo "Coverage report saved to $directory/$filename"

echo "Lint"
flake8


