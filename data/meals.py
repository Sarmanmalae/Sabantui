import sqlalchemy
from sqlalchemy import orm

from data.db_session import SqlAlchemyBase


class Meals(SqlAlchemyBase):
    __tablename__ = 'menu'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String)
    shop_id = sqlalchemy.Column(sqlalchemy.Integer,
                                sqlalchemy.ForeignKey("shops.id"))
    shop = orm.relation('Shops')
    category = sqlalchemy.Column(sqlalchemy.String)
    price = sqlalchemy.Column(sqlalchemy.Integer)
    pic = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    in_stock = sqlalchemy.Column(sqlalchemy.Boolean)

