from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auction_logic import (
    cooldown_remaining_seconds,
    get_active_auction,
    get_single_auction,
    get_user_last_bid_time,
    place_bid,
    update_auction_status_if_ended,
    user_highest_bid_for_auction,
)
from app.database import get_db
from app.deps import get_current_user
from app.models import Auction, User
from app.schemas import (
    ALLOWED_INCREMENT,
    AuctionMeOut,
    AuctionStateOut,
    HighestBidderOut,
    PlaceBidIn,
    UserOut,
)

router = APIRouter(prefix="/auction", tags=["auction"])


def _highest_bidder_out(auction: Auction, db: Session) -> Optional[HighestBidderOut]:
    if not auction.current_highest_bidder_id:
        return None
    user = db.get(User, auction.current_highest_bidder_id)
    if not user:
        return None
    return HighestBidderOut(id=user.id, email=user.email)


def _time_remaining(auction: Auction) -> Optional[float]:
    if auction.status != "active":
        return None
    now = datetime.now(timezone.utc)
    end = auction.end_time
    if end.tzinfo is None:
        now = now.replace(tzinfo=None)
    if now >= end:
        return 0.0
    return (end - now).total_seconds()


def _auction_state(auction: Auction, db: Session) -> AuctionStateOut:
    update_auction_status_if_ended(db, auction)
    db.refresh(auction)
    winner = _highest_bidder_out(auction, db) if auction.status == "ended" else None
    return AuctionStateOut(
        title=auction.title,
        description=auction.description,
        start_time=auction.start_time,
        end_time=auction.end_time,
        current_highest_bid=auction.current_highest_bid,
        current_highest_bidder=_highest_bidder_out(auction, db),
        status=auction.status,
        time_remaining_seconds=_time_remaining(auction),
        winner=winner,
    )


@router.get("/state", response_model=AuctionStateOut)
def get_auction_state(db: Session = Depends(get_db)):
    auction = get_single_auction(db)
    if not auction:
        raise HTTPException(status_code=404, detail="No auction found.")
    return _auction_state(auction, db)


@router.post("/bid")
def place_bid_route(
    body: PlaceBidIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if body.increment not in ALLOWED_INCREMENT:
        raise HTTPException(
            status_code=400,
            detail="Invalid increment. Allowed: 5, 10, 15, 20, 50.",
        )
    auction = get_active_auction(db)
    if not auction:
        raise HTTPException(status_code=404, detail="No active auction found.")
    bid, err = place_bid(db, auction.id, current_user.id, body.increment)
    if err:
        raise HTTPException(status_code=400, detail=err)
    update_auction_status_if_ended(db, auction)
    db.refresh(auction)
    return {
        "message": "Bid placed.",
        "auction": _auction_state(auction, db),
        "your_bid": bid.amount,
    }


@router.get("/me", response_model=AuctionMeOut)
def auction_me(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    auction = get_single_auction(db)
    is_highest = False
    my_highest: Optional[float] = None
    cooldown: Optional[float] = 0.0

    if auction:
        is_highest = auction.current_highest_bidder_id == current_user.id
        my_highest = user_highest_bid_for_auction(db, auction.id, current_user.id)
        last_bid = get_user_last_bid_time(db, auction.id, current_user.id)
        cooldown = cooldown_remaining_seconds(last_bid)

    return AuctionMeOut(
        user=UserOut.model_validate(current_user),
        is_highest_bidder=is_highest,
        my_highest_bid=my_highest,
        cooldown_remaining_seconds=cooldown,
    )
