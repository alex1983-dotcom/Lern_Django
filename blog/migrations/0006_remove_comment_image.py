# Generated by Django 5.1.4 on 2024-12-16 20:56

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0005_comment_image'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='comment',
            name='image',
        ),
    ]
