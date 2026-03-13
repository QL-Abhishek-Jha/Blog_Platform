Blog API (Django + DRF)

This is a simple backend project made with Django REST Framework.

It has
JWT login (access token and refresh token)
User roles (user, author, admin)
Topics, blogs, comments
User can subscribe to authors
When author publishes a blog, notifications are created in database

How to run

1. Install packages
   pip install -r requirements.txt

2. Migrations
   python manage.py makemigrations users
   python manage.py makemigrations blogs
   python manage.py migrate

3. Create superuser
   python manage.py createsuperuser

4. Start server
   python manage.py runserver

Admin panel
http://127.0.0.1:8000/admin/

User app routes (not listing all endpoints)

Auth routes
register
login
token refresh
logout
change password
forgot password
reset password

Profile routes
me
public author profile

Subscription routes
subscribe author
unsubscribe author
my subscriptions

Blog app routes (not listing all endpoints)

Topic routes
list topics
create topic
topic detail
update topic
delete topic

Blog routes
public blog list
public blog detail
blogs by topic
blogs by author
author my blogs list
author create blog
author update blog
admin list blogs
admin delete blog
admin migrate blog topic

Notification routes
list notifications
mark notification read
