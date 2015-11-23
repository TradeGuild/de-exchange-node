from mq import BlockingMQClient

# Set up message queue client
EXCHANGE = 'exchange_matcher'
EXCHANGE_TYPE = 'fanout'
TRADE_ROUTING_KEY = "exchange_trades"
CLIENT_BROKER_URL = "amqp://guest:guest@localhost:5672/%2F" # %2F is "/" encoded

client = BlockingMQClient(CLIENT_BROKER_URL, EXCHANGE)

def on_message(channel, method, header, body):
    print "consuming\t%s" % body
    # Acknowledge message receipt
    channel.basic_ack(method.delivery_tag)

if __name__ == "__main__":
    mqclient.consume(on_message, queue="test_queue")
