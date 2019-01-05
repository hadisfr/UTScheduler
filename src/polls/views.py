from django.shortcuts import render, Http404, redirect, reverse
from django.core.exceptions import ObjectDoesNotExist
from django.db.utils import IntegrityError
from django.utils.timezone import now
from django.contrib import messages
from datetime import datetime

from .models import User, Poll, Choice, Vote, TextChoice, TimedChoice, RecurringChoice, Comment
from .mail.mail import Mail
from .mail.notifier import Notifier


# todo: should refactor or combine with involvement
def needs_involvement_or_ownership(func):
    def involvement_or_ownership_checked_func(req, poll_id, *args, **kwargs):
        try:
            poll = Poll.objects.get(id=poll_id)
        except ObjectDoesNotExist:
            raise Http404
        if poll and (poll.audience.filter(name=req.puser.name).exists() or poll.owner == req.puser):
            return func(req, poll, *args, **kwargs)
        else:
            raise Http404

    return involvement_or_ownership_checked_func

def needs_involvement(func):
    def involvement_checked_func(req, poll_id, *args, **kwargs):
        try:
            poll = Poll.objects.get(id=poll_id)
        except ObjectDoesNotExist:
            raise Http404
        if poll and poll.audience.filter(name=req.puser.name).exists():
            return func(req, poll, *args, **kwargs)
        else:
            raise Http404

    return involvement_checked_func


def needs_ownership(func):
    def ownership_checked_func(req, poll_id, *args, **kwargs):
        try:
            poll = Poll.objects.get(id=poll_id)
        except ObjectDoesNotExist:
            raise Http404
        if poll and poll.owner == req.puser:
            return func(req, poll, *args, **kwargs)
        else:
            raise Http404

    return ownership_checked_func


def is_poll_closed(poll):
    return poll.close_date and poll.close_date < now()


def only_open_polls(func):
    def opennes_checkec_function(req, poll, *args, **kwargs):
        if not is_poll_closed:
            raise Http404
        else:
            return func(req, poll, *args, **kwargs)

    return opennes_checkec_function


def landing(req):
    return redirect(reverse('poll:all'))


def my_polls(req):
    owned_polls = Poll.objects.filter(owner=req.puser)
    involved_polls = Poll.objects.filter(audience=req.puser)
    return render(req, "polls/my_polls.html", {"owned_polls": owned_polls, "involved_polls": involved_polls})


def login(req):
    if req.method == 'GET':
        return render(req, "login.html")
    elif req.method == 'POST':
        try:
            user = User.objects.get(name=req.POST['username'])
            req.session['username'] = user.name
            return redirect(reverse('landing'))
        except (ObjectDoesNotExist, ValueError, KeyError):
            messages.add_message(req, messages.ERROR, "Wrong authentication data!")
            return render(req, "login.html", status=401)
    else:
        raise Http404


def signup(req):
    if req.method == 'GET':
        return render(req, "signup.html")
    elif req.method == 'POST':
        try:
            User.objects.create(name=req.POST['username'], email=req.POST['email'])
            messages.add_message(req, messages.SUCCESS, "User created successfully!")
            return redirect(reverse('landing'))
        except (IntegrityError, ValueError, KeyError):
            messages.add_message(req, messages.ERROR, "Duplicate username!")
            return redirect(reverse('signup'))
    else:
        raise Http404


def logout(req):
    req.session['username'] = None
    return redirect(reverse('landing'))


def new_poll(req):
    try:
        if req.method == 'GET':
            return render(req, "polls/new_poll.html", {'types': Poll.POLL_T})
        elif req.method == 'POST':
            poll = Poll.objects.create(question_text=req.POST['question'], owner=req.puser, poll_type=req.POST['type'])
            messages.add_message(req, messages.SUCCESS, "Poll created successfully!")
            return redirect(reverse('poll:show', kwargs={'poll_id': poll.id}))
        else:
            raise Http404
    except ObjectDoesNotExist:
        raise Http404


@needs_ownership
def handle_poll_for_owner(req, poll):
    return render(req, "polls/poll_details.html", {
        "poll": poll,
        "choices": [{"choice": choice, "votes": [
            {"text": opt[1], "num": Vote.objects.filter(choice=choice, vote=opt[0]).count()}
            for opt in Vote.VOTE_T
        ]} for choice in Choice.objects.filter(poll=poll)],
        "involved_users": User.objects.filter(poll=poll),
        "users": User.objects.exclude(poll=poll).exclude(owner=poll),
        "closed": is_poll_closed(poll),
        "chosen": poll.chosen_choice if is_poll_closed(poll) else "",
        "weekdays": RecurringChoice.WEEKDAYS
    })


@needs_involvement
def handle_poll_for_audience(req, poll):
    def get_first_vote(l):
        return l[0].get_vote_display() if len(l) else None

    return render(req, "polls/poll_vote.html", {
        "poll": poll,
        "choices": [{'choice': choice, 'vote': get_first_vote(Vote.objects.filter(voter=req.puser, choice=choice))}
                    for choice in Choice.objects.filter(poll=poll)],
        "possible_votes": [vote[1] for vote in Vote.VOTE_T],
        "closed": is_poll_closed(poll),
        "chosen": poll.chosen_choice.content if is_poll_closed(poll) else ""
    })


def handle_poll(req, poll_id):
    try:
        return handle_poll_for_owner(req, poll_id)
    except Http404:
        return handle_poll_for_audience(req, poll_id)


@needs_ownership
@only_open_polls
def add_choice(req, poll):
    if req.method == 'POST':
        status = messages.SUCCESS
        status_msg = "Choice created successfully!"
        if poll.poll_type == Poll.POLL_T_TEXTUAL:
            TextChoice.objects.create(poll=poll, content=req.POST['text'])
        elif poll.poll_type == Poll.POLL_T_TIMED:
            try:
                start_datetime = datetime.strptime(req.POST['start-date'] + ' ' + req.POST['start-time'],
                    '%Y-%m-%d %H:%M')
                end_datetime = datetime.strptime(req.POST['start-date'] + ' ' + req.POST['end-time'],
                    '%Y-%m-%d %H:%M')
                if start_datetime >= end_datetime:
                    raise Exception
                TimedChoice.objects.create(poll=poll, start_date=start_datetime, end_date=end_datetime)
            except Exception as e:
                status = messages.ERROR
                status_msg = "Wrong datetime format!"
        elif poll.poll_type == Poll.POLL_T_RECURRING:
            try:
                start_time = datetime.strptime(req.POST['start-time'], '%H:%M').time()
                end_time = datetime.strptime(req.POST['end-time'], '%H:%M').time()
                weekday = int(req.POST['weekday'])
                if start_time >= end_time or weekday < 0 or weekday > 6:
                    raise Exception
                RecurringChoice.objects.create(poll=poll, weekday=weekday, start_time=start_time, end_time=end_time)
            except Exception as e:
                status = messages.ERROR
                status_msg = "Wrong time format!"

        messages.add_message(req, status, status_msg)
        return redirect(reverse('poll:show', kwargs={'poll_id': poll.id}))
    else:
        raise Http404


@needs_ownership
@only_open_polls
def add_user_to_poll(req, poll):
    if req.method == 'POST':
        try:
            this_audience = User.objects.get(name=req.POST['username'])
        except (ObjectDoesNotExist, ValueError, KeyError):
            raise Http404
        poll.audience.add(this_audience)
        Notifier(Mail()).notify_participate(
            req.puser,
            this_audience,
            req.build_absolute_uri(reverse('poll:show', kwargs={'poll_id': poll.id}))
        )
        messages.add_message(req, messages.SUCCESS, "User added successfully!")
        return redirect(reverse('poll:show', kwargs={'poll_id': poll.id}))
    else:
        raise Http404


@needs_involvement
@only_open_polls
def vote(req, poll):
    choice_prefix = 'vote_'
    if req.method == 'POST':
        status = messages.SUCCESS
        status_msg = "Voted successfully!"
        for idx, key in enumerate(req.POST):
            if key.startswith(choice_prefix):
                try:
                    choice = Choice.objects.get(id=key[len(choice_prefix):])
                except (ObjectDoesNotExist, ValueError, KeyError):
                    raise Http404
                if choice.poll != poll:
                    raise Http404
                Vote.objects.update_or_create(
                    voter=req.puser,
                    choice=choice,
                    defaults={'vote': {key: value for (value, key) in Vote.VOTE_T}[req.POST[key]]},
                )
                if {key: value for (value, key) in Vote.VOTE_T}[req.POST[key]] == 1:
                    other_votes = Vote.objects.filter(voter=req.puser, vote=1)
                    for other_vote in other_votes:
                        choice_overlap = False
                        if other_vote.choice == choice:
                            continue
                        if poll.poll_type == Poll.POLL_T_TIMED:
                            if other_vote.choice.poll.poll_type == Poll.POLL_T_TIMED:
                                if choice.timedchoice.overlaps(other_vote.choice.timedchoice):
                                    choice_overlap = True
                            else:
                                choice_overlap = True
                        elif poll.poll_type == Poll.POLL_T_RECURRING:
                            if other_vote.choice.poll.poll_type == Poll.POLL_T_TIMED:
                                choice_overlap = True
                            else:
                                choice_overlap = True
                        if choice_overlap:
                            if status == messages.SUCCESS:
                                status_msg = ""
                            status = messages.WARNING
                            status_msg += ' Choice ' + str(idx + 1) + ' clashes with \"' + str(other_vote.choice) + '\" from vote \"' + str(other_vote.choice.poll) + '\".'
        messages.add_message(req, status, status_msg)
        return redirect(reverse('poll:show', kwargs={'poll_id': poll.id}))
    else:
        raise Http404


@needs_ownership
@only_open_polls
def end_poll(req, poll):
    if req.method == 'POST':
        try:
            poll.chosen_choice = Choice.objects.get(id=req.POST['choice'])
        except (ObjectDoesNotExist, ValueError, KeyError):
            raise Http404
        poll.close_date = now()
        poll.save()
        messages.add_message(req, messages.SUCCESS, "Poll closed successfully!")
        return redirect(reverse('poll:show', kwargs={'poll_id': poll.id}))
    else:
        raise Http404


@needs_ownership
def begin_poll(req, poll):
    if req.method == 'POST':
        poll.chosen_choice = None
        poll.close_date = None
        poll.save()
        for user in poll.audience.all():
            Notifier(Mail()).notify_participate(
                req.puser,
                user,
                req.build_absolute_uri(reverse('poll:show', kwargs={'poll_id': poll.id}))
            )
        messages.add_message(req, messages.SUCCESS, "Poll reopened successfully!")
        return redirect(reverse('poll:show', kwargs={'poll_id': poll.id}))
    else:
        raise Http404


@needs_ownership
@only_open_polls
def delete_choice(req, poll, choice_id):
    try:
        Choice.objects.get(id=choice_id).delete()
    except (ObjectDoesNotExist):
        raise Http404
    messages.add_message(req, messages.SUCCESS, "Choice removed successfully!")
    return redirect(reverse('poll:show', kwargs={'poll_id': poll.id}))


@needs_ownership
@only_open_polls
def delete_user_from_poll(req, poll, user_name):
    try:
        this_audience = User.objects.get(name=user_name)
    except (ObjectDoesNotExist):
        raise Http404
    poll.audience.remove(this_audience)
    messages.add_message(req, messages.SUCCESS, "User removed successfully from poll!")
    return redirect(reverse('poll:show', kwargs={'poll_id': poll.id}))


@needs_involvement_or_ownership
@only_open_polls
def get_comments(req, poll, choice_id):
    try:
        choice =Choice.objects.get(id=choice_id)
    except (ObjectDoesNotExist):
        raise Http404
    return render(req, "polls/choice_comments.html", {
        "poll": poll,
        "choice": choice,
        "comments": Comment.objects.filter(choice=choice, parent=None)
    })


@needs_involvement_or_ownership
@only_open_polls
def get_replies(req, poll, choice_id, comment_id):
    try:
        choice =Choice.objects.get(id=choice_id)
        comment = Comment.objects.get(id=comment_id)
    except (ObjectDoesNotExist):
        raise Http404
    return render(req, "polls/comment_replies.html", {
        "poll": poll,
        "choice": choice,
        "comment": comment,
        "replies": Comment.objects.filter(choice=choice, parent=comment)
    })


@needs_involvement_or_ownership
@only_open_polls
def add_comment(req, poll, choice_id):
    if req.method == 'POST':
        try:
            choice =Choice.objects.get(id=choice_id)
        except (ObjectDoesNotExist):
            raise Http404
        Comment.objects.create(choice=choice, comment_text=req.POST["comment_text"])
        messages.add_message(req, messages.SUCCESS, "Comment added successfully to choice!")
        return redirect(reverse('poll:comments', kwargs={'poll_id': poll.id, 'choice_id': choice_id}))
    else:
        raise Http404


@needs_involvement_or_ownership
@only_open_polls
def reply_to_comment(req, poll, choice_id, comment_id):
    if req.method == 'POST':
        try:
            choice =Choice.objects.get(id=choice_id)
            comment = Comment.objects.get(id=comment_id)
        except (ObjectDoesNotExist):
            raise Http404
        Comment.objects.create(choice=choice, parent=comment, comment_text=req.POST["comment_text"])
        messages.add_message(req, messages.SUCCESS, "reply added successfully!")
        return redirect(reverse('poll:replies', kwargs={'poll_id': poll.id, 'choice_id': choice_id, 'comment_id': comment.id}))
    else:
        raise Http404

