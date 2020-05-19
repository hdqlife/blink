import os
import sys
import time
import _thread
try:
    import pyftpdlib
except:
    os.system('python3 -m pip install pyftpdlib')
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer
from pyftpdlib.authorizers import DummyAuthorizer
def ptdv():
    try:
        import ptvsd
    except:
        print(sys.argv)
        os.system('python3 -m pip install ptvsd')
    import ptvsd
    def run():
        if 'debug' in sys.argv:
            ptvsd.enable_attach(address=('0.0.0.0',5678))
            ptvsd.wait_for_attach()
        try:
            from app.bLink.client import client
            client.run()
            # import test
            # test.run()
        except Exception as e:
            print(e)
            import traceback
            traceback.print_exc()
    run()
def udpserver():
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(('0.0.0.0',8888))
    print('udpserver',8888)
    def r():
        while True:
            data,addr=s.recvfrom(2048)
            s.sendto(b'ok',addr)
            if data==b'restart':
                print('restin...')
                python=sys.executable
                os.execl(python,python,*sys.argv)
           
    _thread.start_new_thread(r,())
def sendrestart():
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('192.168.1.150',8888))
    s.send(b'restart')
    time.sleep(1)
    print('kill')
def debugserver():
    # Instantiate a dummy authorizer for managing 'virtual' users
    authorizer = DummyAuthorizer()

    # Define a new user having full r/w permissions and a read-only
    # anonymous user  perm='elradfmwMT'
    ftpUser=('root', 'Xykj20160315', os.getcwd())
    authorizer.add_user(*ftpUser,perm='elradfmwMT')
    print('ftpuser',ftpUser)
    authorizer.add_anonymous(os.getcwd())

    # Instantiate FTP handler class
    handler = FTPHandler
    handler.authorizer = authorizer

    # Define a customized banner (string returned when client connects)
    handler.banner = "pyftpdlib based ftpd ready."

    # Specify a masquerade address and the range of ports to use for
    # passive connections.  Decomment in case you're behind a NAT.
    #handler.masquerade_address = '151.25.42.11'
    #handler.passive_ports = range(60000, 65535)

    # Instantiate FTP server class and listen on 0.0.0.0:2121
    address = ('0.0.0.0', 53333)
    server = FTPServer(address, handler)
    print('ftpAddress',address)

    # set a limit for connections
    server.max_cons = 256
    server.max_cons_per_ip = 5

    # start ftp server
    import _thread
    if 'ftpserver' in sys.argv:
        _thread.start_new_thread(server.serve_forever,())
    if 'debug' in sys.argv:
        _thread.start_new_thread(udpserver,())
    ptdv()

def main():
    print('oscwd',os.getcwd(),os.path)
    print('sys.argv',sys.argv)
    if 'kill' in sys.argv:
        sendrestart()
    else:
        debugserver()
if __name__ == "__main__":
    main()
