import sys
import threading
import time
import uuid
from orderbook.kafka_util import get_order_consumer

sys.path.append('../')
from orderbook.interface import insert_many_orders, Order, create_order
from orderbook.matcher import match_orders


def create_order_book(price=500.0, tsize=0.1, size=10, offset=0, priority=0.0, insert=True):
    bids = []
    asks = []
    for i in range(0, size):
        base_price = price * (1 + (float(i) / float(size)) / 2)
        bid = create_order('bid', base_price + offset, priority,
                           round(time.time(), 2), tsize, uuid.uuid4())

        ask = Order('ask', base_price - offset, priority,
                    round(time.time(), 2), tsize, uuid.uuid4())

        bids.append(bid)
        asks.append(ask)
        if insert:
            insert_many_orders([bid, ask])
    return {'bids': bids, 'asks': asks}


class OrderConsumer(threading.Thread):
    daemon = False

    def run(self):
        for message in get_order_consumer():
            if message.message.value == 'terminate':
                return
            while match_orders():
                pass


threads = [
    OrderConsumer()
]


def run_consumers():
    for t in threads:
        t.start()
