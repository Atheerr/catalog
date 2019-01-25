from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))


class Technology(Base):
    __tablename__ = 'technology'
    name = Column(String(80), nullable=False)
    description = Column(String(250))
    user_id = Column(Integer, ForeignKey('user.id'))
    id = Column(Integer, primary_key=True)
    user = relationship(User)

    @property
    def serialize(self):
        # serialized data for API endpoints
        return {
            'name': self.name,
            'description': self.description,
            'id': self.id,
        }


class TechnologyItem(Base):
    __tablename__ = 'item'
    name = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    author = Column(String(250))
    description = Column(String(250))
    type = Column(String(80), default='COMPUTING')
    price = Column(String(8))
    user_id = Column(Integer, ForeignKey('user.id'))
    technology_id = Column(Integer, ForeignKey('technology.id'))
    technology = relationship(Technology)
    user = relationship(User)

    @property
    def serialize(self):
        # serialized data for API endpoints
        return {
            'name': self.name,
            'author': self.author,
            'description': self.description,
            'type': self.type,
            'price': self.price,
            'id': self.id,
        }


engine = create_engine('postgresql://catalog:password@localhost/catalog')
Base.metadata.create_all(engine)
