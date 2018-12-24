from django.shortcuts import render, Http404, redirect
from django.core.exceptions import ObjectDoesNotExist

from .models import User, Poll, Choice, Vote


def my_polls(req):
    try:
        user = User.objects.get(name=req.session['username'])
        owned_polls = Poll.objects.filter(owner=user)
        involved_polls = Poll.objects.filter(audience=user)
        return render(req, "polls/my_polls.html", {"owned_polls": owned_polls, "involved_polls": involved_polls})
    except ObjectDoesNotExist:
        raise Http404


def login(req):
    if req.method == 'GET':
        return render(req, "login.html")
    elif req.method == 'POST':
        try:
            user = User.objects.get(name=req.POST['username'])
            req.session['username'] = user.name
            if req.POST.get('redirect', None):
                return redirect("/%s" % req.POST['redirect'])
            else:
                return redirect("/")
        except ObjectDoesNotExist:
            return render(req, "login.html", {
                "msg": "Wrong authentication data!",
                "redirect": req.POST.get('redirect', None)
            }, status=401)
    else:
        raise Http404


def logout(req):
    req.session['username'] = None
    return redirect("/")


def new_poll(req):
    try:
        if req.method == 'GET':
            return render(req, "polls/new_poll.html")
        elif req.method == 'POST':
            poll = Poll.objects.create(question_text=req.POST['question'], owner=User.objects.get(name=req.session['username']))
            return redirect("/polls/poll/%s" % poll.id, {"msg": "Poll created successfully!"})
        else:
            raise Http404
    except ObjectDoesNotExist:
        raise Http404


def handle_poll(req, poll_id):
    try:
        poll = Poll.objects.get(id=poll_id)
        user = User.objects.get(name=req.session['username'])
        choices = Choice.objects.filter(poll=poll)
        if poll.owner == user:
            return render(req, "polls/poll_details.html", {
                "poll": poll,
                "choices": choices,
                "involved_users": User.objects.filter(poll=poll),
                "users": User.objects.exclude(poll=poll).exclude(owner=poll),
            })
        elif poll.audience.filter(name=req.session['username']).exists():
            return render(req, "polls/poll_vote.html", {
                "poll": poll,
                "choices": choices,
                "involved_users": User.objects.filter(poll=poll),
                "users": User.objects.exclude(poll=poll).exclude(owner=poll),
            })
        else:
            return render(req, "login.html", {
                "msg": "Unauthorized Access",
                "redirect": req.POST.get('redirect', None)
            }, status=401)
    except ObjectDoesNotExist:
        raise Http404


def add_choice(req, poll_id):
    if req.method == 'POST':
        try:
            poll = Poll.objects.get(id=poll_id)
            user = User.objects.get(name=req.session['username'])
            if poll.owner == user:
                Choice.objects.create(poll=poll, choice_text=req.POST['text'])
                return redirect("/polls/poll/%s" % poll.id, {"msg": "Choice created successfully!"})
            else:
                return render(req, "login.html", {
                    "msg": "Unauthorized Access",
                    "redirect": req.POST.get('redirect', None)
                }, status=401)
        except ObjectDoesNotExist:
            raise Http404
    else:
        raise Http404


def add_user_to_poll(req, poll_id):
    if req.method == 'POST':
        try:
            poll = Poll.objects.get(id=poll_id)
            user = User.objects.get(name=req.session['username'])
            if poll.owner == user:
                poll.audience.add(User.objects.get(name=req.POST['username']))
                return redirect("/polls/poll/%s" % poll.id, {"msg": "User added successfully!"})
            else:
                return render(req, "login.html", {
                    "msg": "Unauthorized Access",
                    "redirect": req.POST.get('redirect', None)
                }, status=401)
        except ObjectDoesNotExist:
            raise Http404
    else:
        raise Http404
