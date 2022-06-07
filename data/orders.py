import sqlalchemy
from sqlalchemy import orm
import datetime

from data.db_session import SqlAlchemyBase


class Orders(SqlAlchemyBase):
    __tablename__ = 'orders'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    client_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id"))
    shop_order_num = sqlalchemy.Column(sqlalchemy.Integer)
    meals = sqlalchemy.Column(sqlalchemy.String)
    itog_price = sqlalchemy.Column(sqlalchemy.Integer)
    date = sqlalchemy.Column(sqlalchemy.DateTime,
                             default=datetime.datetime.now)
    shop_id = sqlalchemy.Column(sqlalchemy.Integer)
    is_ready = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    news = orm.relation("Users")
