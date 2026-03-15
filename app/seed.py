from datetime import timedelta, timezone

from sqlalchemy.orm import Session

from app.config import settings
from app.models import Auction


def seed_auction_if_empty(db: Session) -> None:
    if db.query(Auction).first() is not None:
        return
    start = settings.get_auction_start_time()
    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    end = start + timedelta(minutes=30)
    auction = Auction(
        title="The Legendary Black Pouch Bag",
        description=(
            "Behold: the one and only Black Pouch Bag. "
            "Rumored to hold exactly one phone, keys, and your dignity. "
            "Worn by legends. Desired by friends. "
            "Do not miss your chance to own a piece of history (and a very nice bag)."
        ),
        start_time=start,
        end_time=end,
        current_highest_bid=0.0,
        status="active",
    )
    db.add(auction)
    db.commit()
