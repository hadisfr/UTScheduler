from django.shortcuts import render, Http404, redirect, reverse
from django.core.exceptions import ObjectDoesNotExist
from django.db.utils import IntegrityError
from django.utils.timezone import now
from django.contrib import messages

from .models import User, Poll, Choice, Vote
from .mail.mail import Mail
from .mail.notifier import Notifier


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
        except (ObjectDoesNotExist, ValueError):
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
        except (IntegrityError, ValueError):
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
            return render(req, "polls/new_poll.html")
        elif req.method == 'POST':
            poll = Poll.objects.create(question_text=req.POST['question'], owner=req.puser)
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
        "chosen": poll.chosen_choice.choice_text if is_poll_closed(poll) else ""
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
        "chosen": poll.chosen_choice.choice_text if is_poll_closed(poll) else ""
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
        Choice.objects.create(poll=poll, choice_text=req.POST['text'])
        messages.add_message(req, messages.SUCCESS, "Choice created successfully!")
        return redirect(reverse('poll:show', kwargs={'poll_id': poll.id}))
    else:
        raise Http404


@needs_ownership
@only_open_polls
def add_user_to_poll(req, poll):
    if req.method == 'POST':
        try:
            this_audience = User.objects.get(name=req.POST['username'])
        except (ObjectDoesNotExist, ValueError):
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
        for key in req.POST:
            if key.startswith(choice_prefix):
                try:
                    choice = Choice.objects.get(id=key[len(choice_prefix):])
                except (ObjectDoesNotExist, ValueError):
                    raise Http404
                if choice.poll != poll:
                    raise Http404
                Vote.objects.update_or_create(
                    voter=req.puser,
                    choice=choice,
                    defaults={'vote': {key: value for (value, key) in Vote.VOTE_T}[req.POST[key]]},
                )
        messages.add_message(req, messages.SUCCESS, "Voted successfully!")
        return redirect(reverse('poll:show', kwargs={'poll_id': poll.id}))
    else:
        raise Http404


@needs_ownership
@only_open_polls
def end_poll(req, poll):
    if req.method == 'POST':
        try:
            poll.chosen_choice = Choice.objects.get(id=req.POST['choice'])
        except (ObjectDoesNotExist, ValueError):
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
