from bot.models import Comment, Post
from users.models import User

import random
from faker import Faker

fake = Faker()


def generate_comments():
    users = User.objects.all()
    post = Post.objects.last()

    for i in range(80):

        print(f"generating comment #{i + 1}")

        comment = Comment.objects.create(
            comment_post=post,
            user=random.choice(users),
            text=fake.sentence()
        )

        if i % 2 == 0:
            Comment.objects.create(
                comment_post=post,
                user=random.choice(users),
                parent=comment,
                text=fake.sentence()
            )


def run():
    generate_comments()
