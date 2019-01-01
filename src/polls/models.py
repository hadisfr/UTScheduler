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
    isTimed = models.BooleanField(null=True, default=False)


class Choice(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE)


class TextChoice(Choice):
    content = models.CharField(max_length=200)


class TimedChoice(Choice):
    content = models.DateTimeField()


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
