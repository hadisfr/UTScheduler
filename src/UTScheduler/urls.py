"""UTScheduler URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
import polls.views

urlpatterns = [
    path('', polls.views.landing, name="landing"),
    path('poll/', include(('polls.urls', 'polls'), namespace="poll")),
    path('login/', polls.views.login, name="login"),
    path('validate/<username>', polls.views.validate_email, name="validate_email"),
    path('signup/', polls.views.signup, name="signup"),
    path('logout/', polls.views.logout, name="logout"),
    path('admin/', admin.site.urls),
]
