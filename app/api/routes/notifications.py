"""
Phase 3 – Step 4: Notifications System
app/routers/notifications.py

Endpoints:
  GET  /notifications/         — list unread notifications
  PUT  /notifications/{id}/read — mark as read
  GET  /notifications/all       — list all (read + unread)
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from app.database import get_db
from app.models import Notification, User
from app.dependencies import get_current_user

router = APIRouter(prefix="/notifications", tags=["notifications"])


class NotificationOut(BaseModel):
    id: int
    type: str
    title: str
    message: Optional[str]
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("/", response_model=list[NotificationOut])
def get_unread_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """GET /notifications — list unread notifications for the current user."""
    return (
        db.query(Notification)
        .filter(
            Notification.user_id == current_user.id,
            Notification.is_read == False,
        )
        .order_by(Notification.created_at.desc())
        .all()
    )


@router.get("/all", response_model=list[NotificationOut])
def get_all_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """GET /notifications/all — list all notifications (paginated in production)."""
    return (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
        .limit(50)
        .all()
    )


@router.put("/{notification_id}/read", response_model=NotificationOut)
def mark_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """PUT /notifications/{id}/read — mark a notification as read."""
    notif = (
        db.query(Notification)
        .filter(
            Notification.id == notification_id,
            Notification.user_id == current_user.id,
        )
        .first()
    )
    if not notif:
        raise HTTPException(404, "Notification not found.")
    notif.is_read = True
    db.commit()
    db.refresh(notif)
    return notif


@router.put("/read-all", status_code=204)
def mark_all_as_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark all notifications as read."""
    db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False,
    ).update({"is_read": True})
    db.commit()


# ── Helper used by other services ───────────────────────────────────────────

def create_notification(
    db: Session,
    user_id: int,
    type: str,
    title: str,
    message: str = "",
) -> Notification:
    """Call this from any other router to create an in-app notification."""
    notif = Notification(user_id=user_id, type=type, title=title, message=message)
    db.add(notif)
    db.commit()
    db.refresh(notif)
    return notif
