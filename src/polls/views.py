from django.shortcuts import render, Http404, redirect, reverse
from django.core.exceptions import ObjectDoesNotExist
from django.utils.timezone import now

from .models import User, Poll, Choice, Vote
from .mail.mail import Mail
from .mail.notifier import *


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
        except ObjectDoesNotExist:
            return render(req, "login.html", {
                "msg": "Wrong authentication data!",
            }, status=401)
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
            req.session['msg'] = "Poll created successfully!"
            return redirect(reverse('poll:show', kwargs={'poll_id': poll.id}))
        else:
            raise Http404
    except ObjectDoesNotExist:
        raise Http404


def is_poll_closed(poll):
    return poll.close_date and poll.close_date < now()


def handle_poll(req, poll_id):
    def get_first_vote(l):
        return l[0].get_vote_display() if len(l) else None

    try:
        poll = Poll.objects.get(id=poll_id)
        user = req.puser
        choices = Choice.objects.filter(poll=poll)
        chosen_text = poll.chosen_choice.choice_text if is_poll_closed(poll) else ""
        if poll.owner == user:
            return render(req, "polls/poll_details.html", {
                "poll": poll,
                "choices": [{"choice": choice, "votes": [
                    {"text": opt[1], "num": Vote.objects.filter(choice=choice, vote=opt[0]).count()}
                    for opt in Vote.VOTE_T
                ]} for choice in choices],
                "involved_users": User.objects.filter(poll=poll),
                "users": User.objects.exclude(poll=poll).exclude(owner=poll),
                "closed": is_poll_closed(poll),
                "chosen": chosen_text
            })
        elif poll.audience.filter(name=req.session.get('username', None)).exists():
            return render(req, "polls/poll_vote.html", {
                "poll": poll,
                "choices": [{'choice': choice, 'vote': get_first_vote(Vote.objects.filter(voter=user, choice=choice))}
                            for choice in choices],
                "possible_votes": [vote[1] for vote in Vote.VOTE_T],
                "closed": is_poll_closed(poll),
                "chosen": chosen_text
            })
        else:
            return render(req, "login.html", {
                "msg": "Unauthorized Access",
            }, status=401)
    except ObjectDoesNotExist:
        raise Http404


def add_choice(req, poll_id):
    if req.method == 'POST':
        try:
            poll = Poll.objects.get(id=poll_id)
            if poll.owner == req.puser and not is_poll_closed(poll):
                Choice.objects.create(poll=poll, choice_text=req.POST['text'])
                req.session['msg'] = "Choice created successfully!"
                return redirect(reverse('poll:show', kwargs={'poll_id': poll.id}))
            else:
                raise Http404
        except ObjectDoesNotExist:
            raise Http404
    else:
        raise Http404


def add_user_to_poll(req, poll_id):
    if req.method == 'POST':
        try:
            poll = Poll.objects.get(id=poll_id)
            if poll.owner == req.puser and not is_poll_closed(poll):
                this_audience = User.objects.get(name=req.POST['username'])
                poll.audience.add(this_audience)
                uri = req.build_absolute_uri()
                uri = uri[:uri.rfind('/')]
                nn = Notifier(Mail())
                nn.notify_participate(req.puser, this_audience, uri)
                req.session['msg'] = "User added successfully!"
                return redirect(reverse('poll:show', kwargs={'poll_id': poll.id}))
            else:
                raise Http404
        except ObjectDoesNotExist:
            raise Http404
    else:
        raise Http404


def vote(req, poll_id):
    choice_prefix = 'vote_'
    if req.method == 'POST':
        try:
            poll = Poll.objects.get(id=poll_id)
            if poll.audience.filter(name=req.puser.name).exists() and not is_poll_closed(poll):
                for key in req.POST:
                    if key.startswith(choice_prefix):
                        choice = Choice.objects.get(id=key[len(choice_prefix):])
                        if choice.poll != poll:
                            raise Http404
                        Vote.objects.update_or_create(
                            voter=req.puser,
                            choice=choice,
                            defaults={'vote': {key: value for (value, key) in Vote.VOTE_T}[req.POST[key]]},
                        )
                req.session['msg'] = "Voted successfully!"
                return redirect(reverse('poll:show', kwargs={'poll_id': poll.id}))
            else:
                raise Http404
        except (ObjectDoesNotExist, ValueError):
            raise Http404
    else:
        raise Http404


def end_poll(req, poll_id):
    if req.method == 'POST':
        try:
            poll = Poll.objects.get(id=poll_id)
            if poll.owner == req.puser and not is_poll_closed(poll):
                try:
                    poll.chosen_choice = Choice.objects.get(id=req.POST['choice'])
                except ObjectDoesNotExist:
                    raise Http404
                poll.close_date = now()
                poll.save()
                req.session['msg'] = "Poll closed successfully!"
                return redirect(reverse('poll:show', kwargs={'poll_id': poll.id}))
            else:
                raise Http404
        except (ObjectDoesNotExist, ValueError):
            raise Http404
    else:
        raise Http404


def begin_poll(req, poll_id):
    if req.method == 'POST':
        try:
            poll = Poll.objects.get(id=poll_id)
            if poll.owner == req.puser:
                poll.chosen_choice = None
                poll.close_date = None
                poll.save()
                req.session['msg'] = "Poll reopened successfully!"
                return redirect(reverse('poll:show', kwargs={'poll_id': poll.id}))
            else:
                raise Http404
        except ObjectDoesNotExist:
            raise Http404
    else:
        raise Http404
