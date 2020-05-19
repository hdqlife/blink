import json
import socket
import time
from queue import Queue
from threading import Thread

from paho.mqtt.client import Client
from serial import Serial

import _thread
from common.function import crc16, md5


class SerialClient(Thread):
    def __init__(self,com,burd,read=None):
        self.comName=com
        self.burd=burd
        self.com=None
        self.read=read
        Thread.__init__(self,daemon=True)
        #self.start()
    def connectAuto(self,data):
        if self.com is None:
            self.open()
        if self.com and data:
            if isinstance(data,list):
                data=bytearray(data)
            self.com.write(data)
    def write(self,data):
        self.connectAuto(data)
    def open(self):
        try:
            self.com=Serial(port=self.comName,baudrate=self.burd,timeout=0.1)
            print('open success',self.comName)
        except Exception as e:
            print(e)
            self.com=None
    def run(self):
        while True:
            try:
                if self.com is None:
                    self.open()
                    time.sleep(2)
                else:
                    data=self.com.read(2048)
                    if self.read and data:
                        #print('comRead',[(int(d)) for d in data])
                        rt=self.read(data)
                        if rt:
                            #print('comWrite',[(int(d)) for d in rt])
                            self.write(rt)
            except Exception as e:
                print('comError',e,self.comName)
                import traceback
                traceback.print_exc()
                self.com=None
    def update(self,burd,port):
        self.comName=port
        self.burd=burd
        if self.com:
            self.com.close()
        self.com=None
    def isEnable(self):
        return self.com is not None
class MoutbusClient():
    def __init__(self,param):
        if isinstance(param["port"],str):
            self.device=SerialClient(param["port"],param["ip"],read=self.moutbusRead)
        else:
            self.device=TcpClient(param["ip"],param["port"],read=self.moutbusRead)
        self.watch=param.get("watch",[])
        self.addr=int(param.get("addr",1))
        self.data=-1
    def moutbusRead(self,data):
        all_num=len(data)
        for i in range(all_num-2):
            if data[i]==self.addr:
                if data[i+1]==0x05 or data[i+1]==0x06:
                    crc_begin=i+6
                    data_begin=i+4
                else:
                    crc_begin=data[i+2]+i+3
                    data_begin=i+3
                if crc_begin+1<all_num:
                    crc_value1,crc_value2=data[crc_begin],data[crc_begin+1]
                    crc_value=crc16(data[i:crc_begin])
                    if crc_value[0]==crc_value1 and crc_value[1]==crc_value2:
                        value=0
                        for j in range(data_begin,crc_begin):
                            value=value*256+data[j]
                        self.data=value
                    else:
                        print('crcCheckError',data[i:crc_begin+2])

    def write(self,command,index,value,addr=None):
        if addr:
            self.addr=addr
        data=[self.addr,command,(index>>8)&0xff,index&0xff,(value>>8)&0xff,value&0xff]
        crc_value = crc16(data)
        data.append(crc_value[0])
        data.append(crc_value[1])
        self.device.write(data)
    def read(self,command,index,value,addr):
        self.write(command,index,value,addr)
        self.data=-1
        num=0
        while self.data==-1 and num<10:
            time.sleep(0.1)
            num+=1
        return self.data

class TcpClient(Thread):
    def __init__(self, ip,port,time_out=None, read=None, connect_success=None, block=True):
        self.ip, self.port = ip,port
        self.timeout = time_out
        self.sock = None
        self.src_address = ('127.0.0.1', 0)
        self.connect_success = connect_success
        self.alive = True
        self.read = read
        self.block = block
        self.url = ''
        Thread.__init__(self,daemon=True)
        #self.start()
    def p_read(self, data):
        if self.read:
            return self.read(data)
        return None
    def connectAuto(self, data=None, sleep_error_time=None):
        if self.sock is None:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(self.timeout)
                sock.connect((self.ip, self.port))
                sock.setblocking(self.block)
                self.sock = sock
                self.src_address = self.sock.getsockname()
                print('tcp connecting success', self.ip, self.port)
                return True
            except Exception as e:
                if sleep_error_time:
                    time.sleep(sleep_error_time)
                return False
        if data and self.sock:
            if isinstance(data,list):
                data=bytearray(data)
            self.sock.send(data)
        return True

    def run(self):
        while self.alive:
            if self.connectAuto(sleep_error_time=5):
                try:
                    data = self.sock.recv(1024 * 1024)
                    if len(data) == 0:
                        self.sock.close()
                        self.sock = None
                    else:
                        rt = self.p_read(data)
                        if rt:
                            self.write(rt)
                except socket.timeout as e:
                    pass
                except IOError as e:
                    print(self.get_info(), 'read err', e)
                    self.sock.close()
                    self.sock = None
        print('exit tcp')

    def write(self, data):
        rt = 0
        if not data:
            return rt
        if isinstance(data, dict):
            data = json.dumps(data)
        if isinstance(data, str):
            data = data.encode('utf_8')
        return self.connectAuto(data)

    def stop(self):
        self.alive = False
        if self.sock:
            self.sock.close()
        self.timeout = -1

    def get_info(self):
        return ['tcp_client', self.ip, self.port, self.src_address[0], self.src_address[1]]

    def isEnable(self):
        return self.sock is not None
    def update(self,ip,port):
        self.ip=ip
        self.port=port
        if self.sock:
            self.sock.close()
        self.sock=None

class UdpServer(Thread):
    def __init__(self, ip, port,read,type='server'):
        self.ip=ip
        self.port=port
        self.sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.read=read
        self.type=type
        Thread.__init__(self,daemon=True)
    def run(self):
        try:
            if self.type=='server':
                self.sock.bind((self.ip,self.port))
                print('listen udp',self.sock.getsockname())
            else:
                self.sock.connect((self.ip,self.port))
                self.sock.send(b'hellow')
        except:
            pass
            return
        while True:
            data,addr=self.sock.recvfrom(8192)
            self.read(self,addr,data)

    def write(self,addr,msg):
        if isinstance(msg,str):
            msg=msg.encode('utf-8')
        self.sock.sendto(msg,addr)
    def write_all(self,msg):
        if isinstance(msg,str):
            msg=msg.encode('utf-8')
        self.sock.sendall(msg)

class TcpServer(Thread):
    def __init__(self,ip,port,time_out=2):
        self.ip=ip
        self.port=port
        self.sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.time_out=time_out
        Thread.__init__(self,daemon=True)
        #self.start()
    def run(self):
        self.sock.bind((self.ip,self.port))
        self.sock.listen(100)
        while True:
            try:
                sock,addr=self.sock.accept()
                sock.settimeout(self.time_out)
                _thread.start_new_thread(self.new,(sock,))
            except Exception as e:
                print('sock',e)
    def new(self,sock):
        while True:
            data=sock.recv(1024)
            if len(data):
                rt=self.read(data)
                if rt:
                    sock.send(rt)
    def read(self,data):
        pass

class MqttClient(Client):
    def __init__(self,clientId,ip,port,username,password,qos=2,keepalive=50,userdata=None,myPreRead=None,topicRecvTail='',topics=None,topicFont=''):
        print('connect_param')
        self.qos=qos
        ps=dict(clientId=clientId,username=username,password=password,ip=ip,port=port)
        for key in ps:
            print(key,':',ps[key])
        Client.__init__(self,clientId)
        self.topics=topics or {}
        self.topicRecvTail=topicRecvTail
        self.topicFont=topicFont
        self.ip=ip
        self.port=port
        self.connectSuccee=False
        self.client=None
        self.userdata=userdata
        
        self.username_pw_set(username,password)
        self.init(keepalive)
        self.flag=0
        self.sucess=None
        self.myPreRead=myPreRead
    def init(self,keepalive):
        try:
            print('connecting',self.ip,self.port)
            self.connect(self.ip,self.port,keepalive=keepalive)
        except Exception as e:
            print('connect server fail',e,self.ip,self.port)
            self.connectSuccee=False

    def _easy_log(self,*args,**kwargs):
        if args[0]==8:
            import traceback
            traceback.print_exc()
            print('log',args,kwargs)
        #print('log',args,kwargs)
        Client._easy_log(self,*args,**kwargs)
    def on_message(self,client, userdata, msg):
        print('recv',msg.topic,msg.payload)
        self.flag=1
        if self.topicRecvTail in msg.topic:
            key=msg.topic.replace(self.topicRecvTail,'')
        else:
            key=msg.topic+self.topicRecvTail
        f=self.topics.get(msg.topic,None)
        rt=dict()
        if f:
            if self.myPreRead:
                rt=self.myPreRead(self,msg.payload,f)
            else:
                rt=f(msg.payload)
            if rt:
                self.write(key,rt)
        return key,rt
    def on_subscribe(self,*args):
        pass
    def mySub(self,key,back):
        subTopic=self.topicFont+key
        print("sub",subTopic)
        #self.client.subscribe(subTopic)
        self.topics[subTopic]=back
      
    def on_connect(self,client,userdata, flags, rc):
        if rc==0:
            for key in self.topics:
                client.subscribe(self.topicFont+key,qos=self.qos)
            self.client=client
            self.connectSuccee=True
            if self.sucess:
                self.sucess()
            print('connect succes',flags)
        else:
            print('connect error',flags)
    def write(self,topic,data):
        print('send',topic,data)
        if isinstance(data,dict):
            data=json.dumps(data)
        self.flag=2
        self.publish(topic,data,qos=self.qos)
    def myloop(self,fun=None):
        if fun:
            self.sucess=fun
        self.loop_forever()
