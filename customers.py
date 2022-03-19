from sqlalchemy import Column, String, BigInteger

from db_config import Base


class Customers(Base):
    __tablename__ = 'customers'

    id = Column(BigInteger(), primary_key=True, autoincrement=True)
    name = Column(String(70), nullable=False)
    address = Column(String(70), nullable=False)

    def as_dict(self):
        obj_dict = {}
        for c in self.__table__.columns:
            obj_dict[c.name] = getattr(self, c.name)
        return obj_dict

    def __repr__(self):
        return f'\n<Customer_id={self.id}, name={self.name}, address={self.address},'

    def __str__(self):
        return self.__repr__()
