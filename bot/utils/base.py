import requests
from django.conf import settings


class Base:
    """
    This is the base class mainly used to telegram API calls
    """

    def __init__(self, token=None):
        self.token = token if token else settings.BOT_TOKEN
        self._user = None
        self.channel = None

    @staticmethod
    def create_buttons(buttons, n_cols):
        """
        :param buttons: A list of telegram button objects
        :param n_cols: The number of buttons per row
        :return:
           A 2D array representing a telegram menu object
        """
        menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]

        return menu

    def login_url(self, redirect=None):
        """
        generates a login url for our bot

        :return
        """

        url = f"{settings.BASE_URL}/telegram_login?token={self.channel.token}"

        if redirect:
            url = f"{url}&redirect={redirect}"

        login_url = dict(
            url=url,
            bot_username=settings.BOT_USERNAME,
            request_write_access=True
        )

        return login_url

    def set_webhook(self, webhook_url, token):

        """
        :param webhook_url: The webhook url to be set
        :param token: The token of the bot whose webhook is being set
        :return:
        """
        method = 'setWebhook'
        url = self.build_telegram_api_url(token, method)

        data = dict(
            url=webhook_url
        )
        requests.post(url, json=data)

    def answer_callback_query(self, callback_query_id, text):

        data = dict(
            text=text,
            callback_query_id=callback_query_id
        )

        method = "answerCallbackQuery"
        url = self.build_telegram_api_url(self.token, method)
        response = requests.post(url, json=data)

        return response.status_code == 200, response.json()

    def send_document(self, chat_id, file_id):

        """
        :param chat_id
        :param file_id
        :return:
           bool: true if response.status_code is 200
           json: The json response from telegram API
        """

        message_data = dict(
            chat_id=chat_id,
            document=file_id
        )

        method = "sendDocument"
        url = self.build_telegram_api_url(self.token, method)
        response = requests.post(url, json=message_data)
        return response.status_code == 200, response.json()

    def forward_telegram_message(self, chat_id, from_chat_id, message_id):

        """
        :param chat_id:
        :param from_chat_id:
        :param message_id:
        :return:
            bool: true if response.status_code is 200
            json: The json response from telegram API
        """
        message_data = dict(
            chat_id=chat_id,
            from_chat_id=from_chat_id,
            message_id=message_id
        )

        method = 'forwardMessage'
        url = self.build_telegram_api_url(self.token, method)

        response = requests.post(url, json=message_data)

        return response.status_code == 200, response.json()

    def edit_message_reply_markup(self, chat_id, message_id, reply_markup=None):
        """
        :param chat_id:
        :param message_id:
        :param text:
        :param reply_markup:
        :return:
            bool: true if response.status_code is 200
            json: The json response from telegram API
        """

        message_data = dict(
            chat_id=chat_id,
            message_id=message_id
        )

        if reply_markup:
            message_data.update(
                dict(
                    reply_markup=reply_markup
                )
            )

        method = "editMessageReplyMarkup"

        url = self.build_telegram_api_url(self.token, method)
        response = requests.post(url, json=message_data)

        return response.status_code == 200, response.json()

    def edit_message_text(self, chat_id, message_id, text, reply_markup=None):
        """
        :param chat_id:
        :param message_id:
        :param text:
        :return:
        """

        message_data = dict(
            chat_id=chat_id,
            message_id=message_id,
            text=text,
            parse_mode='HTML'
        )

        if reply_markup:
            message_data.update(
                dict(
                    reply_markup=reply_markup
                )
            )

        method = "editMessageText"

        url = self.build_telegram_api_url(self.token, method)
        response = requests.post(url, json=message_data)

        return response.status_code == 200, response.json()

    def send_telegram_message(self, chat_id, message, reply_markup=None):
        """
        This method calls the send_message method of python telegram package thus sending a message
        to the corresponding user
        :param recipient_id:
        :param chat_id:
        :param message:
        :param reply_markup
        :return:
            bool: true if response.status_code is 200
            json: The json response from telegram API
        """

        message_data = dict(
            chat_id=chat_id,
            text=message,
            parse_mode='HTML'
        )

        if reply_markup:
            message_data.update(
                dict(
                    reply_markup=reply_markup
                )
            )

        method = "sendMessage"
        url = self.build_telegram_api_url(self.token, method)

        response = requests.post(url, json=message_data)

        return response.status_code == 200, response.json()

    def get_me(self, token):

        """
        :param token:
        Gets the details of a bot with the give token
        :return:
           json: json response from telegram API
        """

        method = 'getMe'
        url = self.build_telegram_api_url(token=token, method=method)
        response = requests.get(url)
        return response.json()

    def get_file(self, file_id):

        """

        :param file_id:
        :return:
        """

        params = dict(
            file_id=file_id
        )
        method = 'getFile'
        url = self.build_telegram_api_url(self.token, method)
        response = requests.get(url, params=params)

        return response.json()

    def get_chat_administrators(self, chat_id):

        """
        Gets administrators of a given chat.
        In our case we are mainly interested in the channels.

        :param chat_id:
        :return:
        """
        method = 'getChatAdministrators'
        params = dict(
            chat_id=chat_id
        )

        url = self.build_telegram_api_url(self.token, method)
        response = requests.get(url, params=params)
        return response.status_code == 200, response.json()

    @staticmethod
    def build_telegram_api_url(token, method):

        """
        :param token:
        :param method:
        builds a telegram API url from the give token and method.
        :return:
           url: A telegram API url
        """

        return f"https://api.telegram.org/bot{token}/{method}"
