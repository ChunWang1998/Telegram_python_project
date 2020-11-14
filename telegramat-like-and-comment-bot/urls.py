"""telegramat-like-and-comment-bot URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
import bot.views as bot_views
import users.views as user_views
# add
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "telegramat-like-and-comment-bot.settings")
django.setup()
#

urlpatterns = [
    path('admin/', admin.site.urls),
    path('webhook/<str:token>', bot_views.Webhook.as_view(), name='webhook'),
    path('telegram_login', user_views.TelegramLogin.as_view(), name='telegram-login'),
    path('telegram_login_required', user_views.TelegramLoginRequired.as_view(), name='telegram-login-required'),
    path('logout', user_views.Logout.as_view(), name='telegram-logout'),
    path('', bot_views.Home.as_view(), name="home"),
    path('get_charts_data', bot_views.GetChartsData.as_view(), name='get-charts-data'),
    path('channels', bot_views.ChannelsList.as_view(), name='channel-list'),
    path('posts', bot_views.PostList.as_view(), name='post-list'),
    path('channel_emoji_edit', bot_views.ChannelEmojiEdit.as_view(), name='channel-emoji-edit'),
    path('comments/<int:post_id>', bot_views.Comments.as_view(), name='comments-list'),
    path('pre_comment_form/<int:comment_id>', bot_views.PreCommentForm.as_view(), name="pre-comment-form"),
    path('comments/retrieve/<int:comment_id>', bot_views.CommentsDetail.as_view(), name='comment-detail'),
    path('subscribe/<int:user_id>/<int:post_id>', bot_views.Subscribe.as_view(), name='subscribe')
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
