from sqlmodel import select, Session
from datetime import datetime

from src import models, schemas


def _get_timeline_by_query(
    db: Session, offset, limit, user_id
) -> list[tuple[models.Tweets, models.Users]]:
    query = (
        (
            select(models.Tweets, models.Users)
            .join_from(
                models.Tweets, models.Users, models.Tweets.sender_id == models.Users.id
            )
            .join(models.Follows, models.Follows.followee_id == models.Users.id)
            .filter(models.Follows.follower_id == user_id)
        )
        .order_by(models.Tweets.timestamp.desc())
        .offset(offset)
        .limit(limit)
    )
    results = db.exec(query).all()
    return results


def _cache_hit(db: Session, user_id) -> bool:
    query = select(models.TimelineCache).where(models.TimelineCache.user_id == user_id)
    result = db.exec(query).first()
    return result is not None


def _get_timeline_by_cache(
    db: Session, offset, limit, user_id
) -> list[tuple[models.Tweets, models.Users]] | None:
    if _cache_hit(user_id):
        _set_influencer_tweet_to_timeline_cache(db, user_id)
        query = (
            select(models.Tweets, models.Users)
            .join(
                models.TimelineCache, models.TimelineCache.tweet_id == models.Tweets.id
            )
            .join(models.Users, models.Tweets.sender_id == models.Users.id)
            .where(models.TimelineCache.user_id == user_id)
            .order_by(models.TimelineCache.timestamp.desc())
            .offset(offset)
            .limit(limit)
        )
        return db.exec(query).all()

    return None


def _set_timeline_cache(
    db: Session, results: list[tuple[models.Tweets, models.Users]], user_id
) -> None:
    for tweet, user in results:
        db_cache = models.TimelineCache(
            user_id=user_id, tweet_id=tweet.id, timestamp=tweet.timestamp
        )
        db.commit()
        db.refresh(db_cache)


def _set_influencer_tweet_to_timeline_cache(
    db: Session, user_id: int
) -> models.TimelineCache:
    query = (
        select(models.InfluencerTweetQueue)
        .join(models.Tweets, models.Tweets.id == models.InfluencerTweetQueue.tweet_id)
        .join(models.Follows, models.Follows.followee_id == models.Tweets.sender_id)
        .where(models.Follows.follower_id == user_id)
        .order_by(models.InfluencerTweetQueue.timestamp.desc())
    )
    results = db.exec(query).all()
    for result in results:
        # insert if not exists
        db_cache = (
            db.query(models.TimelineCache)
            .filter(models.TimelineCache.user_id == user_id)
            .filter(models.TimelineCache.tweet_id == result.tweet_id)
            .first()
        )
        if db_cache:
            continue

        db_cache = models.TimelineCache(
            user_id=user_id, tweet_id=result.tweet_id, timestamp=result.timestamp
        )
        db.add(db_cache)
        db.commit()
        db.refresh(db_cache)
    return db_cache


def _set_tweet_to_user_timeline_cache(
    db: Session, tweet: models.Tweets, user_id: int
) -> models.TimelineCache:
    if (
        db.query(models.Follows)
        .filter(models.Follows.followee_id == user_id)
        .group_by(models.Follows.follower_id)
        .count()
        < 100000
    ):
        # if user not influencer then save to cache
        query = select(models.Follows).where(models.Follows.followee_id == user_id)
        followers = db.exec(query).all()
        for follower in followers:
            db_cache = models.TimelineCache(
                user_id=follower.follower_id,
                tweet_id=tweet.id,
                timestamp=tweet.timestamp,
            )
    else:
        # influencer인 경우 큐에 넣어놓고 유저가 타임라인을 읽을때 가져옴
        db_cache = models.InfluencerTweetQueue(
            tweet_id=tweet.id, timestamp=tweet.timestamp
        )
    db.add(db_cache)
    db.commit()
    db.refresh(db_cache)


def _save_tweet(db: Session, tweet, user_id):
    timestamp = int(datetime.now().timestamp())
    db_tweet = models.Tweets(sender_id=user_id, text=tweet.text, timestamp=timestamp)
    db.add(db_tweet)
    db.commit()
    db.refresh(db_tweet)
    return db_tweet


def get_timeline(db: Session, offset, limit, user_id) -> list[schemas.TimelineOut]:
    results = _get_timeline_by_cache(db, offset, limit, user_id)
    if results:
        results = _get_timeline_by_query(db, offset, limit, user_id)
        _set_timeline_cache(db, results, user_id)
    return results


def post_tweet(db: Session, tweet, user_id):
    db_tweet = _save_tweet(db, tweet, user_id)
    _set_tweet_to_user_timeline_cache(db, db_tweet, user_id)
    return db_tweet
