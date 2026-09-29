web: python manage.py collectstatic --noinput && python manage.py migrate --noinput && gunicorn erp_contabil.wsgi:application --bind 0.0.0.0:$PORT
