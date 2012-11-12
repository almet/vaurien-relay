from urlparse import urlparse
import functools

from vaurien.client import Client as VaurienClient
import zerorpc


class RPCRelay(object):

    # these are the methods generated on the fly
    methods = ('get_handler', 'list_handler')

    def __init__(self, zmq_socket, vaurien_instances):
        """Proxy the calls made here to vaurien clients.

        :param zmq_socket:
            The socket to bind to

        :param vaurien_instances:
            A mapping with the name of the vaurien proxy as a key and its
            address as value

        You can use this relay as follow::

            from vaurienrelay import RPCRelay

            relay = RPCRelay('tcp://socket', instances={
                'db1': 'host:port',
                'memcache2': 'host:port',
            })
            relay.start()

        And then on the client side, you can call the methods listed in :param
        methods:
        """

        self._zmq_socket = zmq_socket
        self._vaurien_instances = vaurien_instances
        self._clients = {}
        self._in_use = []

        for method in self.methods:
            # dynamically create the list of methods.
            setattr(self, method,
                    functools.partial(self.relay_method, self, method))

    def _get_client(self, name):
        """Return a vaurien client, or raise a ValueError if "name"
        doesn't exists.
        """
        if not name in self._clients:
            parts = urlparse(self._vaurien_instances[name])
            host, port = parts.netloc.split(':', -1)
            self._clients[name] = VaurienClient(host, port)
        return self._clients[name]

    def set_handler(self, instance, handler, release_lock=False):
        """Set the handler on the given client.

        An instance can only be set once at a time. A lock is present to avoid
        asking a client to do different things at the same time.

        :param instance:
            The name of the instance to send the command to.

        :param handler:
            The name of the handler to change.

        :param release_lock:
            Explicitely release the lock (default False). This needs to be
            called otherwise it will not be possible to change the handler for
            this instance.
        """
        resp = None

        if instance not in self._in_use or release_lock:
            resp = self._get_client(instance).set_handler(handler)

        if instance in self._in_use and release_lock:
            self._in_use.pop(instance)

        if resp:
            return resp
        else:
            ValueError('There is a lock on this client')

    def relay_method(self, method, instance, *args, **kwargs):
        """Relay the :param method: method to the right vaurien proxy,
        found using :param instance:.
        """
        client_method = getattr(self._get_client(instance), method)
        return client_method(*args, **kwargs)

    def start(self):
        """Start the ZeroRPC interface"""
        s = zerorpc.Server(self)
        s.bind(self._zmq_socket)
        s.run()
