import os
import subprocess
import sys
import unittest
import uuid
import redis
import time
from util import run_consumers

red = redis.StrictRedis()
red_sub = red.pubsub()

sys.path.append('../')
from orderbook.matcher import match_orders, Trade
from orderbook.interface import get_next_order, Order, insert_many_orders, create_order
from orderbook.kafka_util import get_order_producer

HERE = os.path.dirname(os.path.abspath(__file__))
OB_DIR = os.path.join(os.path.dirname(HERE), 'orderbook')

command = lambda x, **kwargs: subprocess.Popen(x, cwd=OB_DIR, **kwargs)
order_producer = get_order_producer()


class MatchOrders(unittest.TestCase):
    def setUp(self):
        red.flushall()

    def test_match_equal(self):
        insert_many_orders([create_order('bid', 240, 0.0, str(round(time.time(), 2)), 0.1, str(uuid.uuid4())),
                            create_order('ask', 240, 0.0, str(round(time.time(), 2)), 0.1, str(uuid.uuid4()))])
        trade = match_orders()
        self.assertIsNotNone(trade)
        self.assertIsInstance(trade, Trade)
        bid = get_next_order('bid')
        self.assertIsNone(bid)
        ask = get_next_order('ask')
        self.assertIsNone(ask)

    def test_match_different_amounts(self):
        insert_many_orders([create_order('bid', 240, 0.0, str(round(time.time(), 2)), 0.2, str(uuid.uuid4())),
                            create_order('ask', 240, 0.0, str(round(time.time(), 2)), 0.1, str(uuid.uuid4()))])
        trade = match_orders()
        self.assertIsNotNone(trade)
        self.assertIsInstance(trade, Trade)
        bid = get_next_order('bid')
        self.assertIsNotNone(bid)
        self.assertIsInstance(bid, Order)
        self.assertEqual(bid.amount, 0.1)
        ask = get_next_order('ask')
        self.assertIsNone(ask)

    def test_match_different_prices_priority(self):
        insert_many_orders([create_order('bid', 242, 1.0, str(round(time.time(), 2)), 0.1, str(uuid.uuid4())),
                            create_order('ask', 240, 0.0, str(round(time.time(), 2)), 0.1, str(uuid.uuid4()))])
        trade = match_orders()
        self.assertIsNotNone(trade)
        self.assertIsInstance(trade, Trade)
        self.assertEqual(trade.price, 242)
        bid = get_next_order('bid')
        self.assertIsNone(bid)
        ask = get_next_order('ask')
        self.assertIsNone(ask)

    def test_match_different_prices_time(self):
        t1 = str(round(time.time(), 2))
        time.sleep(0.015)
        t2 = str(round(time.time(), 2))
        insert_many_orders([create_order('bid', 242, 0.0, t1, 0.1, str(uuid.uuid4())),
                            create_order('ask', 240, 0.0, t2, 0.1, str(uuid.uuid4()))])
        trade = match_orders()
        self.assertIsNotNone(trade)
        self.assertIsInstance(trade, Trade)
        self.assertEqual(trade.price, 240)
        bid = get_next_order('bid')
        self.assertIsNone(bid)
        ask = get_next_order('ask')
        self.assertIsNone(ask)

    def test_speed(self):
        book = []
        for i in range(0, 50000):
            book.append(create_order('bid', 250, 0.0, round(time.time(), 2), 0.1, uuid.uuid4()))
            book.append(create_order('ask', 250, 0.0, round(time.time(), 2), 0.1, uuid.uuid4()))
        t1 = time.time()
        insert_many_orders(book, notify=False)
        t2 = time.time()
        order_producer.send_messages('order', '')
        while match_orders(notify=False):
            pass
        t3 = time.time()
        self.assertLessEqual(t2 - t1, 3)  # calibrated on Ira's laptop then doubled for margin
        self.assertLessEqual(t3 - t2, 30)  # calibrated on Ira's laptop then doubled for margin
        print "time to insert 100k orders: %s" % (t2 - t1)
        print "time to process 100k orders: %s" % (t3 - t2)

    def test_speed_queue(self):
        run_consumers()
        book = []
        for i in range(0, 50000):
            book.append(create_order('bid', 250, 0.0, round(time.time(), 2), 0.1, uuid.uuid4()))
            book.append(create_order('ask', 250, 0.0, round(time.time(), 2), 0.1, uuid.uuid4()))
        t1 = time.time()
        insert_many_orders(book, notify=False)
        t2 = time.time()
        order_producer.send_messages('order', '')
        # TODO is there a better way to tell when we are done?
        while 1:
            bid = get_next_order('bid')
            ask = get_next_order('ask')
            if bid is None or ask is None:
                break
            elif time.time() > t2 + 60:
                self.fail("took too long to process orders")
        t3 = time.time()
        self.assertLessEqual(t2 - t1, 3)  # calibrated on Ira's laptop then doubled for margin
        self.assertLessEqual(t3 - t2, 60)  # calibrated on Ira's laptop then doubled for margin

        print "time to insert 100k orders: %s" % (t2 - t1)
        print "time to process 100k orders (w/queue): %s" % (t3 - t2)
        order_producer.send_messages('order', 'terminate')


if __name__ == "__main__":
    unittest.main()
