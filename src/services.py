from sqlmodel import select, Session
from datetime import datetime

from src import models


def _get_timeline_by_query(db: Session, offset, limit, user_id):
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


def _get_timeline_by_cache(db: Session, offset, limit, user_id):
    query = (
        select(models.Tweets, models.Users)
        .join(models.TimelineCache, models.TimelineCache.tweet_id == models.Tweets.id)
        .join(models.Users, models.Tweets.sender_id == models.Users.id)
        .where(models.TimelineCache.user_id == user_id)
        .order_by(models.TimelineCache.timestamp.desc())
        .offset(offset)
        .limit(limit)
    )
    results = db.exec(query).all()

    if results:
        return results
    return None


def _set_timeline_cache(db: Session, results, user_id):
    timestamp = int(datetime.now().timestamp())
    for tweet, user in results:
        db_cache = _set_tweet_to_user_timeline_cache(db, tweet, user_id)
        db_cache.timestamp = timestamp
        db.commit()
        db.refresh(db_cache)


def get_timeline(db: Session, offset, limit, user_id):
    results = _get_timeline_by_cache(db, offset, limit, user_id)
    if not results:
        results = _get_timeline_by_query(db, offset, limit, user_id)
        _set_timeline_cache(db, results, user_id)
    return results


def _set_tweet_to_user_timeline_cache(db: Session, tweet, user_id):
    timestamp = int(datetime.now().timestamp())
    db_cache = models.TimelineCache(
        user_id=user_id, tweet_id=tweet.id, timestamp=timestamp
    )
    db.add(db_cache)
    db.commit()
    db.refresh(db_cache)
    return db_cache


def _save_tweet(db: Session, tweet, user_id):
    timestamp = int(datetime.now().timestamp())
    db_tweet = models.Tweets(sender_id=user_id, text=tweet.text, timestamp=timestamp)
    db.add(db_tweet)
    db.commit()
    db.refresh(db_tweet)
    return db_tweet


def post_tweet(db: Session, tweet, user_id):
    db_tweet = _save_tweet(db, tweet, user_id)
    if (
        db.query(models.Follows)
        .filter(models.Follows.followee_id == user_id)
        .group_by(models.Follows.follower_id)
        .count()
        < 100000
    ):
        # if user not influencer then save to cache
        _set_tweet_to_user_timeline_cache(db, tweet, user_id)
    else:
        # influencer, do not save to cache
        pass
    return db_tweet
