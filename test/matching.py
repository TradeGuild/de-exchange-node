import os
import threading
import sys
import unittest
import uuid
import redis
import time

red = redis.StrictRedis()
red_sub = red.pubsub()
HERE = os.path.dirname(os.path.abspath(__file__))
OB_DIR = os.path.join(os.path.dirname(HERE), 'dex_node')

sys.path.append('../')
from dex_node.matcher import match_orders, Trade, trade_mq_client, mrunner
from dex_node.interface import get_next_order, BookOrder, insert_many_orders, create_book_order


class MatchOrders(unittest.TestCase):
    def setUp(self):
        red.flushall()

    def test_match_equal(self):
        insert_many_orders([create_book_order('bid', 240, 0.0, str(round(time.time(), 2)), 0.1, str(uuid.uuid4())),
                            create_book_order('ask', 240, 0.0, str(round(time.time(), 2)), 0.1, str(uuid.uuid4()))])
        trade = match_orders()
        self.assertIsNotNone(trade)
        self.assertIsInstance(trade, Trade)
        bid = get_next_order('bid')
        self.assertIsNone(bid)
        ask = get_next_order('ask')
        self.assertIsNone(ask)

    def test_match_different_amounts(self):
        insert_many_orders([create_book_order('bid', 240, 0.0, str(round(time.time(), 2)), 0.2, str(uuid.uuid4())),
                            create_book_order('ask', 240, 0.0, str(round(time.time(), 2)), 0.1, str(uuid.uuid4()))])
        trade = match_orders()
        self.assertIsNotNone(trade)
        self.assertIsInstance(trade, Trade)
        bid = get_next_order('bid')
        self.assertIsNotNone(bid)
        self.assertIsInstance(bid, BookOrder)
        self.assertEqual(bid.amount, 0.1)
        ask = get_next_order('ask')
        self.assertIsNone(ask)

    def test_match_different_prices_priority(self):
        insert_many_orders([create_book_order('bid', 242, 1.0, str(round(time.time(), 2)), 0.1, str(uuid.uuid4())),
                            create_book_order('ask', 240, 0.0, str(round(time.time(), 2)), 0.1, str(uuid.uuid4()))])
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
        insert_many_orders([create_book_order('bid', 242, 0.0, t1, 0.1, str(uuid.uuid4())),
                            create_book_order('ask', 240, 0.0, t2, 0.1, str(uuid.uuid4()))])
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
            book.append(create_book_order('bid', 250, 0.0, round(time.time(), 2), 0.1, uuid.uuid4()))
            book.append(create_book_order('ask', 250, 0.0, round(time.time(), 2), 0.1, uuid.uuid4()))
        t1 = time.time()
        insert_many_orders(book)
        t2 = time.time()
        while match_orders():
            pass
        t3 = time.time()
        self.assertLessEqual(t2 - t1, 3)  # calibrated on Ira's laptop then doubled for margin
        self.assertLessEqual(t3 - t2, 30)  # calibrated on Ira's laptop then doubled for margin
        print "time to insert 100k orders: %s" % (t2 - t1)
        print "time to process 100k orders: %s" % (t3 - t2)


class MatchThread(threading.Thread):

   def run(self):
      trade_mq_client.run()

class MatchOrdersQueue(unittest.TestCase):
    def setUp(self):
        red.flushall()
        MatchThread().start()

    def test_speed_queue(self):
        book = []
        for i in range(0, 50000):
            book.append(create_book_order('bid', 250, 0.0, round(time.time(), 2), 0.1, uuid.uuid4()))
            book.append(create_book_order('ask', 250, 0.0, round(time.time(), 2), 0.1, uuid.uuid4()))
        t1 = time.time()
        insert_many_orders(book)
        t2 = time.time()
        while 1:
            bid = get_next_order('bid')
            ask = get_next_order('ask')
            #print "bid: %s\task: %s" % (bid, ask)
            if bid is None or ask is None:
                break
            elif time.time() > t2 + 120:
                self.fail("took too long to process orders")
            else:
                time.sleep(0.1)
        t3 = time.time()
        self.assertLessEqual(t2 - t1, 3)  # calibrated on Ira's laptop then doubled for margin
        self.assertLessEqual(t3 - t2, 120)  # calibrated on Ira's laptop then doubled for margin

        print "time to insert 100k orders: %s" % (t2 - t1)
        print "time to process 100k orders (w/queue): %s" % (t3 - t2)

    def tearDown(self):
        trade_mq_client.stop()
        mrunner.stop()

if __name__ == "__main__":
    unittest.main()
