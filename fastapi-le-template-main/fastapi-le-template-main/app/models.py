from sqlmodel import Field, SQLModel, Relationship
from typing import Optional, List
from pydantic import EmailStr
from pwdlib import PasswordHash
from datetime import datetime

class UserBase(SQLModel,):
    username: str = Field(index=True, unique=True)
    email: EmailStr = Field(index=True, unique=True)
    password: str

class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    comments: List["Comment"] = Relationship(back_populates="user")
    reactions: List["Reaction"] = Relationship(back_populates="user")

    def check_password(self, plaintext_password:str):
        return PasswordHash.recommended().verify(password=plaintext_password, hash=self.password)


# FEATURE: View Albums - Stores music album information
class AlbumBase(SQLModel):
    title: str = Field(index=True)
    artist: str = Field(index=True)
    release_year: Optional[int] = None
    description: Optional[str] = None

class Album(AlbumBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    tracks: List["Track"] = Relationship(back_populates="album")


# FEATURE: View Album Tracks - Individual songs within an album
class TrackBase(SQLModel):
    title: str = Field(index=True)
    duration: int  # duration in seconds
    album_id: int = Field(foreign_key="album.id")

class Track(TrackBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    album: Album = Relationship(back_populates="tracks")
    comments: List["Comment"] = Relationship(back_populates="track")
    reactions: List["Reaction"] = Relationship(back_populates="track")


# FEATURE: Comment on Track & Delete Comment - Users can add/delete comments on tracks
class CommentBase(SQLModel):
    content: str
    track_id: int = Field(foreign_key="track.id")
    user_id: int = Field(foreign_key="user.id")

class Comment(CommentBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    track: Track = Relationship(back_populates="comments")
    user: User = Relationship(back_populates="comments")


# FEATURE: View Track Reactions & React to Track - Users can like/dislike tracks
class ReactionBase(SQLModel):
    reaction_type: str  # "like" or "dislike"
    track_id: int = Field(foreign_key="track.id")
    user_id: int = Field(foreign_key="user.id")

class Reaction(ReactionBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    track: Track = Relationship(back_populates="reactions")
    user: User = Relationship(back_populates="reactions")