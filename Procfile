web: gunicorn instantlearn.wsgi --bind 0.0.0.0:$PORT
release: python manage.py collectstatic --noinput && python manage.py migrate
