from kafka.client import KafkaClient
from kafka.consumer import SimpleConsumer
from kafka.producer import SimpleProducer


client = KafkaClient("0.0.0.0:9092")


# The batch_send_every_n of 10 and batch_send_every_t of 5 look like they will allow a significant performance bump.
# http://kafka.apache.org/07/performance.html
def get_trade_producer():
    return SimpleProducer(client, async=True, batch_send_every_n=10, batch_send_every_t=5)


def get_trade_consumer():
    return SimpleConsumer(client, "notification", "trade")


# The batch_send_every_n of 1 is to stop the default batching of orders. Even though this would improve
# messaging performance, it would by definition entail holding orders which are otherwise ready for matching.
def get_order_producer():
    return SimpleProducer(client, async=True, batch_send=False, batch_send_every_n=1)


def get_order_consumer():
    return SimpleConsumer(client, "matching", "order")

