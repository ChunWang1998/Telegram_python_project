# telegramat-like-and-comment-bot-code

This is a clone for telegram-like-and-comment-bot

## Running it Locally

To run the project locally follow the following steps. 

+ Create a `local_settings.py` inside the `telegram-like-and-comment-bot` directory. This will mainly contain configurations required
to run the project locally. A sample `local_settings.py` is as follows:

```
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BOT_TOKEN = '<bot_token>'
BASE_URL = '<ngrok_url>'
BOT_USERNAME = '<bot_username>'
ALLOWED_HOSTS = ['*']

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("127.0.0.1", 6379)],
        },
    },
}

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'bot', 'static'),
)

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

CELERY_BROKER_URL = 'redis://localhost:6379'
CELERY_RESULT_BACKEND = 'redis://localhost:6379'

```

+ Enable virtual environment. Pipenv(https://github.com/pypa/pipenv) is being used to manage dependencies. With pipenv installed, 
run the following command to create and enable a virtual environment

```
    pipenv shell
```

+ Install dependencies. 

```
    pipenv install
```

+ Make database migrations (建立DB; migrate executes those SQL commands in the database file. So after executing migrate all the tables of your installed apps are created in your database file.)

```
    python manage.py migrate
```


+ Finally you have to spin up the server. (跟 Django 講要把webserver run起來)
```
    python manage.py runserver
```

+ Setup webhooks by running this command (手動run script, run的是 /scripts/set_webhooks.py): 

```
   python manage.py runscript set_webhook
```

In case you decide to go with ngrok for https,

```
   ./ngrok http 8000
```

Use the above generated https URL in `local_settings.py`


Long running tasks are being ran in the background using celery. Redis is on the other hand handle the 
message queuing. To be able to run celery you have to install redis for your specific operating system. 

Once redis is installed, you first have to install celery as follow:

```
pip install celery
```

With Celery installed, you can now start it on a new terminal as follow:

```
celery -A telegramat-like-and-comment-bot worker -l info
```

###### enable telegram login
+ Should go to BotFather and add your domain (e.g., https://telegramat-lac.herokuapp.com) to `/setdomain` for your telegram bot in order to enable telegram login to your domain.
+ 注意!! 此功能需有 HTTPS 才能用  

## Notes

The most important part of the code is bot/utils, There are three files in there.
+ `livecom_utils.py` - Contains the logic for handling bot & channel messages. 
+ `base.py` - Contains the base code that mainly API calls to Telegram

The rest of the code follows django standard structure. 

For the project to run smoothly you need to have redis installed and running on your local machine

You also need to set the domain of the bot using `BotFather` to the ngrok url above.


## Deployment to heroku
### Prerequisite

+ Install Redis addon on Heroku (this is used for DB caching)
+ Setup an AWS S3 bucket (this is used for storing multimedia ourselves, to increase stability of the post pages.)

### Start Deployment

+ Deployment on Heroku happens through github so it is easy as button click to deploy. 

+ After" "Heroku deployment of the "App", you need to set the required environment variables.

| Variable | Description |
| -------- | ----------- |
| AWS_ACCESS_KEY_ID |   AWS IAM user's KEY ID  (e.g., AKIA...) |
| AWS_SECRET_ACCESS_KEY | AWS IAM user's Access Key (e.g., azAj2...)  |
| AWS_STORAGE_BUCKET_NAME | AWS storage bucket name (e.g., telegramat-like-comment)  |
| BASE_URL                | The base url for your application (e.g., https://telegramat-lac.herokuapp.com)  |
| BOT_TOKEN               | Telegram Bot Token from Bot Father (e.g., 1221641866:AAE...) |
| BOT_USERNAME            | Telegram Bot Username (e.g., tashengon_like_bot)  |
| DATABASE_URL            | (no need, Heroku will add it automatically)Database URL (e.g., postgres://galzbmgaidkruu:52c00d91fbc092221ee30177902612b35f3383683d68403d2f0b95c2e16bdd7c@ec2-52-6-143-153.compute-1.amazonaws.com:5432/d383ltvoj52gp0) |
| DEBUG                   | DEBUG(Should always be 0)   |
| REDIS_URL               |  (no need, Heroku will add it automatically after you install the Heroku Redis AddsOn)Redis URL (e.g., redis://h:p915ac75bb8be2380bda1fb4b952eede756f8c9865c6fc8e74133a7debb780b5f@ec2-3-224-74-102.compute-1.amazonaws.com:22059) |


+ With the environment variables above set, run the following Heroku commands:

###### db migration
```
heroku run python manage.py migrate --app <app_name>
```

###### set app's webbook
```
heroku run python manage.py runscript set_webhook --app=<app_name>
(P.S. run 就是只跑一次的那種command)
```

###### scale dyno for web app
```
heroku ps: scale web=1 --app <app_name>
(P.S. ps:scale 通常用來跑像是service那種跑不完的東西為了要能夠scale用的, =[N] 其中 N 代表的就是啟用的 dyno 數 (用來scale用的...) )
(P.S. `web` is defined in `Procfile`)
```

###### scale script to process background tasks
```
heroku ps: scale process_background_tasks=1 --app <app_name>
(P.S. `process_background_tasks` is defined in `Procfile`)
```

###### enable telegram login
Should go to BotFather and add your BASE_URL (e.g., https://telegramat-lac.herokuapp.com) to `/setdomain` for your telegram bot in order to enable telegram login to your domain. 


## Code Trace (2020/05從Joseph那裏承接時的狀態)
* 基於 Django 做到 frontend (PO文pages, DashBoard pages), backend & http server management (為了讓 telegram 可以 webhook 的方式傳遞訊息過來)
* (若要在local端run)基於外掛 ngrok 來做到 https 的 tunneling 
* `Pipfile` and `Pipfile.lock`: pipenv (virtual env. 管理程式, 類似 anaconda) 要看的類似 Javascript 的 package.json 的套件清單, pipenv 會基於他做必要的套件安裝
* `manage.py`: Django 的起始點, 從這邊打指令帶起 Django 的其他 components
* `db.sqlite3`: DB 資料都是寫到這邊
* `likecombot\*` - 放置一些settings, 最basic的地方 
* `likecombot\settings.py`: Django 的 settings, 但不常需要改動 (`SECRET_KEY`在裡面可能得想辦法保密一下?)
* `likecombot\local_settings.py`: 若要在local端跑, 必須把裡面的設定值寫出來; o.w., 直接寫到環境變數即可
* `likecombot\live_settings.py`: 若找不到 `local_settings.py` 時會跑的 setting; production 用的! (目前本專案沒有架設local環境, 基本上都直接到live跑)
* `likecombot\urls.py` - Django用來針對 backend webserver 決定不同路徑要如何handle; 通常view寫好是要掛到這邊來才知道要trigger
* `scripts\*`: Django 的 script 都是擺到 scripts 資料夾, 可透過 cmd line trigger 執行
* `scripts\set_webhooks.py`: 這支script是用來tell telegram webhook urls 讓他知道有事要如何到我們這邊 notify 
* `templates\*` - Django的 "TEMPLATE", 通常用來放 HTML templates 讓 VIEW 可以用來做 render 用
* `bot\*` (dir.第一層裡面的code) - 好像是 Django MVC 要用到的 code, 基礎 facility for this project
* `bot\migrations\*` - 裡面都是 Django 要建立 DB (& admin panel?) 時要用到的 code, 得跟著 Model 的內容作修改
應該是會按照數字順序跑; 似乎是 auto-generated by Django 猜測是此 cmd `python manage.py migrate` 的 result. 
(不確定此功能可以做到甚麼地步...)
* `bot\utils\views.py` - Django的 "VIEW", 用來寫直接回應request & rendering 的 handler; 這邊放了所有頁面要怎麼render的資訊, 採用 `bot\templates` 內的 htmls 作為 template 來 render. DashBoard 跟 Post pages 都在這邊做.
* `bot\utils\models.py` - Django的 "Model", 用來寫與DB相關的OPs給View來調用
* `bot\utils\tasks.py` - 用 `process_tasks` 跑得一些要跑比較久的 tasks; e.g., msg. sending functions 之 impl
* `bot\utils\base.py` - 更底層的 core code shared by the others, 基本上就一堆 utils
* `bot\utils\livecom_utils.py` - Core logic for the master bot, inherit from `base bot`
* `bot\utils\str_utils.py` - all bot strings (translation就找這裡; html的部分則直接在html裡面寫) 


## FAQ  
* HTML這部分怎麼design的??
```
    Ans:
    * `templates\*` 裡面的 HTML 並是普通的 html! 外加了 Django 的特殊語法使得能夠dynamic而已, 然後還可以寫script加上JS的部分   
    * 甚至可以直接把 bootstrap 的 static htmls 放到 Django
        [Django] using bootstrap template by staticfile - George - Medium
        https://medium.com/@linth/django-using-bootstrap-template-by-staticfile-b99e10993d5e
        George's Blog: 在Django專案中使用Bootstrap template
        http://zhua0404.blogspot.com/2017/12/djangobootstrap-template.html
```

* 前後端的連線, 變成是always connect這樣嗎? htmls 無法獨立存在對嗎?
```
    Ans: Yes, 基本上有點像是半個php這樣, 有server去跑python然後吐dynamic htmls的概念
    不同處只在於只要有python就能夠standalone的跑起webserver
    而不需要apache, 或 IIS server.
```


