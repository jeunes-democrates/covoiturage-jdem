cd /d %~dp0
cd ..
doskey p = python manage.py $*
workon django-basic-project