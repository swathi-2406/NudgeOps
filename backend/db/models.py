"""
NudgeOps Database Models — SQLite compatible (no JSONB, uses JSON).
"""

import uuid, json
from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    String, Integer, Float, Boolean, DateTime, Text, JSON,
    ForeignKey, Index, UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.database import Base


def gen_uuid():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    external_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    display_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    segment: Mapped[str] = mapped_column(String(50), default="new_user")
    timezone: Mapped[str] = mapped_column(String(50), default="UTC")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    opted_out_interventions: Mapped[str] = mapped_column(Text, default="[]")  # JSON string
    meta_data: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    events: Mapped[List["UserEvent"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    intervention_logs: Mapped[List["InterventionLog"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    embeddings: Mapped[List["UserEmbedding"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    bandit_states: Mapped[List["BanditState"]] = relationship(back_populates="user", cascade="all, delete-orphan")

    def get_opted_out(self) -> List[str]:
        return json.loads(self.opted_out_interventions or "[]")


class UserEvent(Base):
    __tablename__ = "user_events"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    event_source: Mapped[str] = mapped_column(String(100), nullable=False, default="app")
    properties: Mapped[str] = mapped_column(Text, default="{}")
    session_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="events")

    __table_args__ = (
        Index("ix_user_events_user_id", "user_id"),
        Index("ix_user_events_event_type", "event_type"),
        Index("ix_user_events_created_at", "created_at"),
    )


class Intervention(Base):
    __tablename__ = "interventions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    intervention_type: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    message_template: Mapped[str] = mapped_column(Text, nullable=False)
    channel: Mapped[str] = mapped_column(String(50), default="in_app")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    manipulativeness_score: Mapped[int] = mapped_column(Integer, default=1)
    risk_level: Mapped[str] = mapped_column(String(20), default="low")
    meta_data: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    logs: Mapped[List["InterventionLog"]] = relationship(back_populates="intervention")

    __table_args__ = (
        Index("ix_interventions_type", "intervention_type"),
    )


class InterventionLog(Base):
    __tablename__ = "intervention_logs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    intervention_id: Mapped[str] = mapped_column(String(36), ForeignKey("interventions.id"), nullable=False)
    policy_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("policies.id"), nullable=True)
    experiment_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("experiments.id"), nullable=True)
    bandit_strategy: Mapped[str] = mapped_column(String(50), default="thompson_sampling")
    context_features: Mapped[str] = mapped_column(Text, default="{}")
    feedback_signal: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    reward: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    feedback_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    delivered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    message_rendered: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship(back_populates="intervention_logs")
    intervention: Mapped["Intervention"] = relationship(back_populates="logs")

    __table_args__ = (
        Index("ix_intervention_logs_user_id", "user_id"),
        Index("ix_intervention_logs_delivered_at", "delivered_at"),
        Index("ix_intervention_logs_feedback", "feedback_signal"),
    )


class BanditState(Base):
    __tablename__ = "bandit_states"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    intervention_type: Mapped[str] = mapped_column(String(100), nullable=False)
    alpha: Mapped[float] = mapped_column(Float, default=1.0)
    beta: Mapped[float] = mapped_column(Float, default=1.0)
    n_pulls: Mapped[int] = mapped_column(Integer, default=0)
    total_reward: Mapped[float] = mapped_column(Float, default=0.0)
    mean_reward: Mapped[float] = mapped_column(Float, default=0.0)
    recent_rewards: Mapped[str] = mapped_column(Text, default="[]")
    is_failing: Mapped[bool] = mapped_column(Boolean, default=False)
    last_updated: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="bandit_states")

    __table_args__ = (
        UniqueConstraint("user_id", "intervention_type", name="uq_bandit_user_intervention"),
        Index("ix_bandit_states_user_id", "user_id"),
    )

    def get_recent_rewards(self) -> List[float]:
        return json.loads(self.recent_rewards or "[]")

    def set_recent_rewards(self, rewards: List[float]):
        self.recent_rewards = json.dumps(rewards)


class UserEmbedding(Base):
    __tablename__ = "user_embeddings"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    embedding: Mapped[str] = mapped_column(Text, nullable=False)  # JSON float list
    embedding_version: Mapped[str] = mapped_column(String(50), default="v1")
    feature_snapshot: Mapped[str] = mapped_column(Text, default="{}")
    computed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="embeddings")

    def get_embedding(self) -> List[float]:
        return json.loads(self.embedding or "[]")


class FeatureStore(Base):
    __tablename__ = "feature_store"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    features: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    computed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    def get_features(self) -> dict:
        return json.loads(self.features or "{}")


class Policy(Base):
    __tablename__ = "policies"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="draft")
    bandit_strategy: Mapped[str] = mapped_column(String(50), default="thompson_sampling")
    config: Mapped[str] = mapped_column(Text, default="{}")
    performance_metrics: Mapped[str] = mapped_column(Text, default="{}")
    artifact_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    promoted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    retired_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_by: Mapped[str] = mapped_column(String(100), default="system")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("name", "version", name="uq_policy_name_version"),
        Index("ix_policies_status", "status"),
    )

    def get_config(self) -> dict:
        return json.loads(self.config or "{}")

    def get_metrics(self) -> dict:
        return json.loads(self.performance_metrics or "{}")


class Experiment(Base):
    __tablename__ = "experiments"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="created")
    control_policy_id: Mapped[str] = mapped_column(String(36), ForeignKey("policies.id"), nullable=False)
    treatment_policy_id: Mapped[str] = mapped_column(String(36), ForeignKey("policies.id"), nullable=False)
    traffic_split: Mapped[float] = mapped_column(Float, default=0.5)
    target_segment: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    hypothesis: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    primary_metric: Mapped[str] = mapped_column(String(100), default="completion_rate")
    min_sample_size: Mapped[int] = mapped_column(Integer, default=30)
    results: Mapped[str] = mapped_column(Text, default="{}")
    winner: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    concluded_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_experiments_status", "status"),
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    actor: Mapped[str] = mapped_column(String(100), nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    details: Mapped[str] = mapped_column(Text, default="{}")
    outcome: Mapped[str] = mapped_column(String(50), default="success")
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_audit_logs_actor", "actor"),
        Index("ix_audit_logs_created_at", "created_at"),
    )


class MonitoringSnapshot(Base):
    __tablename__ = "monitoring_snapshots"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    snapshot_type: Mapped[str] = mapped_column(String(100), nullable=False)
    metrics: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    alerts: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_monitoring_type_created", "snapshot_type", "created_at"),
    )
