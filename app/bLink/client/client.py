from .common.http import initHttp
from common.server import MqttClient
from common import function
from .common.mqttpro import read
import os
from .common.device import Base,Device
from .common import msg
from .common import proto
import _thread
import time
def initwifi():
    os.system('wpa_supplicant -D wext -c /etc/wpa_supplicant.conf -i wlan0 &')
    os.system('udhcpc -i wlan0')
def init4g():
    # insmod /work/dev_power.ko
    # 
    pass
def updread(data):
    print('myudpread',data)
    if data==b'SSSSSSSSGGGGGGGGHHHHHHHHYYYYYYYY':
        return os.popen('ifconfig').read().encode('utf-8')
    else:
        return b'error'
def loop():
    num=0
    while True:
        if num%500==0:
            os.system('ntpdate %s'%msg.FG['ntpserver'])
        num+=1
        time.sleep(1)
def run():
    from bacpypes.core import run
    def bacrun():
        run()
    _thread.start_new_thread(bacrun,())
    _thread.start_new_thread(loop,())
    function.udpsendmsg(9988,updread)
    
    _thread.start_new_thread(initHttp,())
    Base.io=MqttClient(
        #msg.FG['ClientID'],msg.FG['netip'],int(msg.FG['netport']), 121.36.21.219 171.221.238.16
        "","121.36.21.219",1883,
        msg.FG['netusername'],msg.FG['netpassword'],
        keepalive=int(msg.FG['hearttime']),
        topicRecvTail='_reply',topicFont='',
        myPreRead=read,userdata=dict(code="200",msg=""),
        #bind_address=""
    )
    Device(msg.FG['deviceid'],None,protocol=5,interface="Terminal",enable=True)
    proto.MRtu('/dev/ttyO1' if os.name!='nt' else 'COM1',9600).start()
    Base.io.myloop()

if __name__=="__main__":
    run()

