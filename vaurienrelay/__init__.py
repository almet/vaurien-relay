from urlparse import urlparse
import time

from vaurien.client import Client as VaurienClient
import zerorpc


class RPCRelay(object):

    # these are the methods generated on the fly
    methods = ('get_handler', 'list_handlers')

    def __init__(self, zmq_socket, nodes, timeout=60 * 60):
        """Proxy the calls made here to vaurien clients.

        :param zmq_socket:
            The socket to bind to

        :param nodes:
            A mapping with the name of the vaurien proxy as a key and its
            address as value

        :param timeout:
            The time (in seconds) before the lock is released. Defaults to one
            hour.

        You can use this relay as follow::

            from vaurienrelay import RPCRelay

            relay = RPCRelay('tcp://socket', nodes={
                'db1': 'host:port',
                'memcache2': 'host:port',
            })
            relay.start()

        And then on the client side, you can call the methods listed in :param
        methods:
        """

        self._zmq_socket = zmq_socket
        self._nodes = nodes
        self._clients = {}
        self._locks = {}
        self._timeout = timeout

    def _get_client(self, name):
        """Return a vaurien client, or raise a ValueError if "name"
        doesn't exists.
        """
        if not name in self._clients:
            parts = urlparse(self._nodes[name])
            host, port = parts.netloc.split(':', -1)
            self._clients[name] = VaurienClient(host, port)
        return self._clients[name]

    def set_handler(self, proxy, handler, release_lock=False, timeout=None):
        """Set the handler on the given client.

        As a proxy can only handle one handler at a time, a lock is present to
        avoid a client to ask the proxy to do that. You can control this lock
        by using the :param release_lock: argument (default False).

        :param proxy:
            The name of the vaurien proxy to send the command to.

        :param handler:
            The name of the handler to change.

        :param release_lock:
            Explicitely release the lock (default False). This needs to be
            called when you stop using the proxy.

        :param timeout:
            Optional parameter; the timeout value for this lock (if any). If
            not set, the value passed to the constructor will be used.
        """
        if proxy in self._locks:
            if release_lock or time.time() >= self._locks[proxy]:
                self._locks.pop(proxy)

        if proxy in self._locks:
            raise ValueError('There is a lock on this client')

        # Do the request.
        res = self._get_client(proxy).set_handler(handler)

        if not release_lock:
            self._locks[proxy] = time.time() + (timeout or self._timeout)

        return res

    def get_handler(self, proxy):
        return self._get_client(proxy).get_handler()

    def get_handlers(self, proxy):
        return self._get_client(proxy).get_handlers()

    def start(self):
        """Start the ZeroRPC interface"""
        s = zerorpc.Server(self)
        s.bind(self._zmq_socket)
        s.run()
