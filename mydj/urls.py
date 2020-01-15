from django.contrib import admin
from django.urls import path, re_path, include
from .views import *
from django.contrib.auth import views as auth_views

urlpatterns = [
    re_path('^auth/', include(('django.contrib.auth.urls', "auth"))),
    path('auth/password_change_done/', auth_views.PasswordChangeDoneView.as_view(template_name='registration/password_change_done.html'), name='password_change_done'),
    re_path('^admin/', admin.site.urls),

    re_path('^(?:index|index\.html|\s*)$', index, name="index"),
    path('get_weibo_user', get_weibo_user),
]

