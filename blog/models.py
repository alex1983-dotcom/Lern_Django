from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.text import slugify
from taggit.managers import TaggableManager
from mdeditor.fields import MDTextField
from django.core.files.storage import default_storage


class PublishedManager(models.Manager):
    """
    Менеджер для получения только опубликованных постов.
    """
    def get_queryset(self):
        return super().get_queryset().filter(status=Post.Status.PUBLISHED)


class Post(models.Model):
    """
    Модель для представления поста в блоге.
    """

    class Status(models.TextChoices):
        DRAFT = 'DF', 'DRAFT'
        PUBLISHED = 'PB', 'Published'

    title = models.CharField(max_length=250)
    slug = models.SlugField(max_length=250, unique_for_date='publish', blank=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blog_posts')
    body = MDTextField()
    publish = models.DateTimeField(default=timezone.now)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=2, choices=Status.choices, default=Status.DRAFT)
    objects = models.Manager()  # Менеджер применяемый по умолчанию
    published = PublishedManager()  # Конкретно - прикладной менеджер
    tags = TaggableManager()

    class Meta:
        ordering = ['-publish']
        indexes = [
            models.Index(fields=['-publish'])
        ]

    def __str__(self):
        # Возвращает строковое представление модели.
        return self.title

    def save(self, *args, **kwargs):
        # Переопределяет метод save для автоматического создания slug.
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        # Возвращает абсолютный URL для поста.
        return reverse('blog:post_detail',
                       args=[self.publish.year,
                             self.publish.month,
                             self.publish.day,
                             self.slug])


class Comment(models.Model):
    """
    Модель для представления комментария к посту.
    """
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    name = models.CharField(max_length=80)
    email = models.EmailField()
    body = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.BooleanField(default=True)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ['created']
        indexes = [
            models.Index(fields=['created']),
        ]

    def __str__(self):
        # Возвращает строковое представление модели.
        return f"Comment by {self.name} on {self.post}"


class Image(models.Model):
    """
    Модель для представления изображения.
    """
    title = models.CharField(max_length=200)
    image = models.ImageField(upload_to='images/')
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Переопределяет метод save для автоматического создания имени файла.
        if self.image:
            ext = self.image.name.split('.')[-1]
            self.image.name = f"{self.title}.{ext}"
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Переопределяет метод delete для удаления файла из хранилища.
        if self.image:
            if default_storage.exists(self.image.name):
                default_storage.delete(self.image.name)
                print("Файл успешно удалён.")
        super().delete(*args, **kwargs)

    def __str__(self):
        # Возвращает строковое представление модели.
        return self.title
