# Generated by Django 5.1.4 on 2024-12-17 21:10

import mdeditor.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0009_alter_post_body'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='body',
            field=mdeditor.fields.MDTextField(),
        ),
    ]
