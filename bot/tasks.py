from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.template.loader import render_to_string
from django.urls import reverse
from django.conf import settings
from django.core.files import File
from django.utils import timezone
from io import BytesIO
import requests
import re

from bot.models import DashboardNotification, Comment, PostSubscription, Post
from bot.utils.base import Base
from bot.utils.str_utils import *

from celery import shared_task
import json

channel_layer = get_channel_layer()


@shared_task
def send_dashboard_notification(dashboard_notification_id):
    dashboard_notification = DashboardNotification.objects.filter(id=dashboard_notification_id).first()

    if dashboard_notification:
        group_name = 'like-com-notifications'
        async_to_sync(channel_layer.group_send)(
            group_name,
            dict(
                type='send_dashboard_notification',
                text=render_to_string('bot/dashboard_notification.html',
                                      context=dict(dashboard_notification=dashboard_notification))
            )
        )


@shared_task
def send_comment_notification(comment_id):
    base_utils = Base(token=settings.BOT_TOKEN)
    comment = Comment.objects.filter(id=comment_id).first()
    if comment:
        base_utils.channel = comment.comment_post.post_channel
        url = reverse('comments-list', kwargs=dict(post_id=comment.comment_post.id))
        login_url = base_utils.login_url(redirect=url)
        post_url = f"{settings.BASE_URL}{url}"

        subscriptions = PostSubscription.objects.filter(post=comment.comment_post)

        for subscription in subscriptions:
            menu = [
                [
                    dict(
                        text=open_comment,
                        login_url=login_url
                    )
                ],
                [
                    dict(
                        text=unsubscribe,
                        callback_data=json.dumps(
                            dict(
                                subscribe_post_id=comment.comment_post.id
                            )
                        )
                    )

                ]
            ]

            reply_markup = dict(inline_keyboard=menu)
            if comment.parent:
                if comment.parent.user == subscription.user:
                    message = comment_replied_message.format(
                        full_name=comment.user.full_name,
                        post_url=post_url,
                        text=comment.text
                    )
                    base_utils.send_telegram_message(chat_id=subscription.user.bot_chat_id, message=message,
                                                     reply_markup=reply_markup)

            else:
                if comment.user.telegram_id != subscription.user.telegram_id:
                    message = comment_left_message.format(
                        full_name=comment.user.full_name,
                        post_url=post_url,
                        text=comment.text
                    )
                    base_utils.send_telegram_message(chat_id=subscription.user.bot_chat_id, message=message,
                                                     reply_markup=reply_markup)


@shared_task
def send_post_buttons_menu(post_id, chat_id, message_id):
    """

    :param post_id:
    :param chat_id:
    :param message_id:
    :return:
    """

    base_utils = Base(token=settings.BOT_TOKEN)
    post = Post.objects.filter(id=post_id).first()
    menu_buttons = list()

    if post:
        base_utils.channel = post.post_channel
        post_buttons = post.buttons.order_by('id')
        for button in post_buttons:
            button_emoji = button.button_emoji
            clicks_count = button.clicks.count()

            # If the button is of type comment then send a link to post comments
            if button_emoji.emoji_type == 4:
                comments_count = post.comments.count()
                url = reverse("comments-list", kwargs=dict(post_id=post.id))
                menu_buttons.append(
                    dict(
                        text=f"{button_emoji.emoji}{comments_count if comments_count else ''}",
                        login_url=base_utils.login_url(redirect=url)
                    )
                )

            # For all other buttons just send a callback button

            else:
                menu_buttons.append(
                    dict(
                        text=f"{button_emoji.emoji}{clicks_count if clicks_count else ''}",
                        callback_data=json.dumps(dict(
                            button_id=button.id,
                            post_id=post.id
                        ))
                    )
                )

    menu = base_utils.create_buttons(menu_buttons, 4)

    reply_markup = dict(inline_keyboard=menu)

    _, res = base_utils.edit_message_reply_markup(chat_id, message_id=message_id, reply_markup=reply_markup)
    print(res)


@shared_task
def download_post_image(url, post_id):
    post = Post.objects.filter(id=post_id).first()

    print("Downloading post image")

    if post:

        try:
            response = requests.get(url)

        except Exception as e:
            return

        buffer = BytesIO(response.content)

        image_name = f"post_image_{post.id}_{timezone.now().timestamp()}.jpg"
        post.image.save(image_name, File(buffer))
        buffer.close()


def entity_to_html(entity_type, entity_text, url=None):
    res = entity_text

    tags = {
        'pre': 'pre',
        'code': 'code',
        'bold': 'b',
        'strikethrough': 'del',
        'italic': 'i',
        'underline': 'u'
    }

    if entity_type == 'url':
        res = f"<a href='{entity_text}'>{entity_text}</a>"

    elif entity_type == 'text_link':
        res = f"<a href='{url}'>{entity_text}</a>"

    else:
        if entity_type in tags:
            tag = tags[entity_type]
            res = f"<{tag}>{entity_text}</{tag}>"

    return res


@shared_task
def parse_post_text(post_id, entities, caption_entities):
    if not entities and not caption_entities:
        return

    post = Post.objects.filter(id=post_id).first()

    if post:
        if caption_entities:
            entities = caption_entities
            text = post.caption

        else:
            text = post.text

        entities = [(entity['offset'], entity['length'], entity['type'], entity['url'] if 'url' in entity else None) for
                    entity in entities
                    ]
        entities = sorted(entities, key=lambda x: x[0])
        unchanged_text = list()
        changed_text = list()

        previous_end_index = 0
        for i in range(len(entities)):
            start_index = entities[i][0]
            length = entities[i][1]
            end_index = start_index + length

            entity_type = entities[i][2]
            url = entities[i][3]
            entity_text = text[start_index: end_index]

            changed_text.append(entity_to_html(entity_type, entity_text, url))
            unchanged_text.append(text[previous_end_index: start_index])

            previous_end_index = end_index

        unchanged_text.append(text[previous_end_index:])
        print(changed_text, unchanged_text)
        final_text = ''

        max_index = max(len(unchanged_text), len(changed_text))

        for i in range(max_index):
            if i < len(unchanged_text):
                final_text += unchanged_text[i]

            if i < len(changed_text):
                final_text += changed_text[i]

        print(final_text)
        if caption_entities:
            post.caption = final_text

        else:
            post.text = final_text

        post.save()
