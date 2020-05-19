import uuid
import sys
import os
from common import function
DEBUG='debug' in sys.argv
COM_NAMES=['/dev/ttyO1','/dev/ttyO5','/dev/ttyO4','/dev/ttyO3','/dev/ttyO2']
import json
import time
VER='1_1_1'
CODE_FILES=[
    'app/bLink/client/common/__init__.py',
    'app/bLink/client/common/bac.py',
    'app/bLink/client/common/device.py',
    'app/bLink/client/common/http.py',
    'app/bLink/client/common/mqttpro.py',
    'app/bLink/client/common/msg.py',
    'app/bLink/client/common/proto.py',
    'app/bLink/client/html/index.html',
    'app/bLink/client/client.py',
    'shell/run.sh',
    'test/url.config',
]
DEFAULT_PARAM=dict(
    TP_CONFIG = '/config/push',
    TP_MANAGE = '/devices/push',
    TP_TASK = '/tasks/push',
    TP_EVENT = '/alarms/push',
    TP_PARAM_POST = '/property/post_reply',

    TYPE_ADD = 'add',#设备的添加
    TYPE_DELETE = 'delete',#设备的删除
    TYPE_UPDATE = 'update',#设备参数的更新
    TYPE_QUERY = 'query',#设备属性的查询
    TYPE_SEARCH = 'search',#设备的搜索 无data
    TYPE_UPLOAD = 'upload',

    account="admin",
    password="admin",

    netip='171.221.238.16',
    netport='9092',
    netusername='1235401760240529409&1235411979762819073',
    netpassword='b1aedd9b8e4218d2b34f1d0e5d54f7a7',
    ClientID="1235411979762819073&1&hmacmd5",
    productid='1235401760240529409',
    deviceid="",
    hearttime='60',

    localcom="eth0",
    localip="192.168.1.131",
    netmask="255.255.254.0",
    gateway="192.168.1.1",
    dns="8.8.8.8",
    ntpserver="ntp1.aliyun.com",
    mac="",
    wifiName="wifi",
    wifiPassword="123456"

)
#os.system('rm config.json')
FG=function.FileConfig('config.json',DEFAULT_PARAM)
#FG["deviceid"]=str(uuid.uuid1()).split('-').pop()
FG["deviceid"]="aca213cfac04"
FG["localcom"]="eth0"
NETWORK_NAME=['eth0','eth1','wlan0','lo']
WIFISET='''
ctrl_interface=/var/run/wpa_supplicant
ap_scan=1
network={
 ssid="%s"
 psk="%s"
}
'''
SET_NETIP='''
# /etc/network/interfaces -- configuration file for ifup(8), ifdown(8)

# The loopback interface
auto lo
iface lo inet loopback

# Wireless interfaces
iface wlan0 inet dhcp
        wireless_mode managed
        wireless_essid any
        wpa-driver wext
        wpa-conf /etc/wpa_supplicant.conf

iface tiwlan0 inet dhcp
        wireless_mode managed
        wireless_essid any

iface atml0 inet dhcp

# Wired or wireless interfaces
auto eth0
#iface eth0 inet dhcp
        #pre-up /bin/grep -v -e "ip=[0-9]\+\.[0-9]\+\.[0-9]\+\.[0-9]\+" /proc/cmdline > /dev/null
        iface eth0 inet static
        address %s
        netmask %s

iface eth1 inet dhcp

# Ethernet/RNDIS gadget (g_ether)
# ... or on host side, usbnet and random hwaddr
iface usb0 inet dhcp

# Bluetooth networking
iface bnep0 inet dhcp

'''
TPOICS=[FG['TP_CONFIG'],FG['TP_MANAGE'],FG['TP_TASK'],FG['TP_EVENT'],FG['TP_PARAM_POST']]
REG_MAP={
    'AI0':dict(path='/dev/ad7795',index=1,openMode="b+",regaddr=0),
    'AI1':dict(path='/dev/ad7795',index=1,openMode="b+",regaddr=1),
    'AI2':dict(path='/dev/ad7795',index=1,openMode="b+",regaddr=2),
    'AI3':dict(path='/dev/ad7795',index=1,openMode="b+",regaddr=3),
    'AI4':dict(path='/dev/ad7795',index=1,openMode="b+",regaddr=4),
    'AI5':dict(path='/dev/ad7795',index=1,openMode="b+",regaddr=5), #AI0-AI5:0->5

    'DI0':dict(path='/dev/iocontrol',index=0,openMode="rb",regaddr=6),
    'DI1':dict(path='/dev/iocontrol',index=1,openMode="rb",regaddr=7),
    'DI2':dict(path='/dev/iocontrol',index=2,openMode="rb",regaddr=8),
    'DI3':dict(path='/dev/iocontrol',index=3,openMode="rb",regaddr=9),
    'DI4':dict(path='/dev/iocontrol',index=4,openMode="rb",regaddr=10),
    'DI5':dict(path='/dev/iocontrol',index=5,openMode="rb",regaddr=11),
    'DI6':dict(path='/dev/iocontrol',index=6,openMode="rb",regaddr=12),
    'DI7':dict(path='/dev/iocontrol',index=7,openMode="rb",regaddr=13),#DI0->DI7:6->13
    
    
    'AO0':dict(path='/dev/mcp47254',index=2,openMode="wb",regaddr=14),
    'AO1':dict(path='/dev/mcp47253',index=2,openMode="wb",regaddr=15),
    'AO2':dict(path='/dev/mcp47252',index=2,openMode="wb",regaddr=16),
    'AO3':dict(path='/dev/mcp47251',index=2,openMode="wb",regaddr=17),
    'AO4':dict(path='/dev/ad5422',index=1,openMode="wb",regaddr=18),#AO0->AO4:14->18

    'DO0':dict(path="/dev/outcontrol",index=0,openMode="wb",regaddr=19),
    'DO1':dict(path="/dev/outcontrol",index=1,openMode="wb",regaddr=20),#DO0->DO1:19->20

}
for i in range(0,15):
    REG_MAP["VI"+str(i)]=dict(path='/virture/value',index=i,openMode="b+",regaddr=21+i) #VI0->VI15:21->35
for i in range(0,36):
    REG_MAP['L%s'%i]=dict(path='/dev/dev_74hc595',index=i+1,openMode='wb',regaddr=36+i) #L1->L36:36->71（灯）
DEFAULT_INTERFACE={}
for i in range(1,len(COM_NAMES)):
    ids='SerialA'+str(i)
    tmp={
        "ip": COM_NAMES[i],
        "port": 115200,
        "parity": "None",
        "class":"Serial",
        "stopbit":1,
        "databit":8,
        "interval":1,
        "enable":False,
    }
    DEFAULT_INTERFACE[ids]=tmp
for i in range(1,5):
    ids="can"+str(i)
    tmp=dict(bitrate=125000,id=ids)
    tmp['class']="can"
    tmp['interval']=1
    tmp["enable"]=False
    DEFAULT_INTERFACE[ids]=tmp
for eth in NETWORK_NAME:
    ids='net_'+eth
    DEFAULT_INTERFACE[ids]=function.networkInfo(eth)
    DEFAULT_INTERFACE[ids]['interval']=1
    DEFAULT_INTERFACE[ids]['class']='net'
    DEFAULT_INTERFACE[ids]['enable']=True
    DEFAULT_INTERFACE[ids]['ip']=DEFAULT_INTERFACE[ids].get('addr','0.0.0.0')

DEFAULT_INTERFACE['Terminal']={"enable":True,"interval":1}

CODE_RIGHT=200
CODE_DEVICE_BUSY=201
CODE_DATA_PARSE_ERROR=202
CODE_ERROR=203
CODE_ERROR_TYPE=204
CODE_ERROR_CLASS=205