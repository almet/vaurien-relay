Vaurien RPC relay
##################

Expose a way to control multiple vaurien proxies with a single 0mq interface.

Here is how, programatically, yoyu can use this "relay"::

    from vaurienrelay import RPCRelay

    relay = RPCRelay('tcp://socket', instances={
        'db1': 'host:port',
        'memcache2': 'host:port',
    })
    relay.start()

Then, on the client side, you can call the methods you want, as follows::

    from zerorpc import Client

    c = Client('tcp://socket')
    c.set_hander('db1', 'blackout')

And that's it!
