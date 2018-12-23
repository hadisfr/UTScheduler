from django.contrib import admin

from .models import User, Poll, Choice, Vote

admin.site.register(User)
admin.site.register(Poll)
admin.site.register(Choice)
admin.site.register(Vote)
