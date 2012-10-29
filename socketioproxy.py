from os import path as op
import logging
import socket

from tornado import web, iostream
from tornadio2 import TornadioRouter, SocketServer, SocketConnection

destinations = {
    '/set': ('localhost', 1337),
}

ROOT = op.normpath(op.dirname(__file__))

logger = logging.getLogger('sioproxy')


class EndpointConnection(SocketConnection):
    """Proxies the web client connection through to another server
    and passes data back and forth.

    All clients will use this class, but the endpoint string specified by the
    client will map through to the right server.
    """

    def __init__(self, *args, **kwargs):
        self.endpoint_stream = None
        self.client_closed = False
        super(EndpointConnection, self).__init__(*args, **kwargs)

    #
    # Something happens on the client (socket.io) side.
    #

    def on_open(self, request):
        """New client connection opened"""

        # Find the right endpoint and create th connection
        dest = destinations[self.endpoint]

        name = self.session.handler.name if self.session.handler else '??'
        logger.info('New %s client for endpoint %s on port %s' %
                    (name, self.endpoint, dest[1]))

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        self.endpoint_stream = iostream.IOStream(s)
        self.endpoint_stream.connect(dest, self.on_endpoint_connected)

    def on_message(self, message):
        """Client socket received data"""

        logger.debug('Data from client (%s)' % message)

        # A message string from the client.
        # Encode it and send it to the endpoint server as bytes.
        self.endpoint_stream.write(message.encode('utf-8'))

    def on_close(self):
        """Client connection closed"""
        logger.info('Client left')

        self.client_closed = True

        # Close connection to endpoint
        self.endpoint_stream.close()

    #
    # Something happens on the server (endpoint) side.
    #

    def on_endpoint_connected(self):
        """Connected to endpoint - set up callbacks"""

        self.endpoint_stream.read_until_close(self.on_endpoint_final, self.on_endpoint_data)
        self.endpoint_stream.set_close_callback(self.on_endpoint_closed)

        logger.info('Connection succeeded')

    def on_endpoint_closed(self):
        """Endpoint has closed"""
        if self.client_closed:
            logger.info('Server connection closed (triggered by client)')
        else:
            logger.info('Server connection closed')
            self.close()

    def on_endpoint_final(self, data):
        """Final callback from endpoint - connection is about to close"""
        logger.debug('Final data from endpoint')

    def on_endpoint_data(self, data):
        """Data streamed in fron endpoint: push straight to the client"""
        logger.debug('Data from endpoint (%s)' % data)

        self.send(data)


class ProxyConnection(SocketConnection):
    """Front router - maps all valid endpoint names to the endpoint connection"""

    __endpoints__ = {name: EndpointConnection for name in destinations}


ProxyRouter = TornadioRouter(ProxyConnection, {"verify_remote_ip": False, })

app = web.Application(
    ProxyRouter.urls,
    socket_io_port=8080,
    flash_policy_port=10843,
    flash_policy_file=op.join(ROOT, 'flashpolicy.xml'),
)

if __name__ == '__main__':

    import logging
    logging.basicConfig()
    logging.getLogger('sioproxy').setLevel(logging.DEBUG)

    SocketServer(app)
