from twisted.application import service

import mtsmtdi

config = {
    'mtdi_port': 8989,
}

ser = mtdi.makeService(config)
application = service.Application('mtsmtdi')

ser.setServiceParent(service.IServiceCollection(application))
