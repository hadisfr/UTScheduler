from django.shortcuts import reverse, redirect
from django.core.exceptions import ObjectDoesNotExist

from ..models import User


def provide_user(get_response):
    def middleware(request):
        if request.path_info.startswith(reverse('admin:index')) or\
                request.path_info.startswith(str(reverse('validate_email', kwargs={'username': 'h'})[:-1])):
            return get_response(request)
        if request.path_info in [reverse(url) for url in ['login', 'signup']]:
            try:
                User.objects.get(name=request.session['username'], isRegistered=True)
                return redirect(reverse('landing'))
            except (ObjectDoesNotExist, ValueError, KeyError):
                if request.session.get('username', None):
                    request.session['username'] = None
                    return redirect(reverse('login'))
                else:
                    return get_response(request)
        elif request.path_info.split('/')[0] not in [reverse(url) for url in ['admin:index']]:
            try:
                setattr(request, 'puser', User.objects.get(name=request.session['username'], isRegistered=True))
            except (ObjectDoesNotExist, ValueError, KeyError):
                return redirect(reverse('login'))
        response = get_response(request)
        return response

    return middleware
