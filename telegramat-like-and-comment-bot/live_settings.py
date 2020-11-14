import os
import dj_database_url

ALLOWED_HOSTS = ['telegramat-lac.herokuapp.com']
BOT_TOKEN = os.environ.get('BOT_TOKEN')
BASE_URL = os.environ.get('BASE_URL')
BOT_USERNAME = os.environ.get('BOT_USERNAME')
DEBUG = int(os.environ.get('DEBUG', 0))
print(BOT_TOKEN)
print("d")
db_from_env = dj_database_url.config()
DATABASES = dict(default=db_from_env)

'''
好像這樣寫就可以利用AWS的S3 storage了...!! 只要給他這些資訊就行
Amazon S3 — django-storages 1.9.1 documentation
https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html
'''
# 設定credentials etc.
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
AWS_DEFAULT_ACL = 'public-read'
# 告訴Django我們要吃s3
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [os.environ.get('REDIS_URL', 'redis://localhost:6379')],
        },
    },
}

CELERY_BROKER_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379')
CELERY_RESULT_BACKEND = os.environ.get('REDIS_URL', 'redis://localhost:6379')
