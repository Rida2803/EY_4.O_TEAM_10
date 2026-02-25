import os, sys
sys.path.append(r'E:/cursor/student_budget_tracker')
os.environ.setdefault('DJANGO_SETTINGS_MODULE','student_budget_tracker.settings')
import django
django.setup()
from django.test import Client
from django.contrib.auth.models import User
c=Client()
# create test user if not exists
username='testuser'
pw='pass1234'
if not User.objects.filter(username=username).exists():
    User.objects.create_user(username=username,password=pw)
# login
logged_in = c.login(username=username,password=pw)
print('logged_in:', logged_in)
# GET logout
resp_get = c.get('/accounts/logout/')
print('GET /accounts/logout/ ->', resp_get.status_code)
# POST logout
resp_post = c.post('/accounts/logout/')
print('POST /accounts/logout/ ->', resp_post.status_code)
# After POST, check client logged in
print('client logged in after POST:', '_auth_user_id' in c.session)
