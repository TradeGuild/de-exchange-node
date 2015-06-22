from collections import namedtuple
import json
import redis
import redis_keys

red = redis.StrictRedis()
red_sub = red.pubsub()

Order = namedtuple('Order', 'side price priority time amount id')


def get_ticker():
    """
    Return the current ticker based on the fully merged orderbook (merged
    external + internal orderbook).
    """
    ticker = red.get(redis_keys.RKEY['ticker'])
    if ticker is None:
        raise Exception("no ticker available")
    return json.loads(ticker)


def pop_next_order(side='bid'):
    """
    Get the next order, using the following priorities in descending order: priority, price, time, amount, order id

    :rtype: dict
    :return:
    """
    if side == 'bid':
        raw_order = red.zrevrange(redis_keys.RKEY['book_side'] % side, 0, 1, withscores=True)
    else:
        raw_order = red.zrange(redis_keys.RKEY['book_side'] % side, 0, 1, withscores=True)
    if raw_order is None or len(raw_order) == 0:
        return None
    order_key = raw_order[0][0]
    price = raw_order[0][1]
    olist = order_key.split(redis_keys.SEP)
    order = Order(side, price, *olist)
    red.zrem(redis_keys.RKEY['book_side'] % side, order_key)
    return order


def create_order_key(order):
    return redis_keys.RKEY['book_member'] % (order.priority, order.time, order.amount, order.id)


def insert_order(order, **kwargs):
    """
    Insert a single order.
    """
    insert_many_orders([order], **kwargs)


def insert_many_orders(orders):
    """
    Insert a list of orders.

    :rtype: None
    """
    bids = []
    asks = []
    for order in orders:
        if order.side == 'bid':
            bids.append(order.price)
            bids.append(create_order_key(order))
        if order.side == 'ask':
            asks.append(order.price)
            asks.append(create_order_key(order))

    if len(bids) > 0:
        #print "zadding %s" % bids
        red.zadd(redis_keys.RKEY['book_side'] % 'bid', *bids)
    if len(asks) > 0:
        #print "zadding %s" % asks
        red.zadd(redis_keys.RKEY['book_side'] % 'ask', *asks)
