from django.utils import timezone
from django.core.files import File

from celery import shared_task
from users.models import User

import requests
from io import BytesIO


@shared_task # @shared_task 是 `Celery` 的寫法, 可用來做 delayed 呼叫, 慢慢地在 background 做 (?) 的樣子
def download_user_image(user_id): #用來把user的telegram profile image download下來, 存到db && s3(?)
    user, _ = User.objects.get_or_create(telegram_id=user_id)

    if user:
        if user.photo_url:
            print("Download user image because user.photo_url != user.previous_photo_url")
            try:
                # 下載當下最新的 photo_url
                response = requests.get(user.photo_url)
            except Exception as e:
                print(e)
                return
            buffer = BytesIO(response.content)

            image_name = f"user_image_{user.telegram_id}_{timezone.now().timestamp()}.jpg"
            user.photo.save(image_name, File(buffer))
            user.save()
            buffer.close()

