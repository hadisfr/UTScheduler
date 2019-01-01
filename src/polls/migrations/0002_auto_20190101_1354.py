# Generated by Django 2.1.4 on 2019-01-01 13:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='poll',
            name='isTimed',
        ),
        migrations.AddField(
            model_name='poll',
            name='poll_type',
            field=models.IntegerField(choices=[(0, 'Textual'), (1, 'Timed'), (2, 'Recurring')], default=0),
        ),
    ]
