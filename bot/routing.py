from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/comments/(?P<post_id>\d+)', consumers.CommentConsumer),
    re_path(r'ws/like_com_notifications', consumers.NotificationConsumer)
]
