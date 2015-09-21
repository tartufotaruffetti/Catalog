import os
import sys
import datetime
from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy import String, DateTime, Text, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

# creating the base
Base = declarative_base()


# creating the User table
class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(750), nullable=True)


# creating the Category table
class Category(Base):
    __tablename__ = 'category'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    # setting the ON DELETE CASCADE
    category_item = relationship(
        "CategoryItem",
        backref="categoria",
        cascade="all, delete, delete-orphan"
    )

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return
        {
            'name': self.name,
            'id': self.id
        }


# creating the Items table
class CategoryItem(Base):
    __tablename__ = 'category_item'

    title = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    description = Column(String(250))
    category_id = Column(Integer, ForeignKey('category.id'))
    category = relationship(Category)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)
    image = Column(Text, default="")
    image_data = Column(LargeBinary, nullable=True)
    creation_date = Column(DateTime, default=datetime.datetime.utcnow)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return
        {
            'title': self.title,
            'description': self.description,
            'id': self.id
        }


engine = create_engine('sqlite:///catalogitem1.db')


Base.metadata.create_all(engine)
