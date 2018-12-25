from django.core.mail import send_mail


class Mail:
    def send_email(self, subject, message, e_from, e_to):
        send_mail(subject, message, e_from, [e_to], fail_silently=False,)


