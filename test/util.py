import sys
import time
import uuid
import unittest

sys.path.append('../')
from dex_node.interface import insert_many_orders, BookOrder, create_book_order

def create_order_book(price=500.0, tsize=0.1, size=10, offset=0, priority=0.0, insert=True):
    bids = []
    asks = []
    for i in range(0, size):
        base_price = price * (1 + (float(i) / float(size)) / 2)
        bid = create_book_order('bid', base_price + offset, priority,
                           round(time.time(), 2), tsize, uuid.uuid4())

        ask = BookOrder('ask', base_price - offset, priority,
                    round(time.time(), 2), tsize, uuid.uuid4())

        bids.append(bid)
        asks.append(ask)
        if insert:
            insert_many_orders([bid, ask])
    return {'bids': bids, 'asks': asks}

