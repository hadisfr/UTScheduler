from django.shortcuts import reverse, redirect
from django.core.exceptions import ObjectDoesNotExist

from ..models import User


def provide_user(get_response):
    def middleware(request):
        if (
                not request.path_info.startswith(reverse('admin:index'))
                and request.path_info in [reverse(url) for url in ['login', 'signup']]
        ):
            try:
                User.objects.get(name=request.session['username'])
                return redirect(reverse('landing'))
            except (ObjectDoesNotExist, ValueError, KeyError):
                if request.session.get('username', None):
                    request.session['username'] = None
                    return redirect(reverse('login'))
                else:
                    return get_response(request)
        response = get_response(request)
        return response

    return middleware
