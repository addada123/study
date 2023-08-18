import uuid
from django.core.validators import FileExtensionValidator
import os
from django.conf import settings
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)

def recipe_image_file_path(instance, filename):
    ext = os.path.splitext(filename)[1]
    filename = f'{uuid.uuid4()}{ext}'
    return os.path.join('uploads', 'recipe', filename)

class Tag(models.Model):
    name = models.CharField(max_length=255)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    def __str__(self):
        return self.name

class UserManager(BaseUserManager):

    def create_user(self, email, password=None, **extra_fields):
        """Create, save and return a new user."""
        if not email:
            raise ValueError('User must have an email address.')
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password):
        """Create and return a new superuser."""
        user = self.create_user(email, password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)

        return user


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    objects = UserManager()
    USERNAME_FIELD = 'email'


class Recipe(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    time_minutes = models.IntegerField()
    price = models.DecimalField(max_digits=5, decimal_places=2)
    link = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    tags = models.ManyToManyField(Tag)
    likes_count = models.ManyToManyField('Like', related_name='likes_count')
    ingredients = models.ManyToManyField('Ingredient')
    image = models.ImageField(upload_to=recipe_image_file_path,
                              validators=[FileExtensionValidator(['png'])])
    def __str__(self):
        return self.title

    def like_recipe(self, user):
        like, created = Like.objects.get_or_create(recipe=self, user=user)
        if created:
            self.likes_count.add(like)

    def unlike_recipe(self, user):
        try:
            like = self.likes_count.get(user=user)
            self.likes_count.remove(like)
            like.delete()
        except Like.DoesNotExist:
            pass

    def get_total_likes(self):
        return self.likes_count.count()

class Ingredient(models.Model):
    name = models.CharField(max_length=255)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return self.name

class Like(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)

