from django.db import models
from django.db.models import Count
from django.db.models.signals import post_save
from django.utils import timezone

import secrets
import randomcolor

random_color = randomcolor.RandomColor()

"""
 A base class with date_created and date_modified
 
"""


class TimeStampedModel(models.Model):
    date_created = models.DateTimeField(null=True)
    date_modified = models.DateTimeField(null=True)

    class Meta:
        abstract = True

    @property
    def is_edited(self):
        return self.date_created != self.date_modified

    def save(self, **kwargs):
        now = timezone.now()
        if not self.date_created:
            self.date_created = now

        self.date_modified = now

        super().save(**kwargs)

    @property
    def time(self):
        date_modified = self.date_modified if self.date_modified else self.date_created

        date_modified = timezone.localtime(date_modified)

        if timezone.now() - timezone.timedelta(days=1) > date_modified:
            return date_modified.strftime('%m %d, %Y')

        else:
            return date_modified.strftime("%I:%M %p")


"""
Model to store telegram channel
"""


class Channel(TimeStampedModel):
    token = models.CharField(null=True, max_length=128)
    telegram_id = models.BigIntegerField()
    title = models.CharField(max_length=256)
    username = models.CharField(max_length=256)

    def __str__(self):
        return self.username

    def save(self, **kwargs):
        if not self.token:
            self.token = str(secrets.token_hex(16))

        super().save(**kwargs)

    def clicks_count(self, button_emoji):
        return self.buttons.filter(button_emoji=button_emoji).aggregate(clicks_count=Count('clicks__id'))[
            'clicks_count']

    def get_buttons_data(self):
        data = list()
        for button_emoji in self.button_emojis.order_by('id'):
            if button_emoji.emoji_type == 4:
                post_ids = button_emoji.buttons.values('button_post__id').distinct()
                comments_count = Comment.objects.filter(comment_post__id__in=post_ids).distinct().count()
                data.append(f"{button_emoji.emoji} {comments_count}")

            else:
                data.append(f"{button_emoji.emoji} {self.clicks_count(button_emoji)}")

        return data

    def get_minimal_data(self):
        data = [self.title] + self.get_buttons_data()

        return data

    def get_data(self):
        data = [self.title, self.users.count()] + self.get_buttons_data()

        return data


"""
 Model to store telegram post
"""


class Post(TimeStampedModel):
    post_channel = models.ForeignKey(Channel, related_name='posts', null=True, on_delete=models.CASCADE)
    text = models.TextField(null=True, blank=True)
    caption = models.TextField(null=True, blank=True)
    post_url = models.URLField(null=True)
    image = models.ImageField(null=True, upload_to="post_images")
    has_video = models.BooleanField(default=False)

    def __str__(self):
        return f"post-{self.id}"

    def get_buttons_data(self):
        data = list()
        total_count = 0
        for button in self.buttons.order_by('button_emoji__id'):
            button_emoji = button.button_emoji
            if button_emoji.emoji_type == 4:
                comments_count = Comment.objects.filter(comment_post=button.button_post).count()
                total_count += comments_count
                data.append(f"{button_emoji.emoji} {comments_count}")
            else:
                clicks_count = button.clicks.count()
                total_count += clicks_count
                data.append(f"{button_emoji.emoji} {clicks_count}")

        data.append(total_count)

        return data

    def get_minimal_data(self):
        data = [self.post_channel.title, self.id] + self.get_buttons_data()
        return data

    def get_data(self):
        data = [self.post_channel.title, self.id, self.date_created] + self.get_buttons_data()

        return data
    def test(self):
        print("get!")


"""
A model for post subscriptions

"""


class PostSubscription(models.Model):
    post = models.ForeignKey('bot.Post', related_name='subscriptions', on_delete=models.CASCADE)
    user = models.ForeignKey('users.User', related_name='subscriptions', on_delete=models.CASCADE)


"""
Model to store each button emoji
"""


class ButtonEmoji(models.Model):
    ONE, TWO, THREE, FOUR = [_ for _ in range(1, 5)]
    EMOJI_TYPES = (
        (ONE, 'One'),
        (TWO, 'Two'),
        (THREE, "Three"),
        (FOUR, "Four")
    )
    emoji = models.CharField(max_length=8)
    emoji_type = models.IntegerField(choices=EMOJI_TYPES)
    button_emoji_channel = models.ForeignKey('bot.Channel', related_name='button_emojis', on_delete=models.CASCADE)


"""
Model to store button
"""


class Button(TimeStampedModel):
    button_post = models.ForeignKey('bot.Post', on_delete=models.CASCADE, related_name='buttons')
    button_channel = models.ForeignKey('bot.Channel', related_name='buttons', on_delete=models.CASCADE, null=True)
    button_emoji = models.ForeignKey("bot.ButtonEmoji", related_name='buttons', on_delete=models.CASCADE, null=True)


"""
Model to store a button click
"""


class ButtonClick(TimeStampedModel):
    click_button = models.ForeignKey('bot.Button', related_name='clicks', on_delete=models.CASCADE)
    click_channel = models.ForeignKey('bot.Channel', related_name='clicks', on_delete=models.CASCADE, null=True)
    user = models.ForeignKey('users.User', related_name='clicks', on_delete=models.CASCADE, null=True)


"""
Model to store a comment
"""


class Comment(TimeStampedModel):
    comment_post = models.ForeignKey('bot.Post', on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='created_comments', null=True)
    parent = models.ForeignKey('bot.Comment', related_name='replies', on_delete=models.CASCADE, null=True)
    text = models.TextField()

    def __str__(self):
        return self.text


"""
Model to store comment like
"""


class CommentLike(models.Model):
    user = models.ForeignKey('users.User', related_name='comment_likes', on_delete=models.CASCADE)
    comment = models.ForeignKey('bot.Comment', related_name='likes', on_delete=models.CASCADE)


"""
Model to store a Dashboard Notification
"""


class DashboardNotification(TimeStampedModel):
    user = models.ForeignKey('users.User', related_name='dashboard_notifications',
                             on_delete=models.CASCADE, null=True)
    notification_channel = models.ForeignKey('bot.Channel', related_name='dashboard_notifications',
                                             on_delete=models.CASCADE,
                                             null=True)
    emoji = models.CharField(max_length=8, null=True)


"""
This function assigns buttons to a given post after it is created

"""


def post_post_save_action(sender, instance, created, **kwargs):
    if created:
        if instance.post_channel:
            for button_emoji in instance.post_channel.button_emojis.all():
                Button.objects.create(
                    button_post=instance,
                    button_channel=instance.post_channel,
                    button_emoji=button_emoji
                )


"""
This function assigns button emojis to a given channel after it is created
"""


def channel_post_save_action(sender, instance, created, **kwargs):
    if created:
        emojis = [button_emoji.emoji for button_emoji in instance.button_emojis.all()]
        emojis = emojis if emojis else ["❤", "😂", "😜", "💬"]
        for i in range(1, 5):
            button_emoji, _ = ButtonEmoji.objects.get_or_create(
                emoji_type=i,
                emoji=emojis[i - 1],
                button_emoji_channel=instance
            )


post_save.connect(post_post_save_action, sender=Post)
post_save.connect(channel_post_save_action, sender=Channel)
