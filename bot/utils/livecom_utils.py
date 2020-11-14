from .base import Base
from django.conf import settings

from bot.models import Channel, Post, Button, ButtonClick, DashboardNotification, PostSubscription
from bot.tasks import send_dashboard_notification, send_post_buttons_menu, download_post_image, parse_post_text
from users.models import User

from .str_utils import *
import json


class LiveCom(Base):

    @staticmethod
    def update_object(obj, data):
        """
        Updates a given obj's properties
        :param self:
        :param obj:
        :param data:
        :return:
        """
        for key, value in data.items():
            setattr(obj, key, value)

        obj.save()

    def create_user(self, from_):

        from_['telegram_id'] = from_['id']
        del from_['id']
        user, _ = User.objects.get_or_create(telegram_id=from_['telegram_id'])
        self.update_object(user, from_)
        self._user = user

    def create_channel(self, channel_data):
        channel_data['telegram_id'] = channel_data['id']
        del channel_data['id']
        del channel_data['type']

        channel, _ = Channel.objects.get_or_create(telegram_id=channel_data['telegram_id'])
        self.update_object(channel, channel_data)
        self.channel = channel

    def handle_message(self, request_json):

        message = request_json['message']
        from_ = message['from']
        chat_id = message['chat']['id']
        user_id = message['from']['id']
        reply_markup = None

        from_['bot_chat_id'] = chat_id
        self.create_user(from_)

        is_from_channel = False

        # in case the user logged in for the first time, just do nothing
        if 'connected_website' in message:
            return

        if 'forward_from_chat' in message:
            if message['forward_from_chat']['type'] == 'channel':
                forward_from_chat_id = message['forward_from_chat']['id']
                success, admins = self.get_chat_administrators(forward_from_chat_id)
                user_found = False

                if success:
                    for admin in admins['result']:
                        if admin['user']['id'] == user_id:
                            user_found = True
                            break
                if not user_found:
                    return

                is_from_channel = True

        if is_from_channel:
            channel_data = message['forward_from_chat']
            channel_data['user'] = self._user

            self.create_channel(channel_data)
            reply_message = channel_added_message.format(channel_title=channel_data['title'])
            menu = [
                [
                    dict(
                        text=open_dashboard,
                        login_url=self.login_url()
                    )
                ]
            ]

            reply_markup = dict(inline_keyboard=menu)

        else:
            reply_message = start_message.format(bot_username=settings.BOT_USERNAME)

        self.send_telegram_message(message=reply_message, chat_id=chat_id, reply_markup=reply_markup)

    def handle_callback_query(self, request_json):

        """
        :param request_json: The request json from Telegram received through our webhook
              This method will handle the case of requests received when  a user clicks any of the inline buttons
        :return:
        """

        reply_markup = None
        message_id = request_json['callback_query']['message']['message_id']
        callback_query_id = request_json['callback_query']['id']
        channel_data = request_json['callback_query']['message']['chat']
        chat_id = channel_data['id']
        callback_data = request_json['callback_query']['data']

        from_ = request_json['callback_query']['from']
        self.create_user(from_)

        if 'button_id' in callback_data:
            button_id = json.loads(callback_data)['button_id']
            post_id = json.loads(callback_data)['post_id']
            button = Button.objects.filter(id=button_id).first()

            self.create_channel(channel_data)
            button_click = ButtonClick.objects.filter(click_button=button, click_channel=self.channel,
                                                      user=self._user).first()

            if button_click:
                button_click.delete()
                self.answer_callback_query(
                    callback_query_id=callback_query_id,
                    text=reaction_removed_message.format(
                        emoji=button.button_emoji.emoji
                    )
                )

            else:
                ButtonClick.objects.create(click_button=button, click_channel=self.channel, user=self._user)
                dashboard_notification = DashboardNotification.objects.create(
                    user=self._user,
                    notification_channel=self.channel,
                    emoji=button.button_emoji.emoji
                )
                send_dashboard_notification.delay(dashboard_notification.id)

                self.answer_callback_query(
                    callback_query_id=callback_query_id,
                    text=reaction_added_message.format(
                        emoji=button.button_emoji.emoji
                    )
                )

            send_post_buttons_menu.delay(post_id=post_id, chat_id=chat_id, message_id=message_id)
            return

        elif 'subscribe_post_id' in callback_data:
            post_id = json.loads(callback_data)['subscribe_post_id']
            reply_markup = request_json['callback_query']['message']['reply_markup']

            post = Post.objects.filter(id=post_id).first()

            if post:
                subscription = PostSubscription.objects.filter(post=post, user=self._user).first()
                if subscription:
                    subscription.delete()
                    reply_markup['inline_keyboard'][-1][0] = dict(
                        text=subscribe,
                        callback_data=json.dumps(
                            dict(
                                subscribe_post_id=post.id
                            )
                        )
                    )

                else:
                    PostSubscription.objects.create(post=post, user=self._user)
                    reply_markup['inline_keyboard'][-1][0] = dict(
                        text=unsubscribe,
                        callback_data=json.dumps(
                            dict(
                                subscribe_post_id=post.id
                            )
                        )
                    )

        self.edit_message_reply_markup(chat_id, message_id,
                                       reply_markup=reply_markup)

    def handle_channel_post(self, request_json):

        """

        All the messages received from a channel will be treated as a new post

        :param request_json: request data received from telegram
        :return:
        """
        chat_id = request_json['channel_post']['chat']['id']
        message_id = request_json['channel_post']['message_id']

        text = None
        image_url = None
        caption = None
        has_video = False
        entities = None
        caption_entities = None

        if 'text' in request_json['channel_post']:
            text = request_json['channel_post']['text']

        if 'caption' in request_json['channel_post']:
            caption = request_json['channel_post']['caption']

        if 'caption_entities' in request_json['channel_post']:
            caption_entities = request_json['channel_post']['caption_entities']

        if 'entities' in request_json['channel_post']:
            entities = request_json['channel_post']['entities']

        if 'photo' in request_json['channel_post']:
            file_id = request_json['channel_post']['photo'][-1]['file_id']
            res = self.get_file(file_id)

            file_path = res['result']['file_path']

            image_url = f'https://api.telegram.org/file/bot{settings.BOT_TOKEN}/{file_path}'

        if 'video' in request_json['channel_post']:
            has_video = True

        channel_data = request_json['channel_post']['chat']
        channel_data['user'] = self._user

        self.create_channel(channel_data)
        post_url = f'https://t.me/{self.channel.username}/{message_id}'

        post = Post.objects.create(
            post_channel=self.channel,
            text=text,
            post_url=post_url,
            caption=caption,
            has_video=has_video
        )

        send_post_buttons_menu.delay(post_id=post.id, chat_id=chat_id, message_id=message_id)
        if image_url:
            download_post_image.delay(url=image_url, post_id=post.id)

        parse_post_text(post_id=post.id, entities=entities, caption_entities=caption_entities)

    def process_telegram_request(self, request_json):
        """
        This method receives the request_json sent to our web hook by telegram
        It will then extract all the required information to send the appropriate reply to the user
        :param request_json:
        :return:
        """

        if 'message' in request_json:
            self.handle_message(request_json)

        if 'channel_post' in request_json:
            self.handle_channel_post(request_json)

        if 'callback_query' in request_json:
            self.handle_callback_query(request_json)
