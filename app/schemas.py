from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


# Auth
class RequestOTPIn(BaseModel):
    email: EmailStr


class VerifyOTPIn(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$")


class UserOut(BaseModel):
    id: int
    email: str
    created_at: datetime

    class Config:
        from_attributes = True


class VerifyOTPOut(BaseModel):
    token: str
    user: UserOut


# Auction state
class HighestBidderOut(BaseModel):
    id: int
    email: str


class AuctionStateOut(BaseModel):
    title: str
    description: Optional[str]
    start_time: datetime
    end_time: datetime
    current_highest_bid: float
    current_highest_bidder: Optional[HighestBidderOut]
    status: str
    time_remaining_seconds: Optional[float]
    winner: Optional[HighestBidderOut]


# Bid
ALLOWED_INCREMENT = (5, 10, 15, 20, 50)


class PlaceBidIn(BaseModel):
    increment: int = Field(..., ge=5, le=50)

    def validate_increment(self) -> bool:
        return self.increment in ALLOWED_INCREMENT


class AuctionMeOut(BaseModel):
    user: UserOut
    is_highest_bidder: bool
    my_highest_bid: Optional[float]
    cooldown_remaining_seconds: Optional[float] = 0.0
