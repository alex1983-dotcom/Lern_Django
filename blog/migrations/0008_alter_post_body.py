# Generated by Django 5.1.4 on 2024-12-16 21:20

import mdeditor.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0007_alter_post_body'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='body',
            field=mdeditor.fields.MDTextField(),
        ),
    ]
