from django.contrib import admin
from django.urls import path
import polls.views

urlpatterns = [
    path('', polls.views.my_polls),
    path('new/', polls.views.new_poll),
    path('poll/<poll_id>', polls.views.handle_poll),
    path('poll/<poll_id>/choice', polls.views.add_choice),
    path('poll/<poll_id>/user', polls.views.add_user_to_poll),
    path('poll/<poll_id>/vote', polls.views.vote),
]
