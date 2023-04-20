from fastapi import FastAPI, Query, Depends, Path
from sqlmodel import Session, select
import uvicorn
from src.db import get_db
from src import models, schemas

app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/timeline/{user_id}", response_model=list[schemas.TimelineOut])
def read_timeline(
    user_id: str = Path(...),
    offset: int = 0,
    limit: int = Query(default=100, lte=100),
    db: Session = Depends(get_db),
) -> list[models.Tweets]:
    query = (
        (
            select(models.Tweets, models.Users)
            .join_from(
                models.Tweets, models.Users, models.Tweets.sender_id == models.Users.id
            )
            .join(models.Follows, models.Follows.followee_id == models.Users.id)
            .filter(models.Follows.follower_id == user_id)
        )
        .offset(offset)
        .limit(limit)
    )
    results = db.exec(query).all()

    return [
        schemas.TimelineOut(
            tweet=schemas.Tweet(
                id=tweet.id, text=tweet.text, timestamp=tweet.timestamp
            ),
            user=schemas.User(
                screen_name=user.screen_name, profile_image=user.profile_image
            ),
        )
        for tweet, user in results
    ]


@app.post("/tweet")
def tweet():
    pass


if __name__ == "__main__":
    uvicorn.run(app)
