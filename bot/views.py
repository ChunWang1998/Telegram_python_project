from django.shortcuts import render, get_object_or_404
from django.template.loader import render_to_string
from django.db.models import Count
from django.urls import reverse
from django.db.models.functions import TruncDay
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.views.generic import View
from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from bot.utils.livecom_utils import LiveCom
from bot.models import Button, ButtonEmoji, Post, Comment, PostSubscription
from users.models import User
from bot.mixins import BotMixin
from bot.utils.str_utils import *
from itertools import chain

import json

live_com = LiveCom()


class Home(BotMixin, View):

    def get(self, request):
        context = dict()
        user = request.user
        start_date, end_date = self.get_dates(request)

        if request.user.is_authenticated:
            channels_data = list()
            numbers = [one, two, three]

            channels = user.channels.filter(date_created__gte=start_date, date_created__lte=end_date).order_by('-id')

            for channel in channels:
                channels_data.append(
                    channel.get_data()
                )

            context['channels_data'] = channels_data

            posts_data = list()

            posts = user.posts.filter(date_created__gte=start_date, date_created__lte=end_date).order_by('-id')[:10]

            for post in posts:
                posts_data.append(
                    post.get_data()
                )

            context['posts_data'] = posts_data

            summary_data = list()
            for i in range(3):
                buttons = Button.objects.filter(date_created__gte=start_date, date_created__lte=end_date).order_by('id')
                button_clicks_count = buttons.filter(
                    button_emoji__emoji_type=i + 1
                ).aggregate(
                    clicks_count=Count('clicks__id')
                )['clicks_count']

                summary_data.append(
                    (
                        f'{button} {numbers[i]}', button_clicks_count
                    )
                )

            context['summary_data'] = summary_data

        else:
            return HttpResponseRedirect(reverse('telegram-login-required'))

        return render(request, 'bot/home.html', context)


class ChannelsList(View):

    def get(self, request):
        if request.user.is_authenticated:
            channels = request.user.channels.order_by('-id')
            context = dict()
            context['channels'] = channels
            return render(request, "bot/channel_list.html", context=context)

        else:
            return HttpResponseRedirect(reverse('telegram-login-required'))


class ChannelEmojiEdit(View):

    def post(self, request):
        for key in request.POST:
            value = request.POST[key]
            id = int(key.split('-')[-1])

            button_emoji = ButtonEmoji.objects.filter(id=id).first()
            if button_emoji:
                button_emoji.emoji = value
                button_emoji.save()

        return JsonResponse(
            dict(
                success=True,
                message="Update successfully"
            )
        )


class PostList(View):
    def get(self, request):

        channel_id = request.GET.get('channel-id', None)
        post_id = request.GET.get('post-id', None)
        page_number = request.GET.get('page_number', '1')

        if page_number.isdigit():
            page_number = int(page_number)

        else:
            page_number = 1

        if request.user.is_authenticated:
            posts = request.user.posts.order_by('-id')
            context = dict()

            if post_id:
                posts = posts.filter(id=post_id)

            if channel_id:
                posts = posts.filter(post_channel__id=channel_id)

            paginator = Paginator(posts, 20)
            page_number = min(page_number, paginator.num_pages)
            posts = paginator.page(page_number)

            if page_number < 10:
                pages = [_ for _ in range(1, min(11, paginator.num_pages))]

            elif page_number + 10 > paginator.num_pages:
                pages = [_ for _ in range(page_number, paginator.num_pages + 1)]

            else:
                pages = [_ for _ in range(page_number - 5, page_number + 5)]

            context['page_number'] = page_number
            context['pages'] = pages
            context['has_next'] = posts.has_next()
            if(context['has_next']):
                context['next_page'] = page_number + 1
            context['has_previous'] = posts.has_previous()
            if(context['has_previous']):
                context['previous_page'] = page_number - 1
            context['posts_data'] = [post.get_minimal_data() for post in posts]
            context['channels'] = request.user.channels.values('id', 'title')
            return render(request, 'bot/post_list.html', context=context)

        else:
            return HttpResponseRedirect(reverse('telegram-login-required'))


class GetChartsData(BotMixin, View):

    @staticmethod
    def get_data(button_clicks):
        return dict(
            data=[button_click['clicks_count'] for button_click in button_clicks],
            labels=[button_click['day'].timestamp() * 1000 for button_click in button_clicks]
        )

    def get_charts_data(self, start_date, end_date):
        charts_data = dict()
        numbers = ["one", "two", "three"]

        buttons = Button.objects.filter(clicks__isnull=False).filter(clicks__date_created__gte=start_date,
                                                                     clicks__date_created__lte=end_date)
        button_clicks = buttons.annotate(day=TruncDay('clicks__date_created')).values('day').annotate(
            clicks_count=Count('clicks__id')).order_by('day').values('clicks_count', 'day')

        charts_data["all_buttons"] = self.get_data(button_clicks)

        for i in range(3):
            filtered_button_clicks = button_clicks.filter(button_emoji__emoji_type=i + 1)
            charts_data[f"button_{numbers[i]}"] = self.get_data(filtered_button_clicks)

        return charts_data

    def get(self, request):
        start_date, end_date = self.get_dates(request)
        return JsonResponse(self.get_charts_data(start_date, end_date))


class CommentsDetail(View):

    def get(self, request, comment_id):
        comment = Comment.objects.filter(id=comment_id).first()

        if comment:
            context = dict(
                user=request.user,
                comment=comment,
                post=comment.comment_post
            )
            if comment.parent:
                html = render_to_string("bot/comment_reply.html", context=context)

            else:
                html = render_to_string("bot/comment.html", context=context)

            return JsonResponse(
                dict(
                    success=True,
                    html=html
                )
            )

        else:
            return JsonResponse(
                dict(
                    success=False,
                    message=comment_not_found
                )
            )


class Comments(View):

    def get(self, request, post_id):
        num_to_show = request.GET.get('num_to_show', '5')
        post = get_object_or_404(Post, id=post_id)
        all_comments = post.comments.order_by('id')

        comments_count = all_comments.count()
        num_to_show = int(num_to_show) if num_to_show.isdigit() else 5
        remaining_count = comments_count - num_to_show

        has_next = remaining_count > 0

        if remaining_count < 50:
            pagination_text = show_all_comments

        else:
            pagination_text = show_remaining_comments.format(remaining_count=remaining_count)

        last_index = comments_count - max(0, num_to_show - 50)
        start_index = max(0, last_index - num_to_show)
        comments = all_comments[start_index:last_index]
        num_to_show = num_to_show + 50

        if request.is_ajax():
            show_all = request.GET.get('show_all', None)
            if show_all and show_all == '1':
                comments = all_comments

            data_url = reverse('comments-list', kwargs=dict(post_id=post.id))
            data_url = f"{data_url}?num_to_show={num_to_show}"
            context = dict(
                comments=comments,
                post=post
            )
            html = render_to_string("bot/comments_list.html", request=request, context=context)
            return JsonResponse(
                dict(
                    data_url=data_url,
                    html=html,
                    pagination_text=pagination_text,
                    has_next=has_next
                )
            )

        else:
            login_url = reverse('telegram-login')
            comments_url = reverse('comments-list', kwargs=dict(post_id=post.id))

            context = dict(
                comments=comments,
                num_to_show=num_to_show,
                comments_count=comments_count,
                post=post,
                pagination_text=pagination_text,
                has_next=has_next,
                redirect_url=f"{settings.BASE_URL}{login_url}?redirect={comments_url}",
                bot_username=settings.BOT_USERNAME
            )
            return render(request, "bot/post_comments.html", context)


class PreCommentForm(View):
    def get(self, request, comment_id):
        comment = Comment.objects.filter(id=comment_id).first()

        if comment:
            return JsonResponse(
                dict(
                    success=True,
                    html=render_to_string('bot/pre_comment_form.html', context=dict(comment=comment)),
                    text=comment.text
                )
            )

        else:
            return JsonResponse(
                dict(
                    success=False,
                    message=comment_not_found
                )
            )


class Subscribe(View):

    def get(self, request, user_id, post_id):

        subscription = PostSubscription.objects.filter(post_id=post_id, user__telegram_id=user_id).first()

        if subscription:
            subscription.delete()
            return JsonResponse(
                dict(
                    success=True,
                    button_text=subscribe,
                    message=successful_unsubscription
                )
            )

        else:
            user = User.objects.filter(telegram_id=user_id).first()
            post = Post.objects.filter(id=post_id).first()

            if user and post:
                PostSubscription.objects.create(
                    user=user,
                    post=post
                )

                return JsonResponse(
                    dict(
                        success=False,
                        button_text=unsubscribe,
                        message=successful_subscription
                    )
                )

            else:
                return JsonResponse(
                    dict(
                        success=False,
                        message=something_went_wrong
                    )
                )


class Webhook(View):

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    @staticmethod
    def post(request, token):
        if token != settings.BOT_TOKEN:
            return HttpResponse(status=403)

        request_json = json.loads(request.body.decode('utf-8'))
        live_com.process_telegram_request(request_json)

        return HttpResponse(status=200)
