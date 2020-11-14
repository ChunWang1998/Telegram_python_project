import randomcolor

from users.models import UserChannelColor


def generate_user_colors(user, channel):
    color = randomcolor.RandomColor().generate()[0]
    channel_color = UserChannelColor.objects.filter(
        channel=channel,
        user=user
    ).first()

    if not channel_color:
        while UserChannelColor.objects.filter(color=color).exists():
            color = randomcolor.RandomColor().generate()[0]

        UserChannelColor.objects.create(
            channel=channel,
            user=user,
            color=color
        )
