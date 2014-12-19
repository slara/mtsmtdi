
from twisted.internet import epollreactor
epollreactor.install()
from twisted.application import internet, service
from twisted.internet import protocol
from zope.interface import Interface, implements
from twisted.python import components
from twisted.python import log
from twisted.internet.protocol import Protocol


class IncompleteNetstring(Exception):
    """
    Not enough data to complete a netstring.
    """


class BadNetstring(Exception):
    """
    Incorrect netstring format
    """


class OverLength(Exception):
    """
    netstring of incorrect length
    """


class IBarCodeService(Interface):
    pass


class BarCodeProtocol(Protocol):

    def dataReceived(self, data):
        log.msg("Barcode -> ", data)


# BarCode module
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
