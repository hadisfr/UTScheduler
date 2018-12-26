from django.shortcuts import reverse, redirect
from django.core.exceptions import ObjectDoesNotExist

from ..models import User


def provide_user(get_response):
    def middleware(request):
        if request.path_info != reverse('login'):
            try:
                setattr(request, 'puser', User.objects.get(name=request.session['username']))
            except (ObjectDoesNotExist, ValueError):
                return redirect(reverse('login'))
        response = get_response(request)
        return response

    return middleware
