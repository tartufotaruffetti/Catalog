'''
Created on 31/08/2015

@author: juan
'''
import os
import sys
import datetime
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Text, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
 
Base = declarative_base()

class User(Base):
    __tablename__ = 'user'
   
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(750), nullable=True)

class Category(Base):
    __tablename__ = 'category'
   
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    user_id = Column(Integer,ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
       """Return object data in easily serializeable format"""
       return {
           'name'         : self.name,
           'id'           : self.id,
       }
 
class CategoryItem(Base):
    __tablename__ = 'category_item'


    title =Column(String(80), nullable = False)
    id = Column(Integer, primary_key = True)
    description = Column(String(250))
    category_id = Column(Integer,ForeignKey('category.id'))
    category = relationship(Category)
    user_id = Column(Integer,ForeignKey('user.id'))
    user = relationship(User)
    image = Column(Text, default="")
    image_data = Column(LargeBinary, nullable = True)
    creation_date = Column(DateTime, default=datetime.datetime.utcnow)


    @property
    def serialize(self):
       """Return object data in easily serializeable format"""
       return {
           'title'         : self.title,
           'description'         : self.description,
           'id'         : self.id
       }

engine = create_engine('sqlite:///catalog.db')
 

Base.metadata.create_all(engine)
