from pydantic import BaseModel


class Tweet(BaseModel):
    id: int
    text: str
    timestamp: int

    class Config:
        orm_mode = True


class User(BaseModel):
    screen_name: str
    profile_image: str

    class Config:
        orm_mode = True


class TimelineOut(BaseModel):
    tweet: Tweet
    user: User


class TweetCreate(BaseModel):
    text: str

    class Config:
        orm_mode = True
