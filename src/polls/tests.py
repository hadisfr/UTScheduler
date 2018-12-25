from django.test import TestCase
from unittest.mock import MagicMock
from .mail import notifier
from .models import User


# Create your tests here.

# run tests:
# python3 src/manage.py test polls

# pre: MYSQL
# GRANT ALL PRIVILEGES ON test_utscheduler . * TO 'ut'@'localhost';

class MockMail:
    def __init__(self):
        self.sub = ""
        self.msg = ""
        self.ef = ""
        self.et = ""

    def send_email(self, subject, message, e_from, e_to):
        self.sub = subject
        self.msg = message
        self.ef = e_from
        self.et = e_to


class EmailTest(TestCase):
    def setUp(self):
        self.link = "link"
        self.ml = MockMail()
        self.ntf = notifier.Notifier(self.ml)
        User.objects.create(name="emad", email="emad@gmail.com")
        User.objects.create(name="tayer", email="tayer@gmail.com")

    def test_notifier_valid_users_text_generated_properly(self):
        val = self.ntf.notify_participate(User.objects.get(email="emad@gmail.com"), User.objects.get(email="tayer@gmail.com"), self.link)
        self.assertEqual(self.ml.ef, "emad@gmail.com")
        self.assertEqual(self.ml.et, "tayer@gmail.com")
        self.assertEqual(self.ml.sub, "UTScheduler")
        self.assertEqual(self.ml.msg, "you are involved in a poll:\n"+self.link)
