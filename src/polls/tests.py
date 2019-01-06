from django.test import TestCase
from .mail import notifier
from .models import User, TimedChoice, RecurringChoice, Poll
from datetime import datetime
from django.core.mail import send_mail


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
        User.objects.create(name="tayer", email="m.taiaranian@gmail.com")

    def test_notifier_valid_users_text_generated_properly(self):
        send_mail("ssss", "shshsh", "emad.jabbarnk@gmail.com", ["m.taiaranian@gmail.com"], fail_silently=False,)
        val = self.ntf.notify_participate(User.objects.get(email="emad@gmail.com"), User.objects.get(email="m.taiaranian@gmail.com"), self.link)
        self.assertEqual(self.ml.ef, "emad@gmail.com")
        self.assertEqual(self.ml.et, "m.taiaranian@gmail.com")
        self.assertEqual(self.ml.sub, "UTScheduler")
        self.assertEqual(self.ml.msg, "you are involved in a poll:\n"+self.link)


class OverLapTest(TestCase):
    def setUp(self):
        self.owner = User.objects.create(name="owner", email="emad.jabbarnk@gmail.com")
        self.rec_poll = Poll.objects.create(question_text='dummy_recurring', owner=self.owner, poll_type=2)
        self.tim_poll = Poll.objects.create(question_text='dummy_Timed', owner=self.owner, poll_type=1)


    def create_timed_choice(self, st1, et1):
        st_d1 = datetime.strptime(st1, '%Y-%m-%d %H:%M')
        et_d1 = datetime.strptime(et1, '%Y-%m-%d %H:%M')
        choice = TimedChoice.objects.create(poll=self.tim_poll, start_date=st_d1, end_date=et_d1)
        return choice

    def create_recurring_choice(self, st1, et1, w1):
        st_d1 = datetime.strptime(st1, '%H:%M').time()
        et_d1 = datetime.strptime(et1, '%H:%M').time()
        choice = RecurringChoice.objects.create(poll=self.rec_poll, weekday=w1, start_time=st_d1, end_time=et_d1)
        return choice

    def create_timed_choices(self, st1, et1, st2, et2):
        choice_one = self.create_timed_choice(st1, et1)
        choice_two = self.create_timed_choice(st2, et2)
        return choice_one, choice_two

    def create_recurring_choices(self, st1, et1, w1, st2, et2, w2):
        choice_one = self.create_recurring_choice(st1, et1, w1)
        choice_two = self.create_recurring_choice(st2, et2, w2)
        return choice_one, choice_two

    def test_overlap_two_time_poll_have_overlap_should_return_true(self):
        choice_one, choice_two = self.create_timed_choices('2019-01-09' + ' ' + '13:00', '2019-01-09' + ' ' + '14:00',
                                                           '2019-01-09' + ' ' + '13:30', '2019-01-09' + ' ' + '14:20')
        self.assertTrue(choice_two.overlaps(choice_one), "timed choices should have overlap")

    def test_overlap_two_time_poll_not_overlap_same_day_should_return_false(self):
        choice_one, choice_two = self.create_timed_choices('2019-01-09' + ' ' + '13:00', '2019-01-09' + ' ' + '14:30',
                                                           '2019-01-09' + ' ' + '14:35', '2019-01-09' + ' ' + '16:20')
        self.assertFalse(choice_two.overlaps(choice_one), "timed choices should have no overlap")

    def test_overlap_two_time_poll_not_overlap_diff_daies_should_return_false(self):
        choice_one, choice_two = self.create_timed_choices('2019-01-09' + ' ' + '13:00', '2019-01-09' + ' ' + '14:00',
                                                           '2019-01-16' + ' ' + '13:30', '2019-01-16' + ' ' + '14:20')
        self.assertFalse(choice_two.overlaps(choice_one), "timed choices should have no overlap")

    def test_overlap_two_recurring_poll_have_overlap_should_return_true(self):
        choice_one, choice_two = self.create_recurring_choices('13:00', '14:00', 2,
                                                               '13:30', '14:20', 2)
        self.assertTrue(choice_two.overlaps(choice_one), "recurring choices should have overlap")

    def test_overlap_two_recurring_poll_have_no_overlap_same_day_should_return_false(self):
        choice_one, choice_two = self.create_recurring_choices('13:00', '14:00', 2,
                                                               '14:30', '15:20', 2)
        self.assertFalse(choice_two.overlaps(choice_one), "recurring choices should have no overlap")

    def test_overlap_two_recurring_poll_have_no_overlap_diff_day_should_return_false(self):
        choice_one, choice_two = self.create_recurring_choices('13:00', '14:00', 2,
                                                               '13:20', '15:20', 3)
        self.assertFalse(choice_two.overlaps(choice_one), "recurring choices should have no overlap")

    def test_timed_choice_have_overlap_with_recurring_choice_should_return_true(self):
        choice_one = self.create_timed_choice('2019-01-09' + ' ' + '13:00', '2019-01-09' + ' ' + '14:00')
        choice_two = self.create_recurring_choice('13:20', '14:10', 2)
        self.assertTrue(choice_one.overlaps(choice_two), "timed choices should have overlap")

    def test_timed_choice_have_no_overlap_with_recurring_choice_same_day_should_return_false(self):
        choice_one = self.create_timed_choice('2019-01-09' + ' ' + '13:00', '2019-01-09' + ' ' + '14:00')
        choice_two = self.create_recurring_choice('16:20', '17:10', 2)
        self.assertFalse(choice_one.overlaps(choice_two), "timed choices should have no overlap")

    def test_timed_choice_have_no_overlap_with_recurring_choice_diff_day_should_return_false(self):
        choice_one = self.create_timed_choice('2019-01-09' + ' ' + '13:00', '2019-01-09' + ' ' + '14:00')
        choice_two = self.create_recurring_choice('13:20', '14:10', 3)
        self.assertFalse(choice_one.overlaps(choice_two), "timed choices should have no overlap")

    def test_recurring_choice_have_overlap_with_timed_choice_should_return_true(self):
        choice_one = self.create_recurring_choice('13:20', '14:10', 2)
        choice_two = self.create_timed_choice('2019-01-09' + ' ' + '13:00', '2019-01-09' + ' ' + '14:00')
        self.assertTrue(choice_one.overlaps(choice_two), "recurring choice should have overlap")


    def test_recurring_choice_have_no_overlap_with_timed_choice_same_day_should_return_false(self):
        choice_one = self.create_recurring_choice('16:20', '17:10', 2)
        choice_two = self.create_timed_choice('2019-01-09' + ' ' + '13:00', '2019-01-09' + ' ' + '14:00')
        self.assertFalse(choice_one.overlaps(choice_two), "recurring choices should have no overlap")

    def test_recurring_choice_have_no_overlap_with_timed_choice_diff_day_should_return_false(self):
        choice_one = self.create_recurring_choice('13:20', '14:10', 3)
        choice_two = self.create_timed_choice('2019-01-09' + ' ' + '13:00', '2019-01-09' + ' ' + '14:00')
        self.assertFalse(choice_one.overlaps(choice_two), "recurring choices should have no overlap")
