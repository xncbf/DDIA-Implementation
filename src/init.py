from sqlmodel import SQLModel, Session
from src.db import engine
from src import models
import random
import string


def generate_random_text(length):
    # Define the characters that can be used in the random string
    characters = string.ascii_letters + string.digits + string.punctuation

    # Generate a random string of the specified length
    random_text = "".join(random.choice(characters) for i in range(length))

    return random_text


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def create_datas():
    users = []
    for i in range(1, 100):
        users.append(
            models.Users(
                screen_name=f"user{i}", profile_image=f"https://example.com/user{i}.png"
            )
        )

    follows = []
    for i in range(1, 100):
        for j in range(1, 100):
            if i != j:
                follows.append(models.Follows(follower_id=i, followee_id=j))

    tweets = []
    for i in range(1, 100):
        for j in range(1, 100):
            if i != j:
                tweets.append(
                    models.Tweets(
                        sender_id=i,
                        text=f"{generate_random_text(10)}",
                        timestamp=random.randint(0, 1000000000),
                    )
                )
    with Session(engine) as session:
        for user in users:
            session.add(user)
        for follow in follows:
            session.add(follow)
        for tweet in tweets:
            session.add(tweet)
        session.commit()


create_db_and_tables()
create_datas()
