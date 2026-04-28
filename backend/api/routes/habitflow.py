"""
HabitFlow App API Routes
Handles auth, habits, completions, streaks, social feed.
All data persists to NudgeOps SQLite DB.
"""
import json
import hashlib
import hashlib, os
import secrets
from datetime import datetime, timedelta, date
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr
from jose import jwt, JWTError
from passlib.context import CryptContext

from db.database import get_db
from db.models import (
    User, AppUser, Habit, HabitCompletion, UserStreak,
    Follow, ActivityFeed, ActivityLike, HabitCategory,
    UserEvent, InterventionLog
)
from services.audit_service import log_action
from core.config import settings

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)
security = HTTPBearer(auto_error=False)

SECRET = settings.SECRET_KEY
ALGORITHM = "HS256"
TOKEN_EXPIRE_DAYS = 30

AVATAR_COLORS = ["#6ee7b7","#60a5fa","#a78bfa","#fb7185","#fbbf24","#34d399","#f97316","#e879f9"]

# ── Pydantic schemas ──────────────────────────────────────────────────────────

class SignupRequest(BaseModel):
    username: str
    email: str
    password: str
    display_name: str

class LoginRequest(BaseModel):
    email: str
    password: str

class HabitCreate(BaseModel):
    name: str
    description: Optional[str] = None
    icon: str = "✅"
    color: str = "#6ee7b7"
    frequency: str = "daily"
    target_days: List[int] = [0,1,2,3,4,5,6]
    reminder_time: Optional[str] = None
    is_public: bool = False
    category_id: Optional[str] = None

class HabitUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    frequency: Optional[str] = None
    target_days: Optional[List[int]] = None
    reminder_time: Optional[str] = None
    is_public: Optional[bool] = None
    is_active: Optional[bool] = None

class CompleteHabitRequest(BaseModel):
    completed_date: str  # YYYY-MM-DD
    note: Optional[str] = None
    mood: Optional[int] = None

class ProfileUpdate(BaseModel):
    display_name: Optional[str] = None
    bio: Optional[str] = None
    is_profile_public: Optional[bool] = None
    avatar_color: Optional[str] = None

# ── Auth helpers ──────────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    salt = os.urandom(32)
    key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
    return salt.hex() + ':' + key.hex()

def verify_password(plain: str, hashed: str) -> bool:
    try:
        salt_hex, key_hex = hashed.split(':')
        salt = bytes.fromhex(salt_hex)
        key = hashlib.pbkdf2_hmac('sha256', plain.encode(), salt, 100000)
        return key.hex() == key_hex
    except Exception:
        return False



def create_token(user_id: str) -> str:
    expire = datetime.utcnow() + timedelta(days=TOKEN_EXPIRE_DAYS)
    return jwt.encode({"sub": user_id, "exp": expire}, SECRET, algorithm=ALGORITHM)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> AppUser:
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(credentials.credentials, SECRET, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    result = await db.execute(select(AppUser).where(AppUser.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

# ── Streak helpers ────────────────────────────────────────────────────────────

async def recalc_streak(app_user_id: str, nudgeops_user_id: str, db: AsyncSession):
    """Recalculate streak for a user after a completion."""
    # Get all completion dates for this user, sorted desc
    result = await db.execute(
        select(HabitCompletion.completed_date)
        .where(HabitCompletion.user_id == nudgeops_user_id)
        .distinct()
        .order_by(desc(HabitCompletion.completed_date))
    )
    dates = [r[0] for r in result.all()]

    if not dates:
        return

    today = date.today().isoformat()
    yesterday = (date.today() - timedelta(days=1)).isoformat()

    # Current streak
    current = 0
    check_date = date.today()
    for d in dates:
        if d == check_date.isoformat() or d == (check_date - timedelta(days=1)).isoformat():
            current += 1
            check_date = date.fromisoformat(d) - timedelta(days=1)
        else:
            break

    # Get or create streak record
    streak_result = await db.execute(select(UserStreak).where(UserStreak.user_id == nudgeops_user_id))
    streak = streak_result.scalar_one_or_none()
    if not streak:
        streak = UserStreak(user_id=nudgeops_user_id)
        db.add(streak)

    old_streak = streak.current_streak
    streak.current_streak = current
    streak.longest_streak = max(streak.longest_streak, current)
    streak.total_completions = len(dates)
    streak.last_completion_date = dates[0] if dates else None
    streak.updated_at = datetime.utcnow()

    # Post milestone to activity feed
    milestones = [7, 14, 21, 30, 60, 90, 100, 365]
    if current in milestones and current > old_streak:
        feed = ActivityFeed(
            app_user_id=app_user_id,
            activity_type="streak_milestone",
            content=f"🔥 Hit a {current}-day streak!",
            meta_data=json.dumps({"streak": current}),
        )
        db.add(feed)

# ── AUTH routes ───────────────────────────────────────────────────────────────

@router.post("/auth/signup")
async def signup(payload: SignupRequest, db: AsyncSession = Depends(get_db)):
    # Check uniqueness
    existing = await db.execute(
        select(AppUser).where(or_(AppUser.email == payload.email, AppUser.username == payload.username))
    )
    if existing.scalar_one_or_none():
        raise HTTPException(400, "Email or username already taken")

    # Create NudgeOps user
    nu_user = User(
        external_id=f"hf_{payload.username}",
        email=payload.email,
        display_name=payload.display_name,
        segment="new_user",
    )
    db.add(nu_user)
    await db.flush()

    # Create app user
    color = AVATAR_COLORS[len(payload.username) % len(AVATAR_COLORS)]
    app_user = AppUser(
        nudgeops_user_id=nu_user.id,
        username=payload.username,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        display_name=payload.display_name,
        avatar_color=color,
    )
    db.add(app_user)
    await db.flush()

    # Create default streak record
    db.add(UserStreak(user_id=nu_user.id))

    # Create default categories
    default_cats = [
        ("Health", "#4ade80", "💪"), ("Mind", "#a78bfa", "🧠"),
        ("Learning", "#60a5fa", "📚"), ("Social", "#fb7185", "👥"),
    ]
    for name, color, icon in default_cats:
        db.add(HabitCategory(user_id=nu_user.id, name=name, color=color, icon=icon))

    # Welcome activity
    db.add(ActivityFeed(
        app_user_id=app_user.id,
        activity_type="joined",
        content=f"👋 {payload.display_name} joined HabitFlow!",
        meta_data=json.dumps({}),
    ))

    await log_action(db, "habitflow", "user_signup", "app_user", app_user.id,
                     {"username": payload.username})
    await db.commit()

    token = create_token(app_user.id)
    return {
        "token": token,
        "user": {
            "id": app_user.id,
            "nudgeops_user_id": nu_user.id,
            "username": app_user.username,
            "display_name": app_user.display_name,
            "email": app_user.email,
            "avatar_color": app_user.avatar_color,
            "bio": app_user.bio,
            "is_profile_public": app_user.is_profile_public,
            "created_at": app_user.created_at.isoformat(),
        }
    }


@router.post("/auth/login")
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AppUser).where(AppUser.email == payload.email))
    app_user = result.scalar_one_or_none()
    if not app_user or not verify_password(payload.password, app_user.hashed_password):
        raise HTTPException(401, "Invalid email or password")

    token = create_token(app_user.id)
    streak_result = await db.execute(
        select(UserStreak).where(UserStreak.user_id == app_user.nudgeops_user_id)
    )
    streak = streak_result.scalar_one_or_none()

    return {
        "token": token,
        "user": {
            "id": app_user.id,
            "nudgeops_user_id": app_user.nudgeops_user_id,
            "username": app_user.username,
            "display_name": app_user.display_name,
            "email": app_user.email,
            "avatar_color": app_user.avatar_color,
            "bio": app_user.bio,
            "is_profile_public": app_user.is_profile_public,
            "created_at": app_user.created_at.isoformat(),
            "current_streak": streak.current_streak if streak else 0,
            "longest_streak": streak.longest_streak if streak else 0,
            "total_completions": streak.total_completions if streak else 0,
        }
    }


@router.get("/auth/me")
async def get_me(current_user: AppUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    streak_result = await db.execute(
        select(UserStreak).where(UserStreak.user_id == current_user.nudgeops_user_id)
    )
    streak = streak_result.scalar_one_or_none()
    followers_count = await db.execute(select(func.count(Follow.id)).where(Follow.following_id == current_user.id))
    following_count = await db.execute(select(func.count(Follow.id)).where(Follow.follower_id == current_user.id))

    return {
        "id": current_user.id,
        "nudgeops_user_id": current_user.nudgeops_user_id,
        "username": current_user.username,
        "display_name": current_user.display_name,
        "email": current_user.email,
        "avatar_color": current_user.avatar_color,
        "bio": current_user.bio,
        "is_profile_public": current_user.is_profile_public,
        "created_at": current_user.created_at.isoformat(),
        "current_streak": streak.current_streak if streak else 0,
        "longest_streak": streak.longest_streak if streak else 0,
        "total_completions": streak.total_completions if streak else 0,
        "followers_count": followers_count.scalar() or 0,
        "following_count": following_count.scalar() or 0,
    }

# ── HABITS routes ─────────────────────────────────────────────────────────────

@router.get("/habits")
async def get_habits(
    current_user: AppUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Habit)
        .where(Habit.user_id == current_user.nudgeops_user_id)
        .where(Habit.is_active == True)
        .order_by(Habit.sort_order, Habit.created_at)
    )
    habits = result.scalars().all()

    # Get today's completions
    today = date.today().isoformat()
    comp_result = await db.execute(
        select(HabitCompletion.habit_id)
        .where(HabitCompletion.user_id == current_user.nudgeops_user_id)
        .where(HabitCompletion.completed_date == today)
    )
    completed_today = {r[0] for r in comp_result.all()}

    return [_serialize_habit(h, completed_today) for h in habits]


@router.post("/habits", status_code=201)
async def create_habit(
    payload: HabitCreate,
    current_user: AppUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    habit = Habit(
        user_id=current_user.nudgeops_user_id,
        name=payload.name,
        description=payload.description,
        icon=payload.icon,
        color=payload.color,
        frequency=payload.frequency,
        target_days=json.dumps(payload.target_days),
        reminder_time=payload.reminder_time,
        is_public=payload.is_public,
        category_id=payload.category_id,
    )
    db.add(habit)
    await db.flush()

    # Log event
    db.add(UserEvent(
        user_id=current_user.nudgeops_user_id,
        event_type="habit_created",
        event_source="habitflow",
        properties=json.dumps({"habit_id": habit.id, "name": payload.name}),
    ))
    await db.commit()
    return _serialize_habit(habit, set())


@router.patch("/habits/{habit_id}")
async def update_habit(
    habit_id: str,
    payload: HabitUpdate,
    current_user: AppUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Habit).where(Habit.id == habit_id).where(Habit.user_id == current_user.nudgeops_user_id)
    )
    habit = result.scalar_one_or_none()
    if not habit:
        raise HTTPException(404, "Habit not found")

    for field, value in payload.model_dump(exclude_none=True).items():
        if field == "target_days":
            value = json.dumps(value)
        setattr(habit, field, value)
    habit.updated_at = datetime.utcnow()
    await db.commit()
    return _serialize_habit(habit, set())


@router.delete("/habits/{habit_id}", status_code=204)
async def delete_habit(
    habit_id: str,
    current_user: AppUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Habit).where(Habit.id == habit_id).where(Habit.user_id == current_user.nudgeops_user_id)
    )
    habit = result.scalar_one_or_none()
    if not habit:
        raise HTTPException(404, "Habit not found")
    habit.is_active = False
    await db.commit()


@router.post("/habits/{habit_id}/complete")
async def complete_habit(
    habit_id: str,
    payload: CompleteHabitRequest,
    current_user: AppUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Verify habit ownership
    result = await db.execute(
        select(Habit).where(Habit.id == habit_id).where(Habit.user_id == current_user.nudgeops_user_id)
    )
    habit = result.scalar_one_or_none()
    if not habit:
        raise HTTPException(404, "Habit not found")

    # Check if already completed
    existing = await db.execute(
        select(HabitCompletion)
        .where(HabitCompletion.habit_id == habit_id)
        .where(HabitCompletion.completed_date == payload.completed_date)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(400, "Already completed for this date")

    completion = HabitCompletion(
        habit_id=habit_id,
        user_id=current_user.nudgeops_user_id,
        completed_date=payload.completed_date,
        note=payload.note,
        mood=payload.mood,
    )
    db.add(completion)

    # NudgeOps event
    db.add(UserEvent(
        user_id=current_user.nudgeops_user_id,
        event_type="task_complete",
        event_source="habitflow",
        properties=json.dumps({"habit_id": habit_id, "date": payload.completed_date}),
    ))

    await db.flush()
    await recalc_streak(current_user.id, current_user.nudgeops_user_id, db)

    # Activity feed for public habits
    if habit.is_public:
        db.add(ActivityFeed(
            app_user_id=current_user.id,
            activity_type="habit_completed",
            content=f"{habit.icon} {current_user.display_name} completed \"{habit.name}\"",
            meta_data=json.dumps({"habit_id": habit_id, "date": payload.completed_date}),
        ))

    await db.commit()

    streak_result = await db.execute(
        select(UserStreak).where(UserStreak.user_id == current_user.nudgeops_user_id)
    )
    streak = streak_result.scalar_one_or_none()
    return {
        "completed": True,
        "current_streak": streak.current_streak if streak else 0,
        "total_completions": streak.total_completions if streak else 0,
    }


@router.delete("/habits/{habit_id}/complete/{date_str}", status_code=204)
async def uncomplete_habit(
    habit_id: str, date_str: str,
    current_user: AppUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(HabitCompletion)
        .where(HabitCompletion.habit_id == habit_id)
        .where(HabitCompletion.user_id == current_user.nudgeops_user_id)
        .where(HabitCompletion.completed_date == date_str)
    )
    completion = result.scalar_one_or_none()
    if completion:
        await db.delete(completion)
        await recalc_streak(current_user.id, current_user.nudgeops_user_id, db)
        await db.commit()


@router.get("/habits/{habit_id}/history")
async def get_habit_history(
    habit_id: str,
    days: int = 90,
    current_user: AppUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Habit).where(Habit.id == habit_id).where(Habit.user_id == current_user.nudgeops_user_id)
    )
    habit = result.scalar_one_or_none()
    if not habit:
        raise HTTPException(404, "Habit not found")

    since = (date.today() - timedelta(days=days)).isoformat()
    comp_result = await db.execute(
        select(HabitCompletion)
        .where(HabitCompletion.habit_id == habit_id)
        .where(HabitCompletion.completed_date >= since)
        .order_by(desc(HabitCompletion.completed_date))
    )
    completions = comp_result.scalars().all()

    return {
        "habit": _serialize_habit(habit, set()),
        "completions": [
            {"date": c.completed_date, "note": c.note, "mood": c.mood}
            for c in completions
        ],
        "completion_rate": len(completions) / days if days else 0,
        "total": len(completions),
    }


@router.get("/habits/completions/range")
async def get_completions_range(
    start: str, end: str,
    current_user: AppUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(HabitCompletion)
        .where(HabitCompletion.user_id == current_user.nudgeops_user_id)
        .where(HabitCompletion.completed_date >= start)
        .where(HabitCompletion.completed_date <= end)
    )
    completions = result.scalars().all()
    by_date = {}
    for c in completions:
        if c.completed_date not in by_date:
            by_date[c.completed_date] = []
        by_date[c.completed_date].append(c.habit_id)
    return by_date


# ── NUDGE routes ──────────────────────────────────────────────────────────────

@router.post("/nudge/request")
async def request_nudge(
    current_user: AppUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a personalized nudge via the bandit engine."""
    from services.bandit_service import select_intervention
    try:
        result = await select_intervention(current_user.nudgeops_user_id, db)
        return result
    except Exception as e:
        raise HTTPException(500, str(e))


@router.post("/nudge/feedback")
async def submit_nudge_feedback(
    log_id: str,
    signal: str,
    current_user: AppUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    from services.bandit_service import record_feedback
    valid = ["engaged","completed","ignored","dismissed","negative"]
    if signal not in valid:
        raise HTTPException(400, f"Signal must be one of {valid}")
    return await record_feedback(log_id, current_user.nudgeops_user_id, signal, db)


@router.get("/nudge/history")
async def get_nudge_history(
    limit: int = 20,
    current_user: AppUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(InterventionLog)
        .where(InterventionLog.user_id == current_user.nudgeops_user_id)
        .order_by(desc(InterventionLog.delivered_at))
        .limit(limit)
    )
    logs = result.scalars().all()
    return [
        {
            "id": l.id,
            "intervention_type": l.intervention_id,
            "message": l.message_rendered,
            "feedback_signal": l.feedback_signal,
            "reward": l.reward,
            "delivered_at": l.delivered_at.isoformat(),
            "feedback_at": l.feedback_at.isoformat() if l.feedback_at else None,
        }
        for l in logs
    ]


# ── STATS routes ──────────────────────────────────────────────────────────────

@router.get("/stats")
async def get_stats(
    current_user: AppUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    streak_result = await db.execute(
        select(UserStreak).where(UserStreak.user_id == current_user.nudgeops_user_id)
    )
    streak = streak_result.scalar_one_or_none()

    # Habits count
    habits_result = await db.execute(
        select(func.count(Habit.id))
        .where(Habit.user_id == current_user.nudgeops_user_id)
        .where(Habit.is_active == True)
    )
    habits_count = habits_result.scalar() or 0

    # Last 30 days completion heatmap
    since = (date.today() - timedelta(days=29)).isoformat()
    comp_result = await db.execute(
        select(HabitCompletion.completed_date, func.count(HabitCompletion.id).label("cnt"))
        .where(HabitCompletion.user_id == current_user.nudgeops_user_id)
        .where(HabitCompletion.completed_date >= since)
        .group_by(HabitCompletion.completed_date)
    )
    heatmap = {r.completed_date: r.cnt for r in comp_result.all()}

    # Best day of week
    dow_result = await db.execute(
        select(HabitCompletion.completed_date, func.count(HabitCompletion.id).label("cnt"))
        .where(HabitCompletion.user_id == current_user.nudgeops_user_id)
        .group_by(HabitCompletion.completed_date)
        .order_by(desc("cnt"))
        .limit(1)
    )
    best_day_row = dow_result.first()

    # Nudge stats
    nudge_result = await db.execute(
        select(func.count(InterventionLog.id))
        .where(InterventionLog.user_id == current_user.nudgeops_user_id)
    )
    total_nudges = nudge_result.scalar() or 0

    nudge_completed = await db.execute(
        select(func.count(InterventionLog.id))
        .where(InterventionLog.user_id == current_user.nudgeops_user_id)
        .where(InterventionLog.feedback_signal == "completed")
    )
    nudges_completed = nudge_completed.scalar() or 0

    return {
        "current_streak": streak.current_streak if streak else 0,
        "longest_streak": streak.longest_streak if streak else 0,
        "total_completions": streak.total_completions if streak else 0,
        "active_habits": habits_count,
        "heatmap": heatmap,
        "total_nudges": total_nudges,
        "nudge_completion_rate": nudges_completed / total_nudges if total_nudges else 0,
    }


# ── SOCIAL routes ─────────────────────────────────────────────────────────────

@router.get("/social/feed")
async def get_feed(
    limit: int = 30,
    current_user: AppUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Get IDs of people this user follows + self
    following_result = await db.execute(
        select(Follow.following_id).where(Follow.follower_id == current_user.id)
    )
    following_ids = [r[0] for r in following_result.all()] + [current_user.id]

    feed_result = await db.execute(
        select(ActivityFeed, AppUser.display_name, AppUser.avatar_color, AppUser.username)
        .join(AppUser, AppUser.id == ActivityFeed.app_user_id)
        .where(ActivityFeed.app_user_id.in_(following_ids))
        .order_by(desc(ActivityFeed.created_at))
        .limit(limit)
    )
    rows = feed_result.all()

    # Check which ones current user liked
    liked_result = await db.execute(
        select(ActivityLike.activity_id)
        .where(ActivityLike.app_user_id == current_user.id)
    )
    liked_ids = {r[0] for r in liked_result.all()}

    return [
        {
            "id": row.ActivityFeed.id,
            "user": {"display_name": row.display_name, "avatar_color": row.avatar_color, "username": row.username},
            "activity_type": row.ActivityFeed.activity_type,
            "content": row.ActivityFeed.content,
            "likes_count": row.ActivityFeed.likes_count,
            "liked_by_me": row.ActivityFeed.id in liked_ids,
            "created_at": row.ActivityFeed.created_at.isoformat(),
        }
        for row in rows
    ]


@router.get("/social/discover")
async def discover_users(
    q: Optional[str] = None,
    limit: int = 20,
    current_user: AppUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(AppUser).where(AppUser.id != current_user.id).where(AppUser.is_profile_public == True)
    if q:
        query = query.where(or_(
            AppUser.username.contains(q),
            AppUser.display_name.contains(q)
        ))
    result = await db.execute(query.limit(limit))
    users = result.scalars().all()

    following_result = await db.execute(
        select(Follow.following_id).where(Follow.follower_id == current_user.id)
    )
    following_ids = {r[0] for r in following_result.all()}

    out = []
    for u in users:
        streak_r = await db.execute(select(UserStreak).where(UserStreak.user_id == u.nudgeops_user_id))
        streak = streak_r.scalar_one_or_none()
        out.append({
            "id": u.id, "username": u.username, "display_name": u.display_name,
            "avatar_color": u.avatar_color, "bio": u.bio,
            "current_streak": streak.current_streak if streak else 0,
            "is_following": u.id in following_ids,
        })
    return out


@router.post("/social/follow/{user_id}")
async def follow_user(
    user_id: str,
    current_user: AppUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if user_id == current_user.id:
        raise HTTPException(400, "Cannot follow yourself")
    existing = await db.execute(
        select(Follow).where(Follow.follower_id == current_user.id).where(Follow.following_id == user_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(400, "Already following")
    db.add(Follow(follower_id=current_user.id, following_id=user_id))
    await db.commit()
    return {"following": True}


@router.delete("/social/follow/{user_id}", status_code=204)
async def unfollow_user(
    user_id: str,
    current_user: AppUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Follow).where(Follow.follower_id == current_user.id).where(Follow.following_id == user_id)
    )
    follow = result.scalar_one_or_none()
    if follow:
        await db.delete(follow)
        await db.commit()


@router.post("/social/like/{activity_id}")
async def like_activity(
    activity_id: str,
    current_user: AppUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    existing = await db.execute(
        select(ActivityLike)
        .where(ActivityLike.activity_id == activity_id)
        .where(ActivityLike.app_user_id == current_user.id)
    )
    if existing.scalar_one_or_none():
        # Unlike
        like = (await db.execute(select(ActivityLike).where(
            ActivityLike.activity_id == activity_id,
            ActivityLike.app_user_id == current_user.id
        ))).scalar_one()
        await db.delete(like)
        # Decrement
        activity = (await db.execute(select(ActivityFeed).where(ActivityFeed.id == activity_id))).scalar_one_or_none()
        if activity:
            activity.likes_count = max(0, activity.likes_count - 1)
        await db.commit()
        return {"liked": False}
    else:
        db.add(ActivityLike(activity_id=activity_id, app_user_id=current_user.id))
        activity = (await db.execute(select(ActivityFeed).where(ActivityFeed.id == activity_id))).scalar_one_or_none()
        if activity:
            activity.likes_count += 1
        await db.commit()
        return {"liked": True}


@router.get("/social/profile/{username}")
async def get_profile(
    username: str,
    current_user: AppUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(AppUser).where(AppUser.username == username))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")

    streak_r = await db.execute(select(UserStreak).where(UserStreak.user_id == user.nudgeops_user_id))
    streak = streak_r.scalar_one_or_none()

    followers_count = (await db.execute(select(func.count(Follow.id)).where(Follow.following_id == user.id))).scalar() or 0
    following_count = (await db.execute(select(func.count(Follow.id)).where(Follow.follower_id == user.id))).scalar() or 0

    is_following = bool((await db.execute(
        select(Follow).where(Follow.follower_id == current_user.id).where(Follow.following_id == user.id)
    )).scalar_one_or_none())

    # Public habits
    habits_r = await db.execute(
        select(Habit).where(Habit.user_id == user.nudgeops_user_id).where(Habit.is_public == True).where(Habit.is_active == True)
    )
    public_habits = habits_r.scalars().all()

    return {
        "id": user.id, "username": user.username, "display_name": user.display_name,
        "avatar_color": user.avatar_color, "bio": user.bio,
        "current_streak": streak.current_streak if streak else 0,
        "longest_streak": streak.longest_streak if streak else 0,
        "total_completions": streak.total_completions if streak else 0,
        "followers_count": followers_count, "following_count": following_count,
        "is_following": is_following,
        "public_habits": [_serialize_habit(h, set()) for h in public_habits],
    }


@router.patch("/profile")
async def update_profile(
    payload: ProfileUpdate,
    current_user: AppUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(current_user, field, value)
    await db.commit()
    return {"updated": True}


@router.get("/categories")
async def get_categories(
    current_user: AppUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(HabitCategory).where(HabitCategory.user_id == current_user.nudgeops_user_id)
    )
    cats = result.scalars().all()
    return [{"id": c.id, "name": c.name, "color": c.color, "icon": c.icon} for c in cats]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _serialize_habit(h: Habit, completed_today: set) -> dict:
    return {
        "id": h.id,
        "name": h.name,
        "description": h.description,
        "icon": h.icon,
        "color": h.color,
        "frequency": h.frequency,
        "target_days": json.loads(h.target_days) if h.target_days else [0,1,2,3,4,5,6],
        "reminder_time": h.reminder_time,
        "is_public": h.is_public,
        "is_active": h.is_active,
        "category_id": h.category_id,
        "completed_today": h.id in completed_today,
        "created_at": h.created_at.isoformat(),
    }
