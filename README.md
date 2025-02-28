# school-assistance

```sh
pip install -r requirements.txt

python manage.py makemigrations

python manage.py migrate

python manage.py createsuperuser

```







```sh
>>> from django.contrib.auth.models import User 
>>> superuser = User.objects.get(username="admin")  
>>> superuser.set_password("admin5524") 
>>> superuser.save()
```