from django.db import models
from django.contrib.auth.models import AbstractUser
from bot.models import Post

"""
Model for custom django user. It inherits from Abstract Base User allowing for custom fields to be added.

"""

# 這邊去繼承 Django 的基本版 User model, 然後自己做 customized fields
class User(AbstractUser):
    telegram_id = models.BigIntegerField(primary_key=True)
    bot_chat_id = models.BigIntegerField(null=True)
    previous_photo_url = models.URLField(null=True)
    photo_url = models.URLField(null=True)
    photo = models.ImageField(null=True, upload_to='user_photos') # 是可以沒輸入, 然後自動upload到default storage (e.g., s3)
    channels = models.ManyToManyField('bot.Channel', blank=True, related_name='users')
    last_name = models.CharField(max_length=1024, blank=True, null=True)

    def __str__(self):
        return self.username

    def save(self, **kwargs):
        username = self.username
        user = User.objects.filter(username=self.username).exclude(telegram_id=self.telegram_id).first()
        count = 1
        while user:
            self.username = f"{username}_{count}"
            user = User.objects.filter(username=self.username).first()
            count += 1

        super().save(**kwargs)

    @property
    def posts(self):
        return Post.objects.filter(post_channel__users=self).distinct()

    @property
    def photo_initials(self):
        initials = ""
        if self.first_name:
            initials += self.first_name[0].upper()

        if self.last_name:
            initials += self.last_name[0].upper()

        return initials

    @property
    def full_name(self):
        name = ""
        if self.first_name:
            name += self.first_name

        if self.last_name:
            name += " " + self.last_name

        return name


"""
Model for storing user color in a given channel

"""


class UserChannelColor(models.Model):
    user = models.ForeignKey('users.User', on_delete=models.CASCADE)
    channel = models.ForeignKey('bot.Channel', on_delete=models.CASCADE)
    color = models.CharField(max_length=32)

    def __str__(self):
        return self.color
