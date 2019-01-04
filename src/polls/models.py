from django.db import models


class User(models.Model):
    name = models.CharField(max_length=40, primary_key=True)
    email = models.EmailField()


class Poll(models.Model):
    question_text = models.CharField(max_length=200)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="owner")
    audience = models.ManyToManyField(User)
    pub_date = models.DateTimeField(auto_now_add=True)
    close_date = models.DateTimeField(null=True)
    chosen_choice = models.ForeignKey('Choice', on_delete=models.CASCADE, null=True, related_name="chosen")
    POLL_T_TEXTUAL = 0
    POLL_T_TIMED = 1
    POLL_T_RECURRING = 2
    POLL_T = (
        (POLL_T_TEXTUAL, 'Textual'),
        (POLL_T_TIMED, 'Timed'),
        (POLL_T_RECURRING, 'Recurring'),
    )
    poll_type = models.IntegerField(choices=POLL_T, default=0)

    def __str__(self):
        return self.question_text


class Choice(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE)

    def __str__(self):
        if self.poll.poll_type == Poll.POLL_T_TEXTUAL:
            return str(self.textchoice)
        elif self.poll.poll_type == Poll.POLL_T_TIMED:
            return str(self.timedchoice)
        elif self.poll.poll_type == Poll.POLL_T_RECURRING:
            return str(self.recurringchoice)
        else:
            raise NotImplementedError()


class TextChoice(Choice):
    content = models.CharField(max_length=200)

    def __str__(self):
        return self.content


class TimedChoice(Choice):
    start_date = models.DateTimeField(null=True)
    end_date = models.DateTimeField(null=True)

    def overlaps(self, other):
        if other.__class__ == TimedChoice:
            if (self.start_date <= other.start_date <= self.end_date) or (
                self.start_date <= other.end_date <= self.end_date) or (
                other.start_date <= self.start_date <= other.end_date) or (
                other.start_date <= self.end_date <= other.end_date):
                return True
            return False
        elif other.__class__ == RecurringChoice:
            if self.start_date.weekday() == other.weekday:
                if (self.start_date.time() <= other.start_time <= self.end_date.time()) or (
                    self.start_date.time() <= other.end_time <= self.end_date.time()) or (
                    other.start_time <= self.start_date.time() <= other.end_time) or (
                    other.start_time <= self.end_date.time() <= other.end_time):
                        return True
            return False

    def __str__(self):
        return 'On: ' + str(self.start_date.strftime('%Y-%m-%d')) + ', ' + str(self.start_date.strftime('%H:%m')) + ' to ' + str(self.end_date.strftime('%H:%m'))


class RecurringChoice(Choice):
    WEEKDAYS = (
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    )
    weekday = models.IntegerField(choices=WEEKDAYS)
    start_time = models.TimeField()
    end_time = models.TimeField()

    def overlaps(self, other):
        if other.__class__ == TimedChoice:
            if self.weekday == other.start_date.weekday():
                if (self.start_time <= other.start_date.time() <= self.end_time) or (
                    self.start_time <= other.end_date.time() <= self.end_time) or (
                    other.start_date.time() <= self.start_time <= other.end_date.time()) or (
                    other.start_date.time() <= self.end_time <= other.end_date.time()):
                    return True
            return False
        elif other.__class__ == RecurringChoice:
            if self.weekday == other.weekday:
                if (self.start_time <= other.start_time <= self.end_time) or (
                    self.start_time <= other.end_time <= self.end_time) or (
                    other.start_time <= self.start_time <= other.end_time) or (
                    other.start_time <= self.end_time <= other.end_time):
                        return True
            return False

    def __str__(self):
        return 'Every ' + str(self.WEEKDAYS[self.weekday][1]) + ', ' + str(self.start_time.strftime('%H:%M')) + ' to ' + str(self.end_time.strftime('%H:%M'))


class Vote(models.Model):
    VOTE_T = (
        (1, 'Yes'),
        (0, 'Maybe'),
        (-1, 'No'),
    )
    voter = models.ForeignKey(User, on_delete=models.CASCADE)
    choice = models.ForeignKey(Choice, on_delete=models.CASCADE)
    vote = models.IntegerField(choices=VOTE_T)

    class Meta:
        unique_together = (("voter", "choice"),)


class Comment(models.Model):
    choice = models.ForeignKey('Choice', on_delete=models.CASCADE)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True)
    comment_text = models.CharField(max_length=400)
