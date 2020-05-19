from common.server import TcpServer,SerialClient
from common.function import crc16,bytesToint,intToBytes
import time
import traceback

class ModbusTcp(TcpServer):
    def __init__(self,ip,port):
        TcpServer.__init__(self,ip,port)
    def modbusRead(self,addr,index,num):
        return [1]*num
    def modbusWrite(self,addr,index,num):
        #print('write',addr,index,num)
        pass
    def readData(self,data):
        if data[1]==3:
            rs=self.modbusRead(data[0],data[2]*256+data[3],data[4]*256+data[5])
            rt=[]
            for d in rs:
                rt.append((d>>8)&0xff)
                rt.append(d&0xff)
            #rt=crc16(bytearray(rt),'add_tail')
            return data[0:2]+bytearray([len(rt)])+bytearray(rt)
        elif data[1]==6:
            self.modbusWrite(data[0],data[2]*256+data[3],data[4]*256+data[5])
            return data
    def read(self,data):
        #print('tcpread',data)
        try:
            rt=self.readData(data[6:])
            send=data[0:5]+bytearray([len(rt)])+rt
            #print('tcpsend',send)
            return send
        except Exception as e:
            traceback.print_exc()
class ModbusRtu(SerialClient):
    def __init__(self,com,burd):
        SerialClient.__init__(self,com,burd,self.m_read)

    def m_read(self,data):
        all_num=len(data)
        #print('read',data)
        for i in range(all_num-2):
            if data[i]==1:
                crc_begin=i+6
                if crc_begin+1<all_num:
                    crc_value1,crc_value2=data[crc_begin],data[crc_begin+1]
                    crc_value=crc16(data[i:crc_begin])
                    if crc_value[0]==crc_value1 and crc_value[1]==crc_value2:
                        rt=crc16(self.readData(data[i:]),'add_tail')
                        if data[i+1]==0x03:
                            return rt
                        else:
                            return data[i:]
                    else:
                        pass
                        #print('crcCheckError',data,crc_value)

    def modbusRead(self,addr,index,num):
        return [1]*num
    def modbusWrite(self,addr,index,num):
        #print('write',addr,index,num)
        pass
    def readData(self,data):
        if data[1]==3:
            rs=self.modbusRead(data[0],data[2]*256+data[3],data[4]*256+data[5])
            rt=[]
            for d in rs:
                rt.append((d>>8)&0xff)
                rt.append(d&0xff)
            #rt=crc16(bytearray(rt),'add_tail')
            return data[0:2]+bytearray([len(rt)])+bytearray(rt)
        elif data[1]==6:
            self.modbusWrite(data[0],data[2]*256+data[3],data[4]*256+data[5])
            return data
import socket
from serial import Serial
class Moutbus():
    def __init__(self):
        self.index=0
        self.flag=False
        self.sock=None
    def readone(self,iporcom,burdorport,addr,cmd,index,value,**kwargs):
        try:
            sock=None
            rt=None
            if self.flag:return
            self.flag=True
            if '.' in iporcom:
                data=self.tcpwrite(addr,cmd,index,value)
                #if self.sock is None or iporcom!=self.ip
                sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
                sock.settimeout(kwargs.get('timeout',1))
                sock.connect((iporcom,burdorport))
                #sock.setblocking(False)
                #sock.setsockopt()
                sock.send(data)
                rt=sock.recv(1024)
                if rt:
                    rt=self.tcpread(rt,addr,cmd)
            else:
                data=self.rtuwrite(addr,cmd,index,value)
                kwargs['timeout']=kwargs.get('timeout',0.5)
                sock=Serial(port=iporcom,baudrate=burdorport,**kwargs)
                sock.write(data)
                rt=sock.read(1024)
                if rt:
                    rt=self.rturead(rt,addr,cmd)
                else:
                    rt=None              
        except Exception as e:
            #traceback.print_exc()
            pass
        finally:
            if sock:
                sock.close()
        self.flag=False
        return rt
    def tcpread(self,data,addr,cmd):
        #print('tcpread',self.index,addr,cmd,data)
        if len(data)>7 and self.index==bytesToint(data[0:2]):
            #num=(data[4]<<8)+data[5]
            if addr==data[6] and cmd==data[7]:
                if cmd==3:
                    return bytesToint(data[9:9+data[8]])
                elif cmd==6:
                    if len(data)>11:
                        return (data[10]<<8)+data[11]
                    else:
                        return 0
    def rturead(self,data,addr,cmd):
        all_num=len(data)
        for i in range(all_num-2):
            if data[i]==addr:
                if data[i+1]==3:
                    crc_begin=i+5
                else:
                    crc_begin=i+6
                if crc_begin+1<all_num:
                    crc_value1,crc_value2=data[crc_begin],data[crc_begin+1]
                    crc_value=crc16(data[i:crc_begin])
                    if crc_value[0]==crc_value1 and crc_value[1]==crc_value2:
                        if data[i+1]==cmd:
                            if cmd==3:
                                num=data[i+2]
                                return bytesToint(data[i+3:i+3+num])
                            else:
                                return 1
        return -1
    def tcpwrite(self,addr,cmd,index,value):
        self.index=(self.index+1)%6553500
        head=intToBytes(self.index,mode="small",num=2)
        rt=[addr,cmd,(index>>8)&0xff,index&0xff,(value>>8)&0xff,value&0xff]
        num=len(rt)
        nums=intToBytes(num,mode="small",num=4)
        return bytearray(head+nums+rt)
    def rtuwrite(self,addr,cmd,index,value):
        rt=bytearray([addr,cmd,(index>>8)&0xff,index&0xff,(value>>8)&0xff,value&0xff])
        return crc16(rt,head="add_tail")
def test():
    ModbusRtu('COM1',9600)
    ModbusTcp('0.0.0.0',9600)
    time.sleep(2)
    c=Moutbus()
    print(c.readone('127.0.0.1',9600,1,3,1,1))
    print(c.readone('127.0.0.1',9600,1,6,1,1))
    print(c.readone('COM2',9600,1,3,1,1))
    print(c.readone('COM2',9600,1,6,1,1))
    print(c.readone('COM2',9600,1,3,1,1))
    input('exit')
if __name__ == "__main__":
    test()