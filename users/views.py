from django.shortcuts import render, get_object_or_404
from django.views import View
from django.http.response import HttpResponse, HttpResponseRedirect
from django.conf import settings
from django.contrib.auth import login, logout
from django.urls import reverse

from bot.models import Channel
from users.models import User
from users.authentication import TelegramAuthentication
from users.utils import generate_user_colors
from users.tasks import download_user_image

telegram_authentication = TelegramAuthentication()


class TelegramLogin(View):
    def get(self, request):
        # ============= 整理 req. data ==================
        telegram_id = request.GET.get('id', None)
        first_name = request.GET.get('first_name', None)
        last_name = request.GET.get('last_name', None)
        username = request.GET.get('username', None)
        auth_date = request.GET.get('auth_date', None)
        telegram_hash = request.GET.get('hash', None)
        channel_token = request.GET.get('token', None)
        photo_url = request.GET.get('photo_url', None)

        request_data = dict(
            first_name=first_name if first_name else '',
            hash=telegram_hash if telegram_hash else '',
            id=telegram_id if telegram_id else ''
        )

        if username:
            request_data.update(dict(username=username))

        if photo_url:
            request_data.update(dict(photo_url=photo_url))

        if last_name:
            request_data.update(dict(last_name=last_name))

        if auth_date:
            request_data.update(dict(auth_date=auth_date))

        # =========== 確認 telegram auth 成功沒出錯... ============
        telegram_authentication.verify_telegram_authentication(
            bot_token=settings.BOT_TOKEN,
            request_data=request_data
        )

        # 從 table 中撈出 user, 若本來沒user的話就 create 一個
        # 這個id是unique, 同時也是bot的chat_id, 也是我們user table 中拿來當作 PK Primary Key
        user, _ = User.objects.get_or_create(telegram_id=telegram_id)

        # 更新 photo_url & last photo_url--每次都更新 (每次都檢查是否有更換usr pic)
        user.previous_photo_url = user.photo_url # 把原本的 url 做更新
        user.photo_url = photo_url
        # 基於 user 的 user.previous_photo_url, user.photo_url 判斷現在應該怎麼塞 `user.photo`
        # 若根本沒photo
        should_download_usr_profile_img = False
        if (user.photo_url == None):
            if(user.photo != None):
                user.photo = None  # 若沒有的話欄位會填寫 None... 採用預設的 寫名字的那種圖
        # 若本次login是有換過photo, 或是首次登入..
        elif (user.photo_url != user.previous_photo_url):
            # 利用 telegram_id 去把 user profile download 下來自己存 (避免 telegram 那邊有時撈 user profile picture 會撈不到...)
            # 撈到以後會直接存到 user obj 當中...
            should_download_usr_profile_img = True

        # username 就是 telegram user 可以自己自己亂改的那個 username, 注意這個是會變動的; 若它沒有設就幫他設一個
        # 注意這不是 primary key
        if not username:
            username = f"{first_name.lower()}_{last_name.lower()}"
        user_data = dict(
            username=username,
            first_name=first_name,
            last_name=last_name,
            photo_url=photo_url
        )
        # 把上面的其他資訊都一一塞到 user obj 中
        for key, value in user_data.items():
            setattr(user, key, value)

        user.save()

        if(should_download_usr_profile_img):
            download_user_image.delay(user.telegram_id) # 注意需在上面的 obj UPDATE 之後才能做!

        # 利用 Django module 做 login!
        login(request, user)

        channel = Channel.objects.filter(token=channel_token).first()

        if channel:
            user.channels.add(channel)
            generate_user_colors(user=user, channel=channel)

        # 轉到 dashboard (管理員後台) 去~
        redirect = request.GET.get('redirect', reverse('home'))

        return HttpResponseRedirect(redirect)


class TelegramLoginRequired(View):

    def get(self, request):
        return render(request, 'bot/nologin.html')

class Logout(View):

    def get(self, request):
        logout(request)
        redirect = request.GET.get('redirect', reverse('telegram-login-required'))
        return HttpResponseRedirect(redirect)
