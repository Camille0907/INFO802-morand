from math import ceil
from flask import Flask
from spyne import Application, rpc, ServiceBase, Float
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication

app = Flask(__name__)


class DeliveryCostService(ServiceBase):
    @rpc(Float, Float, _returns=Float)
    def deliveryCost(ctx, distance, weight):
        cost = weight * distance / 100.0  # 1 euro/kg for 100 km
        return ceil(cost * 100) / 100  # rounded 2 digits after comma


application = Application([DeliveryCostService], tns='DeliveryCost', in_protocol=Soap11(validator='lxml'),
                          out_protocol=Soap11())
app.wsgi_app = WsgiApplication(application)
