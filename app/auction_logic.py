from datetime import datetime, timezone
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from app.models import Auction, Bid, User
from app.schemas import ALLOWED_INCREMENT

BID_COOLDOWN_SECONDS = 5
AUCTION_DURATION_MINUTES = 30


def get_active_auction(db: Session) -> Optional[Auction]:
    return db.query(Auction).filter(Auction.status == "active").first()


def get_single_auction(db: Session) -> Optional[Auction]:
    return db.query(Auction).order_by(Auction.id.desc()).first()


def auction_is_active(auction: Auction) -> bool:
    if auction.status != "active":
        return False
    now = datetime.now(timezone.utc)
    if auction.end_time.tzinfo is None:
        now = now.replace(tzinfo=None)
    return auction.start_time <= now <= auction.end_time


def update_auction_status_if_ended(db: Session, auction: Auction) -> None:
    now = datetime.now(timezone.utc)
    end = auction.end_time
    if end.tzinfo is None:
        now = now.replace(tzinfo=None)
    if now >= end and auction.status == "active":
        auction.status = "ended"
        db.commit()


def get_user_last_bid_time(db: Session, auction_id: int, user_id: int) -> Optional[datetime]:
    row = (
        db.query(Bid.created_at)
        .filter(Bid.auction_id == auction_id, Bid.user_id == user_id)
        .order_by(Bid.created_at.desc())
        .first()
    )
    return row[0] if row else None


def cooldown_remaining_seconds(last_bid_at: Optional[datetime]) -> float:
    if last_bid_at is None:
        return 0.0
    now = datetime.now(timezone.utc)
    if last_bid_at.tzinfo is None:
        last_bid_at = last_bid_at.replace(tzinfo=timezone.utc)
    elapsed = (now - last_bid_at).total_seconds()
    remaining = BID_COOLDOWN_SECONDS - elapsed
    return max(0.0, remaining)


def is_in_cooldown(last_bid_at: Optional[datetime]) -> bool:
    return cooldown_remaining_seconds(last_bid_at) > 0


def user_highest_bid_for_auction(db: Session, auction_id: int, user_id: int) -> Optional[float]:
    row = (
        db.query(Bid.amount)
        .filter(Bid.auction_id == auction_id, Bid.user_id == user_id)
        .order_by(Bid.amount.desc())
        .first()
    )
    return float(row[0]) if row else None


def place_bid(
    db: Session,
    auction_id: int,
    user_id: int,
    increment: int,
) -> Tuple[Optional[Bid], Optional[str]]:
    if increment not in ALLOWED_INCREMENT:
        return None, "Invalid increment. Allowed: 5, 10, 15, 20, 50."

    auction = db.query(Auction).filter(Auction.id == auction_id).with_for_update().first()
    if not auction:
        return None, "Auction not found."

    now = datetime.now(timezone.utc)
    end = auction.end_time
    if end.tzinfo is None:
        now_naive = now.replace(tzinfo=None)
    else:
        now_naive = now
    if now_naive >= end:
        return None, "Auction has ended."
    if auction.status != "active":
        return None, "Auction is not active."

    if auction.current_highest_bidder_id == user_id:
        return None, "You are already the highest bidder. Wait for someone else to outbid you."

    last_bid_at = get_user_last_bid_time(db, auction_id, user_id)
    if is_in_cooldown(last_bid_at):
        return None, "Please wait 5 seconds between bids."

    new_amount = auction.current_highest_bid + increment
    bid = Bid(auction_id=auction_id, user_id=user_id, increment=increment, amount=new_amount)
    db.add(bid)
    auction.current_highest_bid = new_amount
    auction.current_highest_bidder_id = user_id
    db.commit()
    db.refresh(bid)
    db.refresh(auction)
    return bid, None
