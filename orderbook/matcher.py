import time
import uuid
from interface import *

MIN_TRADE = 0.01
PAIR = 'BTCUSD'

Trade = namedtuple('Trade', 'pair price amount bid_id ask_id')


def sort_orders_by_priority(bid, ask):
    """
    Sort the two orders given by priority then by time. Will return a set of both with the items in descending order.

    :param Order bid:
    :param Order ask:
    :return: a set of two orders in descending priority
    """
    if bid.priority > ask.priority:
        return bid, ask
    elif ask.priority > bid.priority:
        return ask, bid
    else:
        if bid.time < ask.time:
            return bid, ask
        elif ask.time < bid.time:
            return ask, bid
        else:
            return bid, ask


def match_orders():
    bid = get_next_order('bid')
    ask = get_next_order('ask')
    if bid is None or ask is None:
        return False
    if ask.price <= bid.price:
        horder, lorder = sort_orders_by_priority(bid, ask)
        bid_amount = bid.amount
        ask_amount = ask.amount
        trade_amount = min(bid_amount, ask_amount)
        trade = Trade(PAIR, lorder.price, trade_amount, bid.id, ask.id)
        # print "creating trade %s" % repr(trade)
        bid_remainder = bid_amount - trade_amount
        ask_remainder = ask_amount - trade_amount
        if bid_remainder == 0:
            # print "removing bid %s" % bid.id
            rem_order('bid', create_order_key(bid))
        else:
            newbid = create_order('bid', bid.price, bid.priority, bid.time, bid_amount-trade_amount, bid.id)
            # print "updating bid to %s" % repr(newbid)
            update_order(newbid)
        if ask_remainder == 0:
            # print "removing ask %s" % ask.id
            rem_order('ask', create_order_key(ask))
        else:
            newask = create_order('ask', ask.price, ask.priority, ask.time, ask_amount-trade_amount, ask.id)
            # print "updating ask to %s" % repr(newask)
            update_order(newask)

    return True


if __name__ == '__main__':
    import sys
    sys.path.append('../test')
    from util import create_order_book
    red.flushall()

    # insert_many_orders([create_order('bid', 240, 1.0, str(round(time.time(), 2)), 0.2, str(uuid.uuid4())),
    #                     create_order('ask', 238, 0.0, str(round(time.time(), 2)), 0.1, str(uuid.uuid4()))])
    create_order_book(price=250.0, tsize=0.1, size=10, overlap=10, priority=1.0)
    create_order_book(price=250.0, tsize=0.2, size=10, overlap=5, priority=0.0)
    while 1:
        if not match_orders():
            print("processed all orders")
            exit()
