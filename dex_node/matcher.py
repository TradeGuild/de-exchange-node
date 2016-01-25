from interface import *
from mq_client import AsyncMQPublisher

Trade = namedtuple('Trade', 'pair price amount bid_id ask_id')

MIN_TRADE = 0.01
PAIR = 'BTCUSD'

# Set up message queue client
EXCHANGE = 'exchange_matcher'
EXCHANGE_TYPE = 'fanout'
TRADE_ROUTING_KEY = "exchange_trades"
CLIENT_BROKER_URL = "amqp://guest:guest@localhost:5672/%2F" # %2F is "/" encoded

class MatchRunner(object):

    def __init__(self):
        self._keep_alive = True

    def run(self, client):
        while self._keep_alive:
            trade = match_orders()
            if trade is not None:
                client.publish(json.dumps(trade))
            else:
                time.sleep(0.1)

    def stop(self):
        self._keep_alive = False

mrunner = MatchRunner()

trade_mq_client = AsyncMQPublisher(CLIENT_BROKER_URL,
                                   mrunner.run,
                                   exchange=EXCHANGE,
                                   exchange_type=EXCHANGE_TYPE,
                                   routing_key=TRADE_ROUTING_KEY,
                                   content_type='text/plain')


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


def match_orders():
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
        if bid.amount - trade_amount == 0:
            rem_order('bid', create_order_key(bid))
        else:
            newbid = create_book_order('bid', bid.price, bid.priority, bid.time, bid.amount-trade_amount, bid.id)
            update_order(newbid)
        if ask.amount - trade_amount == 0:
            rem_order('ask', create_order_key(ask))
        else:
            newask = create_book_order('ask', ask.price, ask.priority, ask.time, ask.amount-trade_amount, ask.id)
            update_order(newask)
        return trade
    return


if __name__ == '__main__':
    trade_mq_client.run()

