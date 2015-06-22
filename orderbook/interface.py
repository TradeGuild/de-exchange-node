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


def get_next_order(side='bid', pop=False):
    """
    Get the next order, using the following priorities in descending order: priority, price, time, amount, order id

    :param str side: The side 'bid' or 'ask' to get from
    :param bool pop: Remove the order after getting
    :rtype: dict
    :return:
    """
    if side == 'bid':
        raw_order = red.zrevrange(redis_keys.RKEY['book_side'] % side, 0, 0, withscores=True)
    else:
        raw_order = red.zrange(redis_keys.RKEY['book_side'] % side, 0, 0, withscores=True)
    if raw_order is None or len(raw_order) == 0:
        return None
    order = decode_order(side, raw_order)
    if pop:
        order_key, price = get_order_details(raw_order)
        rem_order(side, order_key)
    return order


def get_order_details(raw_order):
    if len(raw_order) == 1 and len(raw_order[0]) > 0:
        return raw_order[0]


def decode_order(side, raw_order):
    if len(raw_order) == 2 and isinstance(raw_order[0], str) and isinstance(raw_order[1], float):
        order_key = raw_order[0]
        price = raw_order[1]
    else:
        order_key, price = get_order_details(raw_order)
    olist = order_key.split(redis_keys.SEP)
    return Order(side, price, *olist)


def rem_order(side, order_key):
    red.zrem(redis_keys.RKEY['book_side'] % side, order_key)


def update_order(order, upsert=True):
    orders = red.zrangebyscore(redis_keys.RKEY['book_side'] % order.side, order.price, order.price, withscores=True)
    # print "updating order %s" % repr(order)
    found = False
    for o in orders:
        ord = decode_order(order.side, o)
        if ord.id == str(order.id):
            found = True
            pipe = red.pipeline()
            pipe.zrem(redis_keys.RKEY['book_side'] % order.side, o[0])
            pipe.zadd(redis_keys.RKEY['book_side'] % order.side, order.price, create_order_key(order))
            pipe.execute()
    if not found and upsert:
        red.zadd(redis_keys.RKEY['book_side'] % order.side, order)


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
