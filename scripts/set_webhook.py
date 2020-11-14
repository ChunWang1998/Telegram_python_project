from django.conf import settings

from bot.utils.livecom_utils import LiveCom

live_com = LiveCom()


def run():
    live_com.set_webhook(token=settings.BOT_TOKEN, webhook_url=f"{settings.BASE_URL}/webhook/{settings.BOT_TOKEN}")
