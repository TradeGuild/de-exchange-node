import logging
import pika
from pika import adapters
import sys


def publish(client, message):
    """
    If the client is not stopping, publish a message to RabbitMQ.

    :param AsyncMQClient client: The publisher client
    :param str message: The fully encoded message to publish
    """
    if client._stopping:
        return
    properties = pika.BasicProperties(app_id=client._app_id,
                                      content_type=client._content_type,
                                      delivery_mode=1)

    client._channel.basic_publish(client._exchange,
                                  client._routing_key,
                                  message,
                                  properties)


def _on_message(channel, method, header, body):
    """
    Invoked by pika when a message is delivered from RabbitMQ. The
    channel is passed for your convenience. The basic_deliver object that
    is passed in carries the exchange, routing key, delivery tag and
    a redelivered flag for the message. The properties passed in is an
    instance of BasicProperties with the message properties and the body
    is the message that was sent.

    :param pika.channel.Channel channel: The channel object
    :param pika.Spec.Basic.Deliver method: The Deliver method
    :param pika.Spec.BasicProperties properties: The client properties
    :param str|unicode body: The message body
    """
    print "Message:"
    print "\t%r" % method
    print "\t%r" % header
    print "\t%r" % body

    # Acknowledge message receipt
    channel.basic_ack(method.delivery_tag)
    
    # when ready, stop consuming
    channel.stop_consuming()


class BlockingMQClient():
    def __init__(self, url, exchange, exchange_type="direct", routing_key="", 
                 cfg=None):
        self.connection = pika.BlockingConnection(pika.URLParameters(url))
        self.channel = self.connection.channel()
        self.channel.exchange_declare(exchange=exchange,
                                      exchange_type=exchange_type)
        self._exchange = exchange
        self._exchange_type = exchange_type
        self._routing_key = routing_key


    def publish(self, message):
        props = pika.BasicProperties(content_type='text/plain', delivery_mode=1)
        self.channel.basic_publish(self._exchange,
                                   self._routing_key,
                                   message,
                                   props)

    def consume(self, on_message, queue):
        self.channel.queue_declare(queue=queue, durable=True, exclusive=False,
                                   auto_delete=False)
        self.channel.queue_bind(queue=queue, exchange=self._exchange,
                           routing_key=self._routing_key)
        self.channel.basic_qos(prefetch_count=1)
        # Setup up our consumer callback
        self.channel.basic_consume(on_message, queue)
        # This is blocking until channel.stop_consuming is called and will allow us to receive messages
        self.channel.start_consuming()


class AsyncMQClient(object):
    """
    This is a configurable asynchronous rabbitmq client.
    Based on "Asynchronous publisher example" from pika docs:

    http://pika.readthedocs.org/en/latest/examples/asynchronous_publisher_example.html
    """

    def __init__(self, amqp_url, exchange='message', exchange_type='direct', 
                 queue='text', routing_key='mq.text',
                 app_id='example-publisher', content_type='application/json',
                 ioloop_instance=None, logger=None):
        """
        Setup the client object, passing in the URL we will use
        to connect to RabbitMQ, and other connection parameters.

        :param str amqp_url: The URL for connecting to RabbitMQ
        :param str exchange: The exchange to publish to
        :param str exchange_type: The rabbitmq exchange type
        :param str queue: The queue to publish to
        :param str routing_key: The routing key to publish
        :param str app_id: The app_id to register with rabbitmq server
        :param str content_type: The content-type that will be published
        :param logging.Logger logger: The logger to log to.
        """
        self._connection = None
        self._channel = None
        self._closing = False
        self._url = amqp_url
        self._exchange = exchange
        self._exchange_type = exchange_type
        self._queue = queue
        self._routing_key = routing_key
        self._app_id = app_id
        self._content_type = content_type
        if logger is not None:
            self._logger = logger
        else:
            self._logger = logging.getLogger(__name__)
        self._ioloop_instance = ioloop_instance

    def connect(self):
        """
        This method connects to RabbitMQ, returning the connection handle.
        When the connection is established, the on_connection_open method
        will be invoked by pika.

        :rtype: pika.SelectConnection
        """
        self._logger.info('Connecting to %s' % self._url)
        return adapters.TornadoConnection(pika.URLParameters(self._url),
                                          self.on_connection_open,
                                          custom_ioloop=self._ioloop_instance)

    def on_connection_open(self, unused_connection):
        """
        Called by pika once the connection to RabbitMQ has
        been established. It passes the handle to the connection object in
        case we need it, but in this case, we'll just mark it unused.

        :type unused_connection: pika.SelectConnection
        """
        self._logger.info('Connection opened')
        self.add_on_connection_close_callback()
        self.open_channel()

    def add_on_connection_close_callback(self):
        """
        Add an on close callback that will be invoked by pika
        when RabbitMQ closes the connection to the publisher unexpectedly.
        """
        self._logger.debug('Adding connection close callback')
        self._connection.add_on_close_callback(self.on_connection_closed)

    def on_connection_closed(self, connection, reply_code, reply_text):
        """
        Invoked by pika when the connection to RabbitMQ is
        closed unexpectedly.

        :param pika.connection.Connection connection: The closed connection obj
        :param int reply_code: The server provided reply_code if given
        :param str reply_text: The server provided reply_text if given
        """
        self._channel = None
        if self._closing:
            self._connection.ioloop.stop()
        else:
            self._logger.warning('Connection closed, reopening in 5 seconds: (%s) %s',
                           reply_code, reply_text)
            self._connection.add_timeout(5, self.reconnect)

    def reconnect(self):
        """
        Invoked by the IOLoop timer if the connection is
        closed. See the on_connection_closed method.
        """
        # This is the old connection IOLoop instance, stop its ioloop
        self._connection.ioloop.stop()

        if not self._closing:
            # Create a new connection
            self._connection = self.connect()
            # There is now a new connection, needs a new ioloop to run
            self._connection.ioloop.start()

    def open_channel(self):
        """
        Open a new channel with RabbitMQ by issuing the Channel.Open RPC
        command. When RabbitMQ responds that the channel is open, the
        on_channel_open callback will be invoked by pika.
        """
        self._logger.debug('Creating a new channel')
        self._connection.channel(on_open_callback=self.on_channel_open)

    def on_channel_open(self, channel):
        """
        Invoked by pika when the channel has been opened.
        The channel object is passed in so we can make use of it.

        Since the channel is now open, we'll declare the exchange to use.

        :param pika.channel.Channel channel: The channel object
        """
        self._logger.debug('Channel opened')
        self._channel = channel
        self.add_on_channel_close_callback()
        self.setup_exchange(self._exchange)

    def add_on_channel_close_callback(self):
        """
        Tell pika to call the on_channel_closed method if
        RabbitMQ unexpectedly closes the channel.
        """
        self._logger.info('Adding channel close callback')
        self._channel.add_on_close_callback(self.on_channel_closed)

    def on_channel_closed(self, channel, reply_code, reply_text):
        """
        Invoked by pika when RabbitMQ unexpectedly closes the channel.
        Channels are usually closed if you attempt to do something that
        violates the protocol, such as re-declare an exchange or queue with
        different parameters. In this case, we'll close the connection
        to shutdown the object.

        :param pika.channel.Channel: The closed channel
        :param int reply_code: The numeric reason the channel was closed
        :param str reply_text: The text reason the channel was closed
        """
        self._logger.warning('Channel was closed: (%s) %s', reply_code, reply_text)
        if not self._closing:
            self._connection.close()

    def setup_exchange(self, exchange_name):
        """
        Setup the exchange on RabbitMQ by invoking the Exchange.Declare RPC
        command. When it is complete, the on_exchange_declareok method will
        be invoked by pika.

        :param str|unicode exchange_name: The name of the exchange to declare
        """
        self._logger.debug('Declaring exchange %s' % exchange_name)
        self._channel.exchange_declare(self.on_exchange_declareok,
                                       exchange_name,
                                       self._exchange_type)

    def on_exchange_declareok(self, unused_frame):
        """
        Invoked by pika when RabbitMQ has finished the Exchange.Declare RPC
        command.

        :param pika.Frame.Method unused_frame: Exchange.DeclareOk response frame
        """
        self._logger.debug('Exchange declared')
        self.setup_queue(self._queue)

    def setup_queue(self, queue_name):
        """
        Setup the queue on RabbitMQ by invoking the Queue.Declare RPC
        command. When it is complete, the on_queue_declareok method will
        be invoked by pika.

        :param str|unicode queue_name: The name of the queue to declare.
        """
        self._logger.info('Declaring queue %s', queue_name)
        self._channel.queue_declare(self.on_queue_declareok, queue_name,
                                    durable=True, exclusive=False, 
                                    auto_delete=False)

    def on_queue_declareok(self, method_frame):
        """
        Invoked by pika when the Queue.Declare RPC call made in
        setup_queue has completed. In this method we will bind the queue
        and exchange together with the routing key by issuing the Queue.Bind
        RPC command. When this command is complete, the on_bindok method will
        be invoked by pika.

        :param pika.frame.Method method_frame: The Queue.DeclareOk frame
        """
        self._logger.debug('Binding %s to %s with %s',
                    self._exchange, self._queue, self._routing_key)
        self._channel.queue_bind(self.on_bindok, self._queue,
                                 self._exchange, self._routing_key)

    def close_channel(self):
        """
        Invoke this command to close the channel with RabbitMQ by sending
        the Channel.Close RPC command.
        """
        self._logger.info('Closing the channel')
        if self._channel:
            self._channel.close()

    def run(self):
        """
        Run the action by connecting to RabbitMQ and then
        starting the IOLoop.
        """
        self._connection = self.connect()
        self._connection.ioloop.start()

    def close_connection(self):
        """This method closes the connection to RabbitMQ."""
        self._logger.info('Closing connection')
        self._closing = True
        self._connection.close()


class AsyncMQPublisher(AsyncMQClient):
    """
    This is a configurable asynchronous rabbitmq publisher.
    Based on "Asynchronous publisher example" from pika docs:

    http://pika.readthedocs.org/en/latest/examples/asynchronous_publisher_example.html
    """

    def __init__(self, amqp_url, producer, exchange='message', exchange_type='topic', 
                 queue='text', routing_key='mq.text',
                 app_id='example-publisher', content_type='application/json',
                 logger=None):
        """
        Setup the publisher object, passing in the URL we will use
        to connect to RabbitMQ, and other connection parameters.

        :param str amqp_url: The URL for connecting to RabbitMQ
        :param function producer: The function producing messages to publish
        :param str exchange: The exchange to publish to
        :param str exchange_type: The rabbitmq exchange type
        :param str queue: The queue to publish to
        :param str routing_key: The routing key to publish
        :param str app_id: The app_id to register with rabbitmq server
        :param str content_type: The content-type that will be published
        :param logging.Logger logger: The logger to log to.
        """
        super(AsyncMQPublisher, self).__init__(amqp_url=amqp_url,
                                               exchange=exchange, 
                                               exchange_type=exchange_type, 
                                               queue=queue, 
                                               routing_key=routing_key,
                                               app_id=app_id, 
                                               content_type=content_type,
                                               logger=None)
        self.producer = producer

    def on_bindok(self, unused_frame):
        """
        This method is invoked by pika when it receives the Queue.BindOk
        response from RabbitMQ. Since we know we're now setup and bound, it's
        time to start consuming.
        """
        self._logger.info('Queue bound')

    def stop(self):
        """
        Stop the mq publisher by closing the channel and connection. We
        set a flag here so that we stop scheduling new messages to be
        published. The IOLoop is started because this method is
        invoked by the Try/Catch below when KeyboardInterrupt is caught.
        Starting the IOLoop again will allow the publisher to cleanly
        disconnect from RabbitMQ.
        """
        self._logger.info('Stopping')
        self._stopping = True
        self.close_channel()
        self.close_connection()
        self._connection.ioloop.stop()
        self._logger.info('Stopped')


class AsyncMQConsumer(AsyncMQClient):
    """
    This is a configurable asynchronous rabbitmq consumer.
    Based on "Asynchronous consumer example" from pika docs:

    http://pika.readthedocs.org/en/latest/examples/asynchronous_consumer_example.html
    """

    def __init__(self, amqp_url, on_message, exchange='message', exchange_type='topic', 
                 queue='text', routing_key='mq.text',
                 app_id='example-publisher', content_type='application/json',
                 logger=None):
        """
        Setup the publisher object, passing in the URL we will use
        to connect to RabbitMQ, and other connection parameters.

        :param str amqp_url: The URL for connecting to RabbitMQ
        :param function producer: The function producing messages to publish
        :param str exchange: The exchange to publish to
        :param str exchange_type: The rabbitmq exchange type
        :param str queue: The queue to publish to
        :param str routing_key: The routing key to publish
        :param str app_id: The app_id to register with rabbitmq server
        :param str content_type: The content-type that will be published
        :param logging.Logger logger: The logger to log to.
        """
        super(AsyncMQConsumer, self).__init__(amqp_url=amqp_url,
                                               exchange=exchange, 
                                               exchange_type=exchange_type, 
                                               queue=queue, 
                                               routing_key=routing_key,
                                               app_id=app_id, 
                                               content_type=content_type,
                                               logger=None)
        self._on_message = on_message

    def on_bindok(self, unused_frame):
        """
        This method is invoked by pika when it receives the Queue.BindOk
        response from RabbitMQ. Since we know we're now setup and bound, it's
        time to start consuming.
        """
        self._logger.info('Queue bound')
        self.start_consuming()

    def start_consuming(self):
        """
        This method sets up the consumer by first calling
        add_on_cancel_callback so that the object is notified if RabbitMQ
        cancels the consumer. It then issues the Basic.Consume RPC command
        which returns the consumer tag that is used to uniquely identify the
        consumer with RabbitMQ. We keep the value to use it when we want to
        cancel consuming. The on_message method is passed in as a callback pika
        will invoke when a message is fully received.
        """
        self._logger.info('Issuing consumer related RPC commands')
        self.add_on_cancel_callback()
        self._consumer_tag = self._channel.basic_consume(self._on_message,
                                                         self._queue)

    def add_on_cancel_callback(self):
        """
        Add a callback that will be invoked if RabbitMQ cancels the consumer
        for some reason. If RabbitMQ does cancel the consumer,
        on_consumer_cancelled will be invoked by pika.
        """
        self._logger.info('Adding consumer cancellation callback')
        self._channel.add_on_cancel_callback(self.on_consumer_cancelled)

    def on_consumer_cancelled(self, method_frame):
        """
        Invoked by pika when RabbitMQ sends a Basic.Cancel for a consumer
        receiving messages.

        :param pika.frame.Method method_frame: The Basic.Cancel frame
        """
        self._logger.info('Consumer was cancelled remotely, shutting down: %r',
                    method_frame)
        if self._channel:
            self._channel.close()

    def stop_consuming(self):
        """
        Tell RabbitMQ that you would like to stop consuming by sending the
        Basic.Cancel RPC command.
        """
        if self._channel:
            self._logger.info('Sending a Basic.Cancel RPC command to RabbitMQ')
            self._channel.basic_cancel(self.on_cancelok, self._consumer_tag)

    def on_cancelok(self, unused_frame):
        """
        This method is invoked by pika when RabbitMQ acknowledges the
        cancellation of a consumer. At this point we will close the channel.
        This will invoke the on_channel_closed method once the channel has been
        closed, which will in-turn close the connection.

        :param pika.frame.Method unused_frame: The Basic.CancelOk frame
        """
        self._logger.info('RabbitMQ acknowledged the cancellation of the consumer')
        self.close_channel()

    def stop(self):
        """
        Cleanly shutdown the connection to RabbitMQ by stopping the consumer
        with RabbitMQ. When RabbitMQ confirms the cancellation, on_cancelok
        will be invoked by pika, which will then closing the channel and
        connection. The IOLoop is started again because this method is invoked
        when CTRL-C is pressed raising a KeyboardInterrupt exception. This
        exception stops the IOLoop which needs to be running for pika to
        communicate with RabbitMQ. All of the commands issued prior to starting
        the IOLoop will be buffered but not processed.
        """
        self._logger.info('Stopping')
        self._closing = True
        self.stop_consuming()
        self._connection.ioloop.stop()
        self._logger.info('Stopped')

