import sys
import time
from unittest import TestCase

from subprocess import Popen
from vaurienrelay import RPCRelay


class RelayTest(TestCase):

    def setUp(self):
        # setup some vaurien proxies
        self.instances = {}
        self.processes = []

        for i in (1, 2):
            port = 8009 + i
            host = 'http://localhost:%d' % port
            self.instances['proxy%s' % i] = host

            # Spawn the WSGI process
            cmd = '%s -m vaurien.tests.support %s' % (sys.executable, port)
            process = Popen(cmd.split(' '))
            self.processes.append(process)

        # start a relay instance
        self.relay = RPCRelay(None, self.instances)

        # wait for the servers to start
        time.sleep(0.5)

    def tearDown(self):
        for process in self.processes:
            process.terminate()

    def test_wrong_routing(self):
        # proxy3 doesn't exist, so this should fail
        self.assertRaises(KeyError, self.relay.set_handler,
                          'proxy3', 'blackout')

    def test_right_routing(self):
        # changing things on one proxy shouldn't impact the other ones
        self.relay.set_handler('proxy1', 'blackout')
        self.assertEquals('blackout', self.relay.get_handler('proxy1'))
        self.assertEquals('default', self.relay.get_handler('proxy2'))

    def test_lock_works(self):
        # until we release the lock explicitely, it's not possible to
        # change the same handler two times.
        self.relay.set_handler('proxy1', 'blackout')
        self.assertRaises(ValueError, self.relay.set_handler,
                          'proxy1', 'normal')
        self.assertEquals('blackout', self.relay.get_handler('proxy1'))

    def test_lock_release(self):
        # if we explicitely release the lock, everything should be back to
        # normal
        self.relay.set_handler('proxy1', 'blackout')
        self.relay.set_handler('proxy1', 'normal', release_lock=True)
        self.assertEquals('normal', self.relay.get_handler('proxy1'))
