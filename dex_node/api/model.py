import sqlalchemy as sa
import sqlalchemy.orm as orm
from flask.ext.login import UserMixin
from sqlalchemy_login_models.model import Base, UserKey, User as SLM_User


__all__ = ['Coin']


# an initially unfunded order
class Order(Base):
    """a de exchange node order"""
    __tablename__ = "order"
    __name__ = __tablename__

    id = sa.Column(sa.Integer, primary_key=True, doc="primary key")
    pair = sa.Column(sa.String(6), nullable=False)
    side = sa.Column(sa.String(3), nullable=False)
    amount = sa.Column(sa.Integer, nullable=False)
    price = sa.Column(sa.Integer, nullable=False)
    time = sa.Column(sa.DateTime, nullable=False)

    user_id = sa.Column(sa.String(120), sa.ForeignKey('user.id'), nullable=False)
    user = orm.relationship("User")

    # TODO import actual invoice model
    #invoice_id = sa.Column(sa.Integer, sa.ForeignKey('invoice.id'), nullable=False)
    #invoice = orm.relationship("Invoice")

    # TODO import actual invoice model
    #payment_id = sa.Column(sa.Integer, sa.ForeignKey('payment.id'), nullable=False)
    #payment = orm.relationship("Invoice")
    
    #quote_id = sa.Column(sa.Integer, sa.ForeignKey('quote.id'), nullable=False)
    #quote = orm.relationship("Quote")

    def __repr__(self):
        return "<Order(id=%s, pair='%s', side='%s', amount=%s, price=%s)>" % (self.id, self.pair, self.side,
                                                                              self.amount, self.price)


# after receiving an invoice paid event, create one of these and add order to book
class OrderFunded(Base):
    """a de exchange node order funded event"""
    __tablename__ = "orderfunded"
    __name__ = __tablename__

    id = sa.Column(sa.Integer, primary_key=True, doc="primary key")
    pair = sa.Column(sa.String(6), nullable=False)
    side = sa.Column(sa.String(3), nullable=False)
    amount = sa.Column(sa.Integer, nullable=False)
    price = sa.Column(sa.Integer, nullable=False)
    time = sa.Column(sa.DateTime, nullable=False)
    user_id = sa.Column(sa.String(120), sa.ForeignKey('user.id'), nullable=False)
    user = orm.relationship("User")
    
    # TODO import actual invoice model
    #invoice_id = sa.Column(sa.Integer, sa.ForeignKey('invoice.id'), nullable=False)
    #invoice = orm.relationship("Invoice")

    # include the signature proving funding
    invoice_signature = sa.Column(sa.String(120), nullable=False)

    def __repr__(self):
        return "<Order(id=%s, pair='%s', side='%s', amount=%s, price=%s)>" % (self.id, self.pair, self.side,
                                                                              self.amount, self.price)


class Trade(Base):
    """a de exchange node trade"""
    __tablename__ = "trade"
    __name__ = __tablename__

    id = sa.Column(sa.Integer, primary_key=True, doc="primary key")
    pair = sa.Column(sa.String(6), nullable=False)
    amount = sa.Column(sa.Integer, nullable=False)
    price = sa.Column(sa.Integer, nullable=False)
    ask_id = sa.Column(sa.Integer, sa.ForeignKey('order.id'), nullable=False)
    ask = orm.relationship("Order")
    bid_id = sa.Column(sa.Integer, sa.ForeignKey('order.id'), nullable=False)
    bid = orm.relationship("Order")

    def __repr__(self):
        return "<Trade(id=%s, pair='%s', amount=%s, price=%s)>" % (self.id, self.pair, self.amount, self.price)

