from sqlalchemy import Column, String, ForeignKey, BigInteger

from db_config import Base

class Users(Base):
    __tablename__ = 'users'

    id = Column(BigInteger(), primary_key=True, autoincrement=True)
    username = Column(String(15), nullable=False, unique=True)
    email = Column(String(50), nullable=False, unique=True)
    password = Column(String(), nullable=False)
    public_id = Column(String(), unique=True)

    def as_dict(self):
        obj_dict = {}
        for c in self.__table__.columns:
            obj_dict[c.name] = getattr(self, c.name)
        return obj_dict

    def __repr__(self):
        return f'<User id={self.id} username={self.username} password={self.password}' \
               f' public id={self.public_id}>'

    def __str__(self):
        return self.__repr__()
