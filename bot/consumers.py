from django.template.loader import render_to_string
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer

from bot.models import Post, Comment, CommentLike
from bot.tasks import send_comment_notification

import json

"""
This is a django-channels' consumer that handles all the comment actions.
用來接收來自 JS/AJAX的 "sockets"... 並非 http request 喔!
"""


class CommentConsumer(WebsocketConsumer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.group_name = None
        self.user = None
        self.post_id = None
        self.parent_id = None

    def connect(self):

        # receives a websocket connection and adds ito  a the specific post comments group
        route_kwargs = self.scope['url_route']['kwargs']

        self.post_id = route_kwargs.get('post_id', None)
        self.group_name = f'post-{self.post_id}'
        self.user = self.scope['user']

        async_to_sync(self.channel_layer.group_add)(
            self.group_name,
            self.channel_name
        )

        self.accept()

    def disconnect(self, code):

        # disconnects a given connection

        async_to_sync(self.channel_layer.group_discard)(
            self.group_name,
            self.channel_name
        )

    def handle_comment_edit(self, data):

        # this method handle the editing of a given comment

        comment_text = data.get('comment', None)
        comment_editing_id = data.get('comment_editing_id', None)
        comment = Comment.objects.filter(id=comment_editing_id).first()
        comment.text = comment_text
        comment.save()

        if comment.parent:
            template = 'bot/comment_reply.html'

        else:
            template = 'bot/comment.html'

        html = render_to_string(template, context=dict(comment=comment, post=comment.comment_post, user=self.user))
        async_to_sync(self.channel_layer.group_send)(
            self.group_name,
            dict(
                comment_id=comment_editing_id,
                html=html,
                type='edit_comment'
            )
        )

    # 創建 new comment (好像不論 new comment 還是 reply-to comment)
    def handle_comment_create(self, data):

        # this method handles the creation of a given comment

        comment_text = data.get('comment', None)
        parent_id = data.get('parent_id', None)
        comment_editing_id = data.get('comment_editing_id', None)

        post = Post.objects.filter(id=self.post_id).first()

        if comment_editing_id:
            self.handle_comment_edit(data)
            return

        else:
            if parent_id:
                parent = Comment.objects.filter(id=parent_id).first()

            else:
                parent = None

            comment = Comment.objects.create(
                user=self.user,
                comment_post=post,
                text=comment_text,
                parent=parent
            )

            send_comment_notification.delay(comment.id)

        # 最後好像會去把下面的 function (依照type裡面塞的name)去回覆給js那邊, 讓js能夠基於結果去manipulate template content...
        async_to_sync(self.channel_layer.group_send)(
            self.group_name,
            dict(
                comment_id=comment.id,
                comments_count=post.comments.count(),
                type='create_comment'
            )
        )

    def handle_comment_like(self, data):

        # This method handles the liking of a given comment

        comment_id = data.get('comment_id', None)

        comment = Comment.objects.filter(id=comment_id).first()
        comment_like = CommentLike.objects.filter(
            comment=comment,
            user=self.user
        ).first()

        if comment_like:
            comment_like.delete()

        else:
            self.create = CommentLike.objects.create(comment=comment, user=self.user)

        if comment.parent:
            template = 'bot/comment_reply.html'

        else:
            template = 'bot/comment.html'

        html = render_to_string(template, context=dict(comment=comment, post=comment.comment_post, user=self.user))

        async_to_sync(self.channel_layer.group_send)(
            self.group_name,
            dict(
                html=html,
                comment_id=comment_id,
                type='like_comment'
            )

        )

    def handle_comment_delete(self, data):

        # This method handles the deletion of a given comment

        comment_id = data.get('comment_id', None)

        if comment_id:
            comment = Comment.objects.filter(id=comment_id).first()
            if comment:
                comment.delete()

        async_to_sync(self.channel_layer.group_send)(
            self.group_name,
            dict(
                comment_id=comment_id,
                type='delete_comment'
            )
        )

    # root handler, 落腳處, 再轉發給各handler
    def receive(self, text_data=None, bytes_data=None):

        # This method receives websocket events and triggers the relevant action
        if text_data:
            data = json.loads(text_data)
            action_type = data['action_type']

            if action_type == 'comment_create':
                self.handle_comment_create(data)

            elif action_type == 'comment_like':
                self.handle_comment_like(data)

            elif action_type == 'comment_delete':
                self.handle_comment_delete(data)

    def create_comment(self, event):

        # dispatched after comment creation
        self.send(text_data=json.dumps(
            dict(
                comment_id=event['comment_id'
                                 ''
                                 ''],
                type=event['type'],
                comments_count=event['comments_count']
            )
        ))

    def delete_comment(self, event):

        # dispatched after comment deletion
        self.send(
            text_data=json.dumps(
                dict(
                    comment_id=event['comment_id'],
                    type=event['type']
                )
            )
        )

    def like_comment(self, event):

        # dispatched after comment like
        self.send(
            text_data=json.dumps(
                dict(
                    html=event['html'],
                    comment_id=event['comment_id'],
                    type=event['type']
                )
            )
        )

    def edit_comment(self, event):

        # dispatched after comment edit

        self.send(
            json.dumps(
                dict(
                    html=event['html'],
                    comment_id=event['comment_id'],
                    type=event['type']
                )
            )
        )


class NotificationConsumer(WebsocketConsumer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None
        self.group_name = None

    def connect(self):
        self.group_name = "like-com-notifications"

        async_to_sync(self.channel_layer.group_add)(
            self.group_name,
            self.channel_name
        )

        self.accept()

    def disconnect(self, code):
        print(code)
        self.close()

    def send_dashboard_notification(self, event):
        self.send(
            text_data=json.dumps(
                dict(
                    type=event['type'],
                    text=event['text']
                )
            )
        )
