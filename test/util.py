import sys
import time
import uuid

sys.path.append('../orderbook')

from interface import insert_many_orders, Order


def create_order_book(price=500.0, tsize=0.1, size=10, overlap=0, priority=0.0):
    bids = []
    asks = []
    for i in range(0, size):
        bid = Order('bid', priority, str(price * (1.0 - float(i - overlap) / 100.0)),
                    str(round(time.time(), 2)), str(tsize), str(uuid.uuid4()))

        ask = Order('ask', priority, str(price * (1.0 + float(i - overlap) / 100.0)),
                    str(round(time.time(), 2)), str(tsize), str(uuid.uuid4()))

        bids.append(bid)
        asks.append(ask)
        insert_many_orders([bid, ask])
    return {'bids': bids, 'asks': asks}