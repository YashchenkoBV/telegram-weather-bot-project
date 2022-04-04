import sqlalchemy
from .db_session import SqlAlchemyBase


class User(SqlAlchemyBase):
    __tablename__ = 'geoloctaion'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    password = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    latest_city = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    constant_city = sqlalchemy.Column(sqlalchemy.String, nullable=True)