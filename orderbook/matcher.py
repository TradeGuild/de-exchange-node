from interface import *
from kafka_util import get_trade_producer, get_order_consumer

MIN_TRADE = 0.01
PAIR = 'BTCUSD'

Trade = namedtuple('Trade', 'pair price amount bid_id ask_id')

trade_producer = get_trade_producer()
order_consumer = get_order_consumer()


def sort_orders_by_priority(bid, ask):
    """
    Sort the two orders given by priority then by time. Will return a set of both with the items in descending order.

    :param Order bid:
    :param Order ask:
    :return: a set of two orders in descending priority
    """
    if bid.priority < ask.priority:
        return bid, ask
    elif ask.priority < bid.priority:
        return ask, bid
    else:
        if bid.time < ask.time:
            return bid, ask
        elif ask.time < bid.time:
            return ask, bid
        else:
            return bid, ask


def match_orders(notify=True):
    """
    Match orders to create a trade, if possible.

    :return: Trade or None
    """
    bid = get_next_order('bid')
    if bid is None:
        return
    ask = get_next_order('ask')
    if ask is None:
        return
    elif ask.price <= bid.price:
        horder, lorder = sort_orders_by_priority(bid, ask)
        trade_amount = min(bid.amount, ask.amount)
        trade = Trade(PAIR, lorder.price, trade_amount, bid.id, ask.id)
        # print "creating trade %s" % repr(trade)
        if bid.amount - trade_amount == 0:
            # print "removing bid %s" % bid.id
            rem_order('bid', create_order_key(bid))
        else:
            newbid = create_order('bid', bid.price, bid.priority, bid.time, bid.amount-trade_amount, bid.id)
            # print "updating bid to %s" % repr(newbid)
            update_order(newbid)
        if ask.amount - trade_amount == 0:
            # print "removing ask %s" % ask.id
            rem_order('ask', create_order_key(ask))
        else:
            newask = create_order('ask', ask.price, ask.priority, ask.time, ask.amount-trade_amount, ask.id)
            # print "updating ask to %s" % repr(newask)
            update_order(newask)
        if notify:
            # TODO save trade here and then send an id, or send whole trade?
            trade_producer.send_messages('trade', json.dumps(trade))
        return trade
    return


def run():
    for message in order_consumer:
        run_simple()


def run_simple():
    while match_orders():
            pass


if __name__ == '__main__':
    run()
