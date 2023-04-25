from sqlalchemy import Column, DateTime, Integer, String, Boolean, ForeignKey
from sqlalchemy.sql.expression import func
from sqlalchemy.orm import relationship

from db.db import Base


class User(Base):
    __tablename__ = "db_user"
    id = Column(Integer, primary_key=True)
    username = Column(String(1000), unique=True, nullable=False)
    password = Column(String(1000), nullable=False)
    created_at = Column(
        DateTime, index=True, default=func.now(), nullable=False
    )

    clients = relationship(
        "Client", back_populates="user", cascade="all, delete"
    )

    def __repr__(self):
        return f"User(id={self.id}, {self.username})"


class Client(Base):
    __tablename__ = "db_client"
    id = Column(Integer, primary_key=True)
    host = Column(String(100), nullable=False)
    user_agent = Column(String(1000), nullable=False)
    user_id = Column(ForeignKey("db_user.id"), nullable=True)

    user = relationship("User", back_populates="clients")
    short_url_uses = relationship(
        "ShortenedURLUse", back_populates="client", cascade="all, delete"
    )

    def __repr__(self):
        return f"Client(id={self.id}, host={self.host})"


class ShortenedURL(Base):
    __tablename__ = "db_shortened_url"
    id = Column(Integer, primary_key=True)
    value = Column(String(1000), unique=True, nullable=False)
    original = Column(String(1000), unique=True, nullable=False)
    created_at = Column(
        DateTime, index=True, default=func.now(), nullable=False
    )
    deleted = Column(Boolean, default=False)

    uses = relationship(
        "ShortenedURLUse", back_populates="url", cascade="all, delete"
    )

    def __repr__(self):
        return f"ShortenedURL({self.value}, original={self.original})"


class ShortenedURLUse(Base):
    __tablename__ = "db_shortened_url_use"
    id = Column(Integer, primary_key=True)
    created_at = Column(
        DateTime, index=True, default=func.now(), nullable=False
    )
    url_id = Column(ForeignKey("db_shortened_url.id"), nullable=False)
    client_id = Column(ForeignKey("db_client.id"), nullable=False)

    url = relationship("ShortenedURL", back_populates="uses")
    client = relationship("Client", back_populates="short_url_uses")

    def __repr__(self):
        return f"ShortenedURLUse(url={self.url_id}, client={self.client_id})"
