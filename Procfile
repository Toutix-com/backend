web: cd /var/app/current/app;source /var/app/venv/staging-LQM1lest/bin/activate;flask db upgrade;cd ../;gunicorn --bind :8000 --workers 3 --threads 2 app.__init__:app
