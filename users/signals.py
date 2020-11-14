# 2020-05-30 這個好像沒用, Joseph 把它關掉了不知道為什麼...

# from django.db.models.signals import post_save
#
# from users.models import User
# from users.tasks import download_user_image
#
#
# def user_post_save_actions(sender, instance, **kwargs):
#     post_save.disconnect(user_post_save_actions, sender=sender)
#
#     if instance.photo_url:
#         if instance.photo_url != instance.previous_photo_url:
#             download_user_image(instance.telegram_id)
#
#     else:
#         instance.photo = None
#         instance.save()
#
#     post_save.connect(user_post_save_actions, sender=sender)
#
#
# post_save.connect(user_post_save_actions, sender=User)
