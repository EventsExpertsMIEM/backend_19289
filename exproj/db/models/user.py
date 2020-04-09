import uuid
from datetime import datetime

from flask_login import current_user, UserMixin, AnonymousUserMixin
from sqlalchemy import (Column, Integer, String, ForeignKey, Table,
                        DateTime, Boolean, UniqueConstraint)
from sqlalchemy.dialects.postgresql import TEXT, ENUM, UUID
from sqlalchemy.orm import relationship, backref

from exproj import config
from exproj.db import Base, USER_ACCESS
from exproj.db.models.tag import d_user_interests, d_user_tags


Account_status = ENUM('unconfirmed', 'active', 'deleted',
                      'banned', name='account_status')


class User(Base, UserMixin):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    cookie_id = Column(UUID(as_uuid=True), default=uuid.uuid4,
                       unique=True, nullable=False)
    name = Column(String, nullable=False)
    surname = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(TEXT, nullable=False)
    confirmation_link = Column(String, nullable=False)
    access = Column(Integer, default=USER_ACCESS['user'], nullable=False)
    status = Column(Account_status, default=config.DEFAULT_USER_STATUS,
                    nullable=False)

    # secondary info
    position = Column(String, nullable=True)

    # statistic
    rating = Column(Integer, default=0, nullable=False)
    question_count = Column(Integer, default=0, nullable=False)
    article_count = Column(Integer, default=0, nullable=False)
    comment_count = Column(Integer, default=0, nullable=False)
    registration_date = Column(DateTime, default=datetime.utcnow,
                               nullable=False)

    # todo: each function has lazy='dynamic'. doesn't look good
    posts = relationship('Post', lazy='dynamic')
    questions = relationship('Question', lazy='dynamic')
    articles = relationship('Article', lazy='dynamic')
    comments = relationship('Comment', lazy='dynamic')
    d_voted_posts = relationship('DPostVotes', lazy='dynamic')
    d_voted_comments = relationship('DCommentVotes', lazy='dynamic')
    tags = relationship('Tag', secondary=d_user_tags, lazy='dynamic')
    interests = relationship('Tag', secondary=d_user_interests, lazy='dynamic')
    avatar = relationship('Avatar', uselist=False, lazy='joined')
    # certificates
    # warns

    def get_id(self):
        return self.cookie_id

    def as_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'surname': self.surname,
            'email': self.email,
            'role': self.get_role(),
            'tags': [t.name for t in self.tags.all()],
            'interests': [t.name for t in self.interests.all()],
            'position': self.position,
            'rating': self.rating,
            'registration_date': self.registration_date.timestamp(),
            'status': self.status,
            'question_count': self.question_count,
            'article_count': self.article_count,
            'comment_count': self.comment_count,
            'has_avatar': self.avatar is not None
        }

    def get_role(self):
        return [key for key, value in USER_ACCESS.items()
                if value == self.access][0]

    def has_access(self, access):
        return self.access >= USER_ACCESS[access]

    def can_answer(self, q):
        if q.u_id == self.id or self.has_access('moderator'):
            return True

        if ((q.closed or q.only_experts_answer or q.only_chosen_tags) and
                not self.has_access('expert')):
            return False

        if (q.only_chosen_tags and
                len(set(self.tags.all()) & set(q.tags.all())) == 0):
            return False

        return True


class Anonymous(AnonymousUserMixin):
    def __init__(self):
        self.id = 0
        self.access = USER_ACCESS['guest']

    def has_access(self, access):
        return False

    def can_answer(self, q):
        return False


class Avatar(Base):
    __tablename__ = 'avatars'

    id = Column(Integer, primary_key=True)
    u_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    ext = Column(String, nullable=False)
