"""
DaedalusSignal Database Models
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Table
from sqlalchemy.orm import relationship
from app.database import Base

# Association tables
user_sources = Table(
    'user_sources',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('source_id', Integer, ForeignKey('sources.id'), primary_key=True)
)

user_tags = Table(
    'user_tags',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id'), primary_key=True)
)

content_tags = Table(
    'content_tags',
    Base.metadata,
    Column('content_id', Integer, ForeignKey('contents.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id'), primary_key=True)
)


class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    is_admin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    email_verified = Column(Boolean, default=False)
    digest_enabled = Column(Boolean, default=True)
    onboarding_complete = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    sources = relationship('Source', secondary=user_sources, back_populates='users')
    tags = relationship('Tag', secondary=user_tags, back_populates='users')
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'is_admin': self.is_admin,
            'email_verified': self.email_verified,
            'digest_enabled': self.digest_enabled,
            'onboarding_complete': self.onboarding_complete,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Source(Base):
    __tablename__ = 'sources'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    url = Column(String(500), nullable=False)
    source_type = Column(String(50), nullable=False)  # youtube, twitter, linkedin, github
    is_default = Column(Boolean, default=False)
    is_approved = Column(Boolean, default=True)
    last_scraped = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    users = relationship('User', secondary=user_sources, back_populates='sources')
    contents = relationship('Content', back_populates='source')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'url': self.url,
            'source_type': self.source_type,
            'is_default': self.is_default,
            'last_scraped': self.last_scraped.isoformat() if self.last_scraped else None
        }


class Tag(Base):
    __tablename__ = 'tags'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    category = Column(String(50), nullable=True)  # e.g., "twitter", "github", etc.
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    users = relationship('User', secondary=user_tags, back_populates='tags')
    contents = relationship('Content', secondary=content_tags, back_populates='tags')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'is_default': self.is_default
        }


class Content(Base):
    __tablename__ = 'contents'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    url = Column(String(500), nullable=False, unique=True)
    content_type = Column(String(50), nullable=False)  # video, post, article, repo
    source_id = Column(Integer, ForeignKey('sources.id'), nullable=False)
    relevance_score = Column(Integer, default=0)  # 0-100
    published_at = Column(DateTime, nullable=True)
    scraped_at = Column(DateTime, default=datetime.utcnow)
    
    source = relationship('Source', back_populates='contents')
    tags = relationship('Tag', secondary=content_tags, back_populates='contents')
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'url': self.url,
            'content_type': self.content_type,
            'source': self.source.to_dict() if self.source else None,
            'relevance_score': self.relevance_score,
            'tags': [tag.to_dict() for tag in self.tags],
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'scraped_at': self.scraped_at.isoformat() if self.scraped_at else None
        }


class Digest(Base):
    __tablename__ = 'digests'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    content_ids = Column(Text, nullable=False)  # JSON array of content IDs
    sent_at = Column(DateTime, default=datetime.utcnow)
    delivery_method = Column(String(20), default='email')  # email or dashboard
    
    user = relationship('User')


class Feedback(Base):
    __tablename__ = 'feedback'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    email = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    feedback_type = Column(String(50), default='general')  # general, feature, bug, unblock_request
    status = Column(String(20), default='pending')  # pending, reviewed, resolved
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship('User')


class EmailBlocklist(Base):
    """Emails that have unsubscribed from digest emails."""
    __tablename__ = 'email_blocklist'

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    reason = Column(String(255), default='user_unsubscribed')  # user_unsubscribed, admin_blocked
    blocked_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'reason': self.reason,
            'blocked_at': self.blocked_at.isoformat() if self.blocked_at else None
        }


class VerificationCode(Base):
    """Verification codes for email verification and password reset."""
    __tablename__ = 'verification_codes'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    email = Column(String(255), nullable=False, index=True)
    code = Column(String(6), nullable=False)
    code_type = Column(String(20), nullable=False)  # 'email_verify' or 'password_reset'
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship('User')
