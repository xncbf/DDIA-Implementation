from fastapi import FastAPI, Query, Depends, Path
from sqlmodel import Session
import uvicorn

from src.services import get_timeline, post_tweet
from src.db import get_db
from src import models, schemas


app = FastAPI()


@app.get("/timeline/{user_id}", response_model=list[schemas.TimelineOut])
def read_timeline(
    user_id: str = Path(...),
    offset: int = 0,
    limit: int = Query(default=100, lte=100),
    db: Session = Depends(get_db),
) -> list[models.Tweets]:
    results = get_timeline(db, offset, limit, user_id)
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


@app.post("/tweet/{user_id}", response_model=schemas.Tweet)
def tweet(
    tweet: schemas.TweetCreate,
    user_id: str = Path(...),
    db: Session = Depends(get_db),
):
    db_tweet = post_tweet(db, tweet, user_id)
    return db_tweet


if __name__ == "__main__":
    uvicorn.run(app)
