from . import msg
from threading import Thread
from common import function 
from common.modbus import ModbusRtu,Moutbus
import time
from .bac import BacnetApp
try:
    import myio
    import moutbusPy as DLL
except:
    myio=None
    moutbusPy=None
class MRtu(ModbusRtu):
    DEVICES_TREE={}
    def __init__(self,name,burd):
        self.map=[None]*len(msg.REG_MAP.keys())
        for key in msg.REG_MAP:
            self.map[msg.REG_MAP[key]['regaddr']]=key
        ModbusRtu.__init__(self,name,burd)
    def modbusRead(self,addr,index,num):
        #print('read',addr,index,num)
        rt=[0]*num
        for i in range(num):
            if index+i<len(self.map):
                if self.map[index+i] in MRtu.DEVICES_TREE:
                    v=MRtu.DEVICES_TREE[self.map[index+i]].config
                else:
                    v=msg.REG_MAP[self.map[index+i]]
                    v['value']=0
                    v['id']=self.map[index+i]
                if v['openMode'][0]!='w':
                    value=Terminal.deviceRead(self,None,None,v)
                    if value is None:
                        rt[i]=0
                    else:
                        v['value']=rt[i]=value
        return rt
    def modbusWrite(self,addr,index,value):
        #print('write',addr,index,value)
        if index<len(self.map):
            va=MRtu.DEVICES_TREE[self.map[index]].config
            va['value']=value
            Terminal.deviceWrite(self,None,None,va)

    def Write(self,*args,**kwargs):
        return Terminal.Write(self,*args,**kwargs)
class Terminal:
    device_tree={}
    regValue={
        "/dev/outcontro":[0,0],
        "/dev/ad542":[0,0,0],
        "/dev/mcp4725":[0,0,0,0],
        "/dev/ad779":[0,1,1,0],
        "/dev/dev_74hc59":[0,0],
        '/dev/iocontro':[0,0,0,0,0,0,0,0,0]
    }
    def deviceWrite(self,config,device,kwargs):
        path,index,openMode,value=kwargs['path'],kwargs['index'],kwargs['openMode'],kwargs['value']
        if path=='/virture/value':return 
        if path=='/dev/dev_74hc595':
            value=[index,value]
        else:
            data=function.intToBytes(value,mode="small")
            if path[:-1]=='dev/mcp4725':
                self.regValue[path[:-1]][2]=self.regValue[path[:-1]][3]=0
            value=self.regValue[path[:-1]]
            for i in range(len(data)):
                value[i+index]=data[i]  
            #function.log('write',path,openMode,kwargs['defaultValue'])
            #print('write2',path,value,openMode)
        return self.Write(path,openMode,value) 
    def deviceRead(self,config,device,kwargs):
        path,index,openMode=kwargs['path'],kwargs['index'],kwargs['openMode']
        if path=='/virture/value':
            return kwargs['value']
        data=Terminal.regValue[path[:-1]]
        if path=='/dev/ad7795':
            mp=[5,4,3,2,1,6]
            data[3]=mp[int(kwargs['id'][-1:])]
            #function.log('read',kwargs['id'],data)
        value=self.Write(path,openMode,data)
        rt=kwargs['value']
        if value[0]==0:
            if path=='/dev/iocontrol':
                rt=value[8-index]          
            elif path=='/dev/ad7795':
                if value[1]==0:
                    rt=kwargs['value']
                else:
                    rt=function.bytesToint(value[2:4],mode="small")
            #function.log(path,openMode,kwargs['defaultValue'],rt,value,index,num)
        #print('read',path,rt)
        return rt
    def Write(self,path,way,data):
        data=','.join(["%x"%d for d in data])
        #return [0,0,0,0,0]
        if myio:
            rt=[int(d) for d in myio.run(path,way,data,0).split(',')]
        else:
            rt=[0,0,0,0,0,0,0,0,0,0,0,0]
        return rt

class Mhelp:
    def __init__(self,protype):
        self.protype=protype
        self.m=Moutbus()
    def deviceRead(self,config,device,param):
        ip_or_com,port_or_burd=self.getipname(config)
        return self.m.readone(
            ip_or_com,port_or_burd,
            device.config['slaveid'],
            3,param['address'],param['count'],time_out=param.get('wait',1),**config
        )
    def deviceWrite(self,config,device,param):
        ip_or_com,port_or_burd=self.getipname(config)
        self.m.readone(ip_or_com,port_or_burd,
            device.config['slaveid'],
            6,param['address'],param['value'],time_out=param.get('wait',1),**config
        )
    def getipname(self,config):
        return (config['ip'],config['port']) if self.protype==4 else (msg.COM_NAMES[config['port']],config['baudrate'])
class BacHelp:
    def __init__(self):
        self.ip=None
        self.port=None
        self.bac=None
    def init(self,ip,port):
        if ip!=self.ip or self.port!=port or self.bac is None:
            try:
                self.bac=BacnetApp((ip,port))
                self.port=port
                self.ip=ip
                return True
            except:
                self.bac=None
                raise Exception("error","%s:%s can not use"%(ip,port))
                return False
        return True
    def whoisback(self,data):
        MRtu.DEVICES_TREE[msg.FG['deviceid']].post(data,'bacnet_search')
    def ojback(self,data,address,key,devid):
        for d in data:
            MRtu.DEVICES_TREE[msg.FG['deviceid']].post(dict(objectid="%s:%s"%d,name='xxx'),'bacnet_search')
    def search(self,p,v,tp):
        if self.init(p['ip'],p.get('port',47808)):
            if tp=='Device':
                self.bac.who_is(v,self.whoisback)
            else:
                print(v)
                self.bac.read(v['address'],["device",v['bacnetid']],'objectList',self.ojback)
            #return self.bac.userdata
    def deviceRead(self,config,device,param):
        if self.init(config['ip'],config['port']):
            result={param["property_key"]:None}
            self.bac.read(
                device.config['address'],param["property_Identifier"],
                param["property_key"],result
            )            
            sleepTime=device.config.get('wait',2)
            while sleepTime>0 and result[param["property_key"]] is None:
                sleepTime-=0.1
                time.sleep(0.1)
            return result[param["property_key"]]
    def deviceWrite(self,config,device,param):
        if self.init(config['ip'],config['port']):
            self.bac.writeValue(
                device.config['address'],param["property_Identifier"],
                param["property_key"],param['value']
            )
class Tc:
    def deviceRead(self,config):
        pass
    def devcieWrite(self,config):
        pass
    
