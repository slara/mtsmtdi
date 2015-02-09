from twisted.application import service

import mtsbarcode

config = {
    'barcode_port': 8989,
}

ser = mtsbarcode.makeService(config)
application = service.Application('mtsbarcode')

ser.setServiceParent(service.IServiceCollection(application))
