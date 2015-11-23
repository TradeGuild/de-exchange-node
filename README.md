# Exchange Node

Each Exchange Node operates a single orderbook, representing a currency pair (i.e. BTC/USD). Unifying the nodes into a single user experience is done in the client, or using an [exchange broker](https://github.com/deginner/de-exchange-broker).

## Message Queue

This server subscribes and publishes events to an [AMQP](http://www.amqp.org/) message queue. Some of these events are published via the [SockJS-mq-server](https://bitbucket.org/deginner/sockjs-mq-server), while others are consumed by servers subscribed to broker events.
