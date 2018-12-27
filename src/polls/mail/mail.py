from django.core.mail import send_mail
from django.core.mail import EmailMessage


class Mail:
    def send_email(self, subject, message, e_from, e_to):
        # send_mail(subject, message, e_from, [e_to], fail_silently=False,)
        email = EmailMessage(subject, message, to=[e_to])
        email.send()
