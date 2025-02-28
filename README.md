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

```sh
git add .
git commit -m "Cambios de prueba en test"
git push origin test


git checkout develop
git merge test
git push origin develop

git checkout master
git merge develop
git push origin master
```
