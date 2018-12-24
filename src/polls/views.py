from django.shortcuts import render, Http404, redirect
from django.core.exceptions import ObjectDoesNotExist

from .models import User


def my_polls(req):
    return render(req, "polls/my_polls.html")


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
