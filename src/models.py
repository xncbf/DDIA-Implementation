from sqlmodel import Field, SQLModel


class Follows(SQLModel, table=True):
    id: int = Field(primary_key=True)
    follower_id: int = Field(foreign_key="users.id")
    followee_id: int = Field(foreign_key="users.id")


class Tweets(SQLModel, table=True):
    id: int = Field(primary_key=True)
    sender_id: int = Field(foreign_key="users.id")
    text: str = Field(max_length=280)
    timestamp: int = Field()


class Users(SQLModel, table=True):
    id: int = Field(primary_key=True)
    screen_name: str = Field(max_length=15)
    profile_image: str = Field(max_length=255)


class TimelineCache(SQLModel, table=True):
    id: int = Field(primary_key=True)
    user_id: int = Field(index=True)
    tweet_id: int = Field(index=True)
    timestamp: int = Field()


class InfluencerTweetQueue(SQLModel, table=True):
    id: int = Field(primary_key=True)
    tweet_id: int = Field(index=True)
    timestamp: int = Field()
