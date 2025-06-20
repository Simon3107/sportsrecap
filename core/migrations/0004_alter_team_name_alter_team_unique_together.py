# Generated by Django 5.2.2 on 2025-06-12 13:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_team_sport'),
    ]

    operations = [
        migrations.AlterField(
            model_name='team',
            name='name',
            field=models.CharField(max_length=100),
        ),
        migrations.AlterUniqueTogether(
            name='team',
            unique_together={('name', 'sport')},
        ),
    ]
