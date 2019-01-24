#!/usr/bin/python3
import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()


# Class that stores user information


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    image = Column(String(250))


# Class to store book information


class Book(Base):
    __tablename__ = 'books'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    author = Column(String(250), nullable=False)
    cover = Column(String(450), nullable=False)
    description = Column(String(), nullable=False)
    categories = Column(String(100), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'id': self.id,
            'name': self.name,
            'author': self.author,
            'categories': self.categories,
            'cover': self.cover,
            'description': self.description,
        }


engine = create_engine('sqlite:///itemcatalog.db')
Base.metadata.create_all(engine)
