import sys
import unittest
import uuid
import redis
import time
from util import create_order_book

red = redis.StrictRedis()
red_sub = red.pubsub()

sys.path.append('../orderbook')

from interface import get_ticker, pop_next_order, Order, insert_order, insert_many_orders


class CreateOrders(unittest.TestCase):
    def setUp(self):
        red.flushall()

    def test_insert_order(self):
        now = str(round(time.time(), 2))
        oid = str(uuid.uuid4())
        amount = str(1.01)
        price = str(240)
        priority = 0.0
        order = Order('bid', priority, price, now, amount, oid)
        insert_order(order)
        time.sleep(0.1)
        got_order = pop_next_order('bid')
        self.assertEqual(got_order, order)

    def test_insert_many_orders(self):
        ask_now = str(round(time.time(), 2))
        bid_now = str(round(time.time(), 2))
        ask_oid = str(uuid.uuid4())
        bid_oid = str(uuid.uuid4())
        amount = str(1.01)
        price = str(240)
        priority = 0.0
        bid = Order('bid', priority, price, bid_now, amount, bid_oid)
        ask = Order('ask', priority, price, ask_now, amount, ask_oid)
        insert_many_orders((bid, ask))
        time.sleep(0.1)
        got_bid = pop_next_order('bid')
        self.assertEqual(got_bid, bid)
        got_ask = pop_next_order('ask')
        self.assertEqual(got_ask, ask)


class GetOrders(unittest.TestCase):
    def setUp(self):
        red.flushall()

    def test_simple_book(self):
        self.orders = create_order_book(price=250.0, tsize=0.1, size=10, overlap=0, priority=0.0)
        lastbid = 300
        lastask = 200
        while True:
            o = pop_next_order('bid')
            print o
            if not o:
                break
            self.assertLessEqual(float(o.price), lastbid)
            lastbid = float(o.price)

        while True:
            o = pop_next_order('ask')
            print o
            if not o:
                break
            self.assertGreaterEqual(float(o.price), lastask)
            lastask = float(o.price)

    def test_priority_sort(self):
        tsize = 1.01
        loworder = Order('ask', 0.0, str(241), str(round(time.time(), 2)), str(tsize), str(uuid.uuid4()))
        mediumorder = Order('ask', 1.0, str(240), str(round(time.time(), 2)), str(tsize), str(uuid.uuid4()))
        highorder = Order('ask', 2.0, str(239), str(round(time.time(), 2)), str(tsize), str(uuid.uuid4()))

        insert_many_orders([loworder, highorder, mediumorder])

        first_got = pop_next_order('ask')
        second_got = pop_next_order('ask')
        third_got = pop_next_order('ask')
        self.assertEqual(first_got, loworder)
        self.assertEqual(second_got, mediumorder)
        self.assertEqual(third_got, highorder)

    def test_price_sort(self):
        tsize = 1.01
        loworder = Order('ask', 0.0, str(239), str(round(time.time(), 2)), str(tsize), str(uuid.uuid4()))
        mediumorder = Order('ask', 0.0, str(240), str(round(time.time(), 2)), str(tsize), str(uuid.uuid4()))
        highorder = Order('ask', 0.0, str(241), str(round(time.time(), 2)), str(tsize), str(uuid.uuid4()))

        insert_many_orders([loworder, highorder, mediumorder])

        first_got = pop_next_order('ask')
        second_got = pop_next_order('ask')
        third_got = pop_next_order('ask')
        self.assertEqual(first_got, loworder)
        self.assertEqual(second_got, mediumorder)
        self.assertEqual(third_got, highorder)

    def test_time_sort(self):
        tsize = 1.01
        loworder = Order('ask', 0.0, str(240), str(round(time.time(), 2)), str(tsize), str(uuid.uuid4()))
        time.sleep(0.1)
        mediumorder = Order('ask', 0.0, str(240), str(round(time.time(), 2)), str(tsize), str(uuid.uuid4()))
        time.sleep(0.1)
        highorder = Order('ask', 0.0, str(240), str(round(time.time(), 2)), str(tsize), str(uuid.uuid4()))

        insert_many_orders([loworder, highorder, mediumorder])

        first_got = pop_next_order('ask')
        second_got = pop_next_order('ask')
        third_got = pop_next_order('ask')
        self.assertEqual(first_got, loworder)
        self.assertEqual(second_got, mediumorder)
        self.assertEqual(third_got, highorder)

    def test_amount_sort(self):
        now = str(round(time.time(), 2))
        loworder = Order('ask', 0.0, str(240), now, str(1), str(uuid.uuid4()))
        time.sleep(0.1)
        mediumorder = Order('ask', 0.0, str(240), now, str(2), str(uuid.uuid4()))
        time.sleep(0.1)
        highorder = Order('ask', 0.0, str(240), now, str(3), str(uuid.uuid4()))

        insert_many_orders([loworder, highorder, mediumorder])

        first_got = pop_next_order('ask')
        second_got = pop_next_order('ask')
        third_got = pop_next_order('ask')
        self.assertEqual(first_got, loworder)
        self.assertEqual(second_got, mediumorder)
        self.assertEqual(third_got, highorder)


if __name__ == "__main__":
    unittest.main()
