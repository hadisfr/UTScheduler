from django.contrib import admin

from .models import User, Poll, Choice, Vote, Comment

admin.site.register(User)
admin.site.register(Poll)
admin.site.register(Choice)
admin.site.register(Vote)
admin.site.register(Comment)
