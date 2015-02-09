# -*- coding: utf-8 -*-
import os
import sys
from datetime import timedelta as td
from datetime import datetime as dt

from twisted.internet import epollreactor
epollreactor.install()
from twisted.application import internet, service
from twisted.internet import protocol, task
from zope.interface import Interface, implements
from twisted.python import components
from twisted.python import log
from twisted.internet.protocol import Protocol
from sqlalchemy import desc

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
        dispatch = {'mt_di': 'detention'}
        log.msg("MTDI <- ", data)
        msg = data.split(',')
        if len(msg) is 0:
            log.msg("Error: empty message")
            return
        command = msg[0]
        handler = getattr(self, 'handle_' + dispatch[command])
        print msg
        handler(*msg[1:])
        self.transport.loseConnection()

    @run_with_transaction
    def handle_detention(self, client, msgtype, dev=0, det=0, index=0):
        def sendack():
            ack = 'MTDI_ED 0000'
            log.msg('MTDI ->', ack)
            self.transport.write(ack)
        if msgtype == '0':
            sendack()
            return
        clients = {'SIN': 3}
        codes = {
            '001': 4001,
            '002': 4002,
            '003': 4003
        }
        device = Device.get(int(13))

        detq = Cod_state.query.filter_by(client_id=clients[client])
        client = Client.get(clients[client])
        code = detq.filter_by(code=codes[det]).one()
        noasign = Cod_state.query.filter_by(client=client).filter(
            Cod_state.description.like('No asig%')).one()

        detention = S_reg.query.filter_by(dev=device).first()

        if detention.cod_state is noasign:
            log.msg('DETENTION:', detention.date_s, client.name, dev, code.description)
            detention.cod_state = code
            detention.user = User.get(device.last_ope_id)
        else:
            if not detention.date_f and (detention.cod_state != code):
                log.msg('DETENTION:', 'DIV')
                BS_reg(state=detention.state,
                       code=code.id,
                       user=device.last_ope_id,
                       date_i=dt.now(),
                       date_s=dt.now(),
                       dev=device.id,
                       wr=0)
        print client.name, msgtype, dev, det, index
        sendack()


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


def makeService(config):
    s = service.MultiService()
    f = BarCodeService()
    barcode = internet.TCPServer(int(config['barcode_port']),
                                 IBarCodeFactory(f))
    barcode.setServiceParent(s)
    return s
