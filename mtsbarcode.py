# -*- coding: utf-8 -*-
import os
import sys

from twisted.internet import epollreactor
epollreactor.install()
from twisted.application import internet, service
from twisted.internet import protocol, task
from zope.interface import Interface, implements
from twisted.python import components
from twisted.python import log
from twisted.internet.protocol import Protocol

sys.path.append(os.path.abspath(
    '/srv/servers/webservice/'
))
from j import *
setup_all()


def run_with_transaction(func):
    def decorated(*args, **kwargs):
        try:
            try:
                retval = func(*args, **kwargs)
                session.commit()
            except:
                session.rollback()
                raise
        finally:
            session.close()
        return retval
    return decorated


class IBarCodeService(Interface):
    pass


class BarCodeProtocol(Protocol):

    def dataReceived(self, data):
        dispatch = {'C': 'detention'}
        log.msg("Barcode -> ", data)
        msg = data.split()
        if len(msg) is 0:
            log.msg("Error: empty message")
            return
        command = msg[2]
        handler = getattr(self, 'handle_' + dispatch[command])
        handler(*msg[1:])

    @run_with_transaction
    def handle_detention(self, client, msgtype, dev, det, index):
        # set client
        client = Client.get_by(code=client)
        # get msg detention code
        print client.name, msgtype, dev, det, index


class IBarCodeFactory(Interface):
    pass


class BarCodeFactoryFromService(protocol.ServerFactory):

    implements(IBarCodeFactory)

    protocol = BarCodeProtocol

    def __init__(self, service):
        self.service = service


components.registerAdapter(BarCodeFactoryFromService,
                           IBarCodeService,
                           IBarCodeFactory)


class BarCodeService(service.Service):

    implements(IBarCodeService)

    def __init__(self):
        log.msg("Starting Service...")
        t = task.LoopingCall(self.echo)
        t.start(5)

    def echo(self):
        log.msg('Hola Mundo!')


def makeService(config):
    s = service.MultiService()
    f = BarCodeService()
    barcode = internet.TCPServer(int(config['barcode_port']),
                                 IBarCodeFactory(f))
    barcode.setServiceParent(s)
    return s
