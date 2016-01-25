import datetime
import sqlalchemy as sa
import sqlalchemy.orm as orm
from flask.ext.login import UserMixin
from sqlalchemy_login_models.model import UserKey, User as SLM_User
from sqlalchemy_login_models import Base

__all__ = ['Order',
           'OrderRequest',
           'Payment',
           'PaymentRequest',
           'Trade']


class PaymentRequest(Base):
    """a request to pay another user of de shared wallet"""

    currency = sa.Column(sa.String(3), nullable=False)
    amount = sa.Column(sa.Integer, nullable=False)
    time = sa.Column(sa.DateTime, default=datetime.datetime.utcnow)
    ref_id = sa.Column(sa.Integer, nullable=True, doc="reference id")

    #recipient_id = sa.Column(sa.String(120), sa.ForeignKey('user.id'), nullable=False)
    #recipient = orm.relationship("User")

    #sender_id = sa.Column(sa.String(120), sa.ForeignKey('user.id'), nullable=False)
    #sender = orm.relationship("User")

    def __repr__(self):
        return "<PaymentRequest(id=%s, currency='%s', amount=%s," +\
               "sender='%s', recipient='%s')>" % (self.id, self.currency,
                                              self.amount, self.sender_id, 
                                              self.recipient)


class Payment(Base):
    """a payment via de shared wallet"""

    currency = sa.Column(sa.String(3), nullable=False)
    amount = sa.Column(sa.Integer, nullable=False)
    time = sa.Column(sa.DateTime, default=datetime.datetime.utcnow)
    ref_id = sa.Column(sa.Integer, nullable=True, doc="reference id")
    state = sa.Column(sa.Enum("requested", "canceled", "complete"), 
                      nullable=False)

    #recipient_id = sa.Column(sa.String(120), sa.ForeignKey('user.id'), nullable=False)
    #recipient = orm.relationship("User")

    #sender_id = sa.Column(sa.String(120), sa.ForeignKey('user.id'), nullable=False)
    #sender = orm.relationship("User")

    def __repr__(self):
        return "<Payment(id=%s, currency='%s', amount=%s, state='%s', " +\
               "sender='%s', recipient='%s')>" % (self.id, self.currency,
                                                  self.amount,
                                                  self.state,
                                                  self.sender_id,
                                                  self.recipient)


class OrderRequest(Base):
    """a request to create a de exchange node order"""

    pair = sa.Column(sa.String(6), nullable=False)
    side = sa.Column(sa.String(3), nullable=False)
    amount = sa.Column(sa.Integer, nullable=False)
    price = sa.Column(sa.Integer, nullable=False)
    time = sa.Column(sa.DateTime, default=datetime.datetime.utcnow)
#    pay_req = sa.Column(sa.String(255), nullable=False,
#                        doc="A signed PaymentRequest to forward to De Shared "+\
#                            "Wallet for funding the Order.")

    user_id = sa.Column(sa.String(120), sa.ForeignKey('user.id'), nullable=False)
    user = orm.relationship("User")

    def __repr__(self):
        return "<OrderRequest(id=%s, pair='%s', side='%s', amount=%s," +\
               "price=%s)>" % (self.id, self.pair, self.side, self.amount, 
                               self.price)


class Order(Base):
    """a de exchange node order"""

    pair = sa.Column(sa.String(6), nullable=False)
    side = sa.Column(sa.String(3), nullable=False)
    amount = sa.Column(sa.Integer, nullable=False)
    price = sa.Column(sa.Integer, nullable=False)
    time = sa.Column(sa.DateTime, default=datetime.datetime.utcnow)
    state = sa.Column(sa.Enum("requested", "unfunded", "active", "partial",
                              "filled", "refunded"), nullable=False)

    user_id = sa.Column(sa.String(120), sa.ForeignKey('user.id'), nullable=False)
    user = orm.relationship("User")

    payment_id = sa.Column(sa.Integer, sa.ForeignKey('payment.id'), nullable=True)
    payment = orm.relationship("Payment")

    def __repr__(self):
        return "<Order(id=%s, pair='%s', side='%s', amount=%s, price=%s)>" % (self.id, self.pair, self.side,
                                                                              self.amount, self.price)


class Trade(Base):
    """a de exchange node trade"""

    pair = sa.Column(sa.String(6), nullable=False)
    amount = sa.Column(sa.Integer, nullable=False)
    price = sa.Column(sa.Integer, nullable=False)
    #ask_id = sa.Column(sa.Integer, sa.ForeignKey('order.id'), nullable=False)
    #ask = orm.relationship("Order")
    #bid_id = sa.Column(sa.Integer, sa.ForeignKey('order.id'), nullable=False)
    #bid = orm.relationship("Order")

    def __repr__(self):
        return "<Trade(id=%s, pair='%s', amount=%s, price=%s)>" % (self.id, self.pair, self.amount, self.price)

