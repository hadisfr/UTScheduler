from django.urls import path
import polls.views

urlpatterns = [
    path('', polls.views.my_polls, name="all"),
    path('new/', polls.views.new_poll, name="new"),
    path('<int:poll_id>', polls.views.handle_poll, name="show"),
    path('<int:poll_id>/choice', polls.views.add_choice, name="choice"),
    path('<int:poll_id>/choice/<choice_id>/del', polls.views.delete_choice, name="delete_choice"),
    path('<int:poll_id>/user', polls.views.add_user_to_poll, name="user"),
    path('<int:poll_id>/user/<user_name>/del', polls.views.delete_user_from_poll, name="delete_user"),
    path('<int:poll_id>/vote', polls.views.vote, name="vote"),
    path('<int:poll_id>/done', polls.views.end_poll, name="done"),
    path('<int:poll_id>/reopen', polls.views.begin_poll, name="reopen"),
    path('<int:poll_id>/choice/<int:choice_id>/comments', polls.views.get_comments, name="comments"),
    path('<int:poll_id>/choice/<int:choice_id>/comment', polls.views.add_comment, name="add_comment"),
    path('<int:poll_id>/choice/<int:choice_id>/comment/<int:comment_id>/replies', polls.views.get_replies, name="replies"),
    path('<int:poll_id>/choice/<int:choice_id>/comment/<int:comment_id>/reply', polls.views.reply_to_comment, name="reply_to_comment"),
]
