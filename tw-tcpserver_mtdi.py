# Nueva implementacion TCP Server

from twisted.application import internet, service
#from twisted.python.log import ILogObserver, FileLogObserver
#from twisted.python.logfile import DailyLogFile

from twisted.internet import reactor,protocol
from twisted.protocols import basic
from random import randint

from sqlalchemy import *
import datetime
import site
import os
#site.addsitedir(os.path.abspath('../webservice'))
#from j import *
#setup_all()

def run_with_transaction(func):
    def decorated(*args, **kwargs):
        try:
            try:
                retval = func(*args, **kwargs)
                session.commit()
            except Exception, e:
                session.rollback()
                raise
        finally:
            session.close()
        return retval
    return decorated

class PLC_Receiver(protocol.Protocol):
    def dataReceived(self, request):
        #salida = data + str(randint(0,11))
        #self.transport.write(salida)
        try:
            self.process_request(request)
        except Exception, e:
            error =  ('exception: %s' % str(e))
            print error
            self.transport.write('Error: %s\n' % str(e))
        self.transport.loseConnection()

    def process_request(self, request):
        """Process a request.

        This method is called by self.handle() for each request it
        reads from the input stream.

        This implementation simply breaks the request string into
        words, and searches for a method named 'do_COMMAND',
        where COMMAND is the first word.  If found, that method is
        invoked and remaining words are passed as arguments.
        Otherwise, an error is returned to the client.
        """

        words = request.split()
        if len(words) == 0:
            self.transport.write('Error: empty request\n')
            return

        command = words[0]
        args = words[1:]

        methodname = 'do_' + command
        if not hasattr(self, methodname):
            self.transport.write('Error: "%s" is not a valid command\n' % command)
            return
        method = getattr(self, methodname)
        method(*args)

    def do_echo(self, *args):
        """Process an 'echo' command"""
        self.transport.write(' '.join(args) + '\n')


    @run_with_transaction
    def do_update(self, *args):

        message = 'UPDATED 0000'#+ str(kh[dev_int][1])#+str(self.request.getpeername()[1])
        self.transport.write(message)

    @run_with_transaction
    def do_stamp(self, *args):
        """Process an 'stamp' command

        #     Database fill
        La data es de la forma:
            stamp tttttttttt dddd s nnnn ss p
            donde:
                tttttttttt      corresponde al time stamped con 10 digitos
                dddd            corresponde al dev_id con 4 digitos
                s               corresponde al estado del dev con un digito
                nnnn		corresponde al send_id, nuemro con 4 digitos correlativo de envios
#JJ IMPERIAL                ss		corresponde al espesor de la madera
                p               corresponde a un digito final de mensaje
        """


        # Sends STAMPED($PID)
        message = 'STAMPED 0000' #+str(self.request.getpeername()[1])
        self.transport.write(message)

class ReceiverFactory(protocol.ServerFactory):
    protocol = PLC_Receiver

application = service.Application('plcserver')
#logfile = DailyLogFile("tcp.log", ".")
#application.setComponent(ILogObserver, FileLogObserver(logfile).emit)

plcService = internet.TCPServer(8989, ReceiverFactory())
plcService.setServiceParent(application)
