# for Migrations :
    # alembic revision --autogenerate -m "migration description"
    # alembic upgrade head


from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, BigInteger
from sqlalchemy import DateTime
from sqlalchemy.orm import relationship, Session
from sqlalchemy.ext.declarative import declarative_base, declared_attr
import random
import string
from datetime import datetime, timedelta

Base = declarative_base()

class BaseModel:
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    id = Column(Integer, primary_key=True, autoincrement=True)

    @classmethod
    def get_or_create(cls, session: Session, defaults=None, **kwargs):
        instance = session.query(cls).filter_by(**kwargs).first()
        if instance:
            params = {**kwargs}
            if defaults:
                params.update(defaults)
            for key, value in params.items():
                setattr(instance, key, value)
            session.commit()
            return instance, False
        else:
            params = {**kwargs}
            if defaults:
                params.update(defaults)
            instance = cls(**params)
            session.add(instance)
            session.commit()
            return instance, True

class User(Base, BaseModel):
    __tablename__ = 'telegram_bot_user'
    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger, nullable=False, unique=True)
    first_name = Column(String(100))
    last_name = Column(String(100))
    username = Column(String(100))
    is_active = Column(Boolean, default=True)
    invite_code = Column(String(10), unique=True)
    inviter_id = Column(Integer, ForeignKey('telegram_bot_user.id'))
    visit_site = Column(Boolean, default=False)
    
    inviter = relationship('User', remote_side=[id], backref='invitees')

    def generate_invite_code(self, session):
        while True:
            characters = string.ascii_letters + string.digits
            invite_code = ''.join(random.choice(characters) for _ in range(10))
            existing_user = session.query(User).filter_by(invite_code=invite_code).first()
            if not existing_user:
                break
        return invite_code
    
    def __repr__(self):
        return f"<User {self.first_name} {self.last_name} (Invite Code: {self.invite_code})>"

class Token(Base, BaseModel):
    __tablename__ = 'telegram_bot_token'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('telegram_bot_user.id'), nullable=False)
    token = Column(String(50), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    expires_at = Column(DateTime, default=lambda: datetime.now() + timedelta(minutes=2))
    is_used = Column(Boolean, default=False)

    user = relationship('User', backref='tokens')
