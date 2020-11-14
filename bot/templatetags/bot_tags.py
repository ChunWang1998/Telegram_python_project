from django import template
from users.models import UserChannelColor
from bot.models import PostSubscription

register = template.Library()


@register.simple_tag
def get_user_color(user, channel):
    user_color = None
    user_channel_color = UserChannelColor.objects.filter(user=user, channel=channel).first()

    if user_channel_color:
        user_color = user_channel_color.color

    return user_color


@register.simple_tag
def user_liked(user, comment):
    if user.is_anonymous:
        return False

    return comment.likes.filter(user__isnull=False).filter(user=user).exists()


@register.simple_tag
def post_subscribed(user, post):
    return PostSubscription.objects.filter(user=user, post=post).exists()
