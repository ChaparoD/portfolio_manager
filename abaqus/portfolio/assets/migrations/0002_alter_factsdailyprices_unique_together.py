# Generated by Django 5.2 on 2025-04-26 17:20

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0001_initial'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='factsdailyprices',
            unique_together={('date', 'asset')},
        ),
    ]
