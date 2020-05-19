import os
import json
from . import msg
from common import function #import function.uid,function.copy,function.get_host_ip,function.intToBytes,function.bytesToint,function.rmDir,function.Pid,
import time
import _thread
import traceback
DEVICES_TREE=dict()
class Base(object):
    param=None
    topics=[]
    clsMap={}
    io=None
    projectKey=""
    has_thread=True
    def __init__(self,Id,parent,**kwargs):
        if parent is None:
            self.dir=Id
        else:
            self.dir=parent.dir+'/'+Id
        self.parent=parent
        self.param.update(kwargs)
        self.param['Id']=Id
        DEVICES_TREE[Id]=self
        self.param['class']=self.__class__.__name__
        self.param['className']=function.uid(self.__class__.__name__)
        oldchild=self.param.get('children',[])
        self.param['children']=[]
        self.param['children'].extend(oldchild)
        self.init()
    def error(self,msg,statu=-1):
        return dict(msg=msg,code=statu)
    def _remove(self,index):
        self.config['enable']=False
        self.parent.config['children'].pop(index)
        self.parent.save()
        del DEVICES_TREE[self.config['Id']]
        function.rmDir(self.dir)
    def initdir(self):
        if not os.path.exists(self.dir):
            os.mkdir(self.dir)
        filePath=self.dir+'/config.json'
        if not os.path.exists(filePath):
            with open(filePath,'w') as f:
                f.write(self.dumps(self.param))
                f.flush()
                f.close()
        with open(filePath,'r') as f:
            self.config=self.loads(f.read())
            #function.log(self.param,self.config)
            for key in self.param:
                if key!='children':
                    self.config[key]=self.param[key]
            for key in self.param:
                if key not in self.config:
                    self.config[key]=self.param[key]
            self.initChildren(self.config['children'])
        self.save()
    def initChildren(self,children):
        for i in range(len(children)):
            b=None
            if isinstance(children[i],str):
                with open(children[i]+'/config.json','r') as f:
                    b=json.loads(f.read())
                    did=b['Id']
                    del b['Id']
                    children[i]=self.clsMap[b['class']](did,self,**b)
            else:
                b=children[i]
                kg={} if len(b)<3 else b[2]
                children[i]=self.clsMap[b[1]](b[0],self,**kg)
            children[i].config['_index']=i               
        for topic in self.topics:
            self.io.mySub(self.topicHead+topic,self.callback)
    def save(self):
        with open(self.dir+'/config.json','w') as f:
            saveOj={}
            for key in self.config:
                if isinstance(self.config[key],list):
                    saveOj[key]=[]
                    for d in self.config[key]:
                        if isinstance(d,Base):
                            saveOj[key].append(d.dir)
                        else:
                            saveOj[key].append(d)
                else:
                    saveOj[key]=self.config[key]
            vu=self.dumps(saveOj)
            f.write(vu)
            f.flush()
    def callback(self,method,data):
        cls=self.clsMap[data.pop('class')]
        f=getattr(self,method)
        rt=f(cls,**data)
        if isinstance(rt,Base):
            rt=rt.dump()
        elif isinstance(rt,list):
            rt=[d.dump() if isinstance(d,Base) else d for d in rt]
        return rt
    def init(self):
        self.initdir()
        self.initFinish()
    
    def initFinish(self):
        pass

    def test(self,testlist):
        function.log('testBegin')
        for testTask in testlist:
            function.log(testTask)
            if len(testTask)==3:
                num=testTask[2]
            else:
                num=1
            for i in range(num):
                function.log(i,self.dumps(self.callback(testTask[0],testTask[1])))
        function.log('testFinish')
    
    def as_complex(self,dct):
        return dct

    def encode_complex(self,obj):
        if isinstance(obj, complex):
            return [obj.real, obj.imag]
        elif obj is None:
            return None
        elif isinstance(obj,Base):
            return obj.dump()
        raise TypeError(repr(obj) + " is not JSON serializable")


    def dump(self,*args,**kwargs):
        dt={}
        for key in self.config:
            if key!='children':
                dt[key]=self.config[key]
        return dt

    def loads(self,v):
        rt=None
        try:
            rt=json.loads(v,object_hook=self.as_complex)
        except Exception as e:
            traceback.print_exc()
            function.log('jsonloads',e,v)
        return rt
    
    def dumps(self,v):
        return json.dumps(v,default=self.encode_complex,indent=4)


    @property
    def topicHead(self):
        p=self
        ids=[]
        while p:
            ids.append(p.config['Id'])
            p=p.parent
        ids.reverse()
        return '/sys/'+self.projectKey+'/'+"_".join(ids)
    def setValue(self,key,value,autoSave=True):
        self.config[key]=value
        if autoSave:
            self.save()
class Event(Base):
    def __init__(self,Id,parent,**kwargs):
        self.param=msg.Event().param()
        Base.__init__(self,Id,parent,**kwargs)
    def loop(self):
        identity=self.parent._search(Identifier,self.config['identifierId'])
        if len(identity)==0:
            #function.log('looptest',self.config['identifierId'],[d.config['Id'] for d in self.parent.config['children']])
            return
        hfun=lambda a,b:a is not None and a>b
        lfun=lambda a,b:a is not None and a<b
        eventFun=dict(alarmhh=hfun,alarmh=hfun,alarml=lfun,alarmll=lfun)
        ps=eventFun[self.config['alarm']](identity[0].config['value'],self.config['value'])
        if ps:
            for link in self.config['Link']:
                #function.log('loglink',link['deviceId'],self.parent.parent.config['Id']
                for aim in self.parent._search(None,link['deviceId']):
                    aim.writeIdentity(link['identifierId'],link['value'])
class Task(Base):
    def __init__(self,Id,parent,**kwargs):
        self.param=msg.Task().param()
        Base.__init__(self,Id,parent,**kwargs)
    def loop(self):
        datetimes=time.localtime(time.time())
        weekNames=["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]
        tasklist=[
            [self.config['starttime'].split(':'),self.config['onstartup'],'startrun'],
            [self.config['endtime'].split(':'),self.config['onfinished'],'endrun']
        ]
        tsToInt=lambda a:int(a[0])*3600+int(a[1])*60+int(a[2])
        if self.config['weekday'][weekNames[datetimes[6]]]:
            for task in tasklist:
                b,e=tsToInt(task[0]),tsToInt(datetimes[3:])
                #function.log(task[2],b>e)
                if b>e:   
                    self.config[task[2]]=False
                else:
                    if self.config.get(task[2],False)==False:
                        for taskdo in task[1]:
                            self.parent.writeIdentity(taskdo["Id"],taskdo['value'])
                    self.config[task[2]]=True
class Prop(Base):
    def __init__(self,Id,parent,**kwargs):
        self.param=msg.Prop().param()
        Base.__init__(self,Id,parent,**kwargs)

class Identifier(Base):
    
    def __init__(self,Id,parent,**kwargs):
        self.param=msg.Identifier().param()
        self.pid=function.Pid(kwargs)
        Base.__init__(self,Id,parent,**kwargs)
    def initFinish(self):
        self.pid.setPid(self.config)
    def dump(self,key=None):
        # rt=dict(value=self.config['value'],Id=self.config['Id'],lastValue=self.config['lastValue'])
        # for key in ['value','Id','lastValue','class','convert_k','convert_b','enable','watchType']:
        #     rt[key]=self.config[key]
        return self.config
    def update(self,cls,Id,**kwargs):
        self.config.update(kwargs)
        if kwargs.get('watchType',None)=='on_pid':
            self.pid.setPid(kwargs)
        if self.config['openMode'][0]=='w' and 'value' in kwargs:
            self.parent.deviceWrite(**self.config)
        else:
            self.config['value']=self.parent.deviceRead(**self.config)
        self.save()
    def loop(self):
        if self.config.get('openMode',None)!='wb' and self.parent.num%self.config['waitNum']==0:
            self.config['value']=self.parent.deviceRead(**self.config)
            if self.config['value'] is None:return
            if self.config['watchType']=='on_change':
                if abs(self.config['lastValue']-self.config['value'])>self.config['watchChangeValue']:
                    self.parent.write(self.dump('watchType'))
                    self.config['lastValue']=self.config['value']
            elif self.config['watchType']=='on_time':
                self.parent.write(self.dump('watchType'))
            elif self.config['watchType']=='on_pid':
                pidSet=self.parent.readIdentity(self.config['pid_in'])
                if pidSet is not None:
                    rt=self.pid.run(pidSet,self.config['value'])
                    self.parent.writeIdentity(self.config['pid_set'],rt)
                #function.log(self.config['pid_in'],pidSet,self.config['Id'],self.config['value'],self.config['pid_set'],rt)
class Device(Base):
    topics=msg.TPOICS
    has_thread=False
    def __init__(self,Id,parent,**kwargs):
        #self.param=msg.Device().param()
        self.num=0
        Base.__init__(self,Id,parent,**kwargs)
    def initFinish(self):
        if self.has_thread is False:
            _thread.start_new_thread(self.loop,())
    def add(self,cls,Id,**kwargs):
        device=self._search(None,Id)
        if len(device)==0:
            device=cls(Id,self,**kwargs)
            self.config['children'].append(device)
            self.save()
            return self.error("success",statu=0)
        else:
            function.log('add error',Id,[d.config['Id'] for d in self.config['children']])
            return self.error("id exist")

    def _search(self,cls,Id=None,**kwargs):
        rt=[]
        if Id and Id in DEVICES_TREE:
            return [DEVICES_TREE[Id]]
        if self.parent and self.parent.config['Id']==Id:
            return [self.parent]
        elif Id==self.config['Id']:
            return [self]
        for d in self.config['children']:
            if isinstance(d,str):continue
            if (Id is None or d.config['Id']==Id) and (cls is None or d.config['class']==cls.__name__):
                rt.append(d)
        return rt
    def search(self,cls,Id,**kwargs):
        return self._search(cls,None)
    def delete(self,cls,Id,**kwargs):
        index=-1
        for d in self.config['children']:
            index+=1
            if d.config['Id']==Id and d.config['class']==cls.__name__:
                d._remove(index)
                break

    def update(self,cls,Id,**kwargs):
        self.updateBefore(cls,Id,kwargs)
        if Id is None or Id==self.config['Id']:
            for key in kwargs:
                self.setValue(key,kwargs[key],autoSave=False)
            self.save()
            return self.dump()
        else:
            g=self._search(None,Id)
            if not len(g):
                return self.error('can not find'+Id)
            else:
                return g[0].update(cls,Id,**kwargs)
    def upload(self,cls,Id,**kwargs):
        pass
    def query(self,cls,Id,**kwargs):
        if Id=='_SELF':
            return self.dump()
        else:
            return self._search(cls,Id)
    def updateBefore(self,cls,Id,value):
        pass
    def write(self,data,topic=None):
        if isinstance(data,(list,dict)):
            data=json.dumps(data,default=self.encode_complex)
        topic=topic or msg.FG['TP_PARAM_POST'].replace('_replay','')
        self.io.write(self.topicHead+topic,data)

    def loop(self):
        while self.config['enable']:
            for child in self.config['children']:
                if child.config['enable'] and child.has_thread:
                    child.loop()
            self.num=(self.num+1)%1000000
            time.sleep(self.config.get('interval',1000)/1000)
        function.log(self,'exit')
    def writeDelay(self,f,cls,Id,kwargs):
        self.io.userdata["code"]=201
        #function.log(self,cls,Id,f,kwargs)
        sleepTime=kwargs.pop('waiting')/1000
        data=dict(Id=Id)
        data['class']=cls.__name__
        data['data']=f(kwargs)
        time.sleep(sleepTime)    
        self.io.userdata["code"]=200
        self.write(data)
    def deviceWrite(self,**kwarg):
        pass
    def deviceRead(self,**kwarg):
        pass
    def writeIdentity(self,Id,value):
        for taskaim in self._search(Identifier,Id):
            taskaim.config['value']=value
            #function.log('writeiden',taskaim.config)
            self.deviceWrite(**taskaim.config)
    def readIdentity(self,Id):
        for taskaim in self._search(Identifier,Id):
            #function.log('writeiden',taskaim.config)
            return self.deviceRead(**taskaim.config)
import time
if os.name == "nt":
    class ioGet:
        def __getattribute__(self,key):
            def f(*args,**kwargs):
                if key=='run': return '-1,0,0,0,0,0,0,0,0,0,0,0,0'
                return 1
            return f
    myio=ioGet()
    from ctypes import CDLL,c_bool,c_ubyte,c_ushort,c_int64
    try:
        DLL=CDLL('lib/moutbus/out/mainwin.dll')
    except Exception as e:
        DLL=ioGet()
    class MoutbusTcp(Device):
        param=function.copy(msg.MoutbusTcp.p)
        def __init__(self,Id,parent,**kwargs):
            Device.__init__(self,Id,parent,**kwargs)
        def initFinish(self):
            self.ctx=c_int64(DLL.modbus_new_tcp(
                self.param["ip"].encode('utf-8'),
                self.param["port"]))
            DLL.modbus_set_debug(self.ctx, c_bool(1))
        def deviceRead(self,command,**kwargs):
            command=command[0]
            data=[]
            return self.Write(command,data,**kwargs)
        def deviceWrite(self,command,value,**kwargs):
            command=command[1]
            data=function.intToBytes(value or 0,'big')
            return self.Write(command,data,**kwargs)
        def Write(self,command,data,addr,index,num,**kwargs):
            return None
            DLL.modbus_set_slave(self.ctx,addr)
            rt=None
            if DLL.modbus_connect(self.ctx)==-1:
                return None
            if command==1:
                destbit=(c_ubyte*num)()
                DLL.modbus_read_bits(self.ctx, index, num, destbit)
            elif command==2:
                destbit=(c_ubyte*num)()
                DLL.modbus_read_input_bits(self.ctx, index, num, destbit)
            elif command==3:
                destbit=(c_int64*num)()
                destbit[0]=3
                DLL.modbus_read_registers(self.ctx, index, num, destbit)
            elif command==4:
                destbit=(c_ushort*num)()
                DLL.modbus_read_input_registers(self.ctx, index, num,destbit)
            elif command==5:
                rt=DLL.modbus_write_bit(self.ctx,index,num)
            elif command==6:
                rt=DLL.modbus_write_register(self.ctx, index, kwargs['value'])
            elif command==15:
                destbit=(c_ubyte*num)(*data)
                rt=DLL.modbus_write_bits(self.ctx, index, num,destbit)
            elif command==10:
                destbit=(c_ubyte*num)(*data)
                rt=DLL.modbus_write_registers(self.ctx, index, num,  destbit)
            if rt==-1:return None
            if rt is None:
                rt=function.bytesToint(destbit,mode="big")
            DLL.modbus_close(self.ctx)
            return rt
        def updateBefore(self,cls,Id,value):
            self.ctx=c_int64(DLL.modbus_new_tcp(
                value["com"].encode('utf-8'),
                value["port"]))
            #DLL.modbus_set_debug(self.ctx, c_bool(1))
else:
    import moutbusPy as DLL
    import myio
    class MoutbusTcp(Device):    
        def __init__(self,Id,parent,**kwargs):
            self.param=dict(ip="192.168.1.157",port=502)
            Device.__init__(self,Id,parent,**kwargs)
        def initFinish(self):
            self.ctx=DLL.modbus_new_tcp(
                self.config["ip"],
                self.config["port"])
            _thread.start_new_thread(self.loop,())
        def Write(self,command,addr=1,index=1,num=1,value=0,**kwargs):
            DLL.modbus_set_slave(self.ctx,addr)
            rt=None
            #function.log('run',self.ctx,command,index,num,value)
            rt=int(DLL.modbus_run(self.ctx,command,index,num,value or 0))
            if rt==-1:
                return None
            return rt
        def updateBefore(self,Id,cls,v):
            if Id==self.config['Id']:
                self.ctx=DLL.modbus_new_tcp(
                    v["ip"],
                    v["port"])
        def deviceRead(self,command,**kwargs):
            command=command[0]
            return self.Write(command,**kwargs)
        def deviceWrite(self,command,**kwargs):
            command=command[1]
            #function.log(command,kwargs)
            return self.Write(command,**kwargs)
        # def query(self,cls,Id,**kwargs):
        #     if cls==Identifier:
        #         if kwargs['value']!=-1:
        #             return self.deviceWrite(**kwargs)
        #         else:
        #             return self.deviceRead(**kwargs)
        #     else:
        #         return Device.query(self,cls,Id,**kwargs)
class MoutbusSerial(MoutbusTcp):
    def __init__(self,Id,parent,**kwargs):
        self.param=function.copy(msg.MoutbusSerial.p)
        Device.__init__(self,Id,parent,**kwargs)
    def initFinish(self):
        function.log(self.config)
        self.ctx=DLL.modbus_new_rtu(
            msg.COM_NAMES[self.config["port"]],
            self.config["baudrate"],
            self.config["parity"],
            self.config["databit"],
            self.config["stopbit"],
        )
        _thread.start_new_thread(self.loop,())
    def updateBefore(self,cls,Id,value):
        self.ctx=DLL.modbus_new_rtu(
            msg.COM_NAMES[self.config["port"]],
            self.config["baudrate"],
            self.config["parity"],
            self.config["databit"],
            self.config["stopbit"]
        )
            #DLL.modbus_set_debug(self.ctx, c_bool(1))
from bacpypes.core import run,deferred
from bacpypes.local.device import LocalDeviceObject
from bacpypes.app import BIPSimpleApplication
from bacpypes.apdu import ReadPropertyRequest,ReadPropertyACK,WritePropertyRequest
from bacpypes.iocb import IOCB
from bacpypes.primitivedata import Null, Atomic, Boolean, Unsigned, Integer, \
    Real, Double, OctetString, CharacterString, BitString, Date, Time, ObjectIdentifier,Tag
from bacpypes.constructeddata import Array, Any, AnyAtomic,ArrayOf
from bacpypes.object import get_datatype 
from bacpypes.pdu import Address,RemoteStation
class BacnetApp(BIPSimpleApplication):
    def __init__(self,*args,**kwarg):
        self.userdata=None
        BIPSimpleApplication.__init__(self,*args,**kwarg)
    def do_IAmRequest(self,apdu):
        function.log('iam',apdu.iAmDeviceIdentifier[0],apdu.iAmDeviceIdentifier[1])
        device=dict(
            Id="%s:%s"%(apdu.iAmDeviceIdentifier[0],apdu.iAmDeviceIdentifier[1]),
            pduSource=[apdu.pduSource.addrNet,[d for d in apdu.pduSource.addrAddr]],
        )
        if self.userdata is not None:
            self.userdata.append(device)
        self.read(device['pduSource'],device['Id'],'objectList',device)
    def who_is(self,config):
        function.log('whoIs',config)
        self.userdata=[]
        BIPSimpleApplication.who_is(self,
            low_limit=config['lowlimits'],
            high_limit=config['highlimits']
        )
        return self.userdata
    def read(self,pduSource,obj_id,key,device,read=None):
        #function.log('request',pduSource,obj_id,key,device)
        if isinstance(obj_id,str):
            obj_id=obj_id.split(':')
            obj_id[1]=int(obj_id[1])
        request=ReadPropertyRequest(
            objectIdentifier=tuple(obj_id),
            propertyIdentifier=key,
            destination=RemoteStation(pduSource[0] or 0,bytearray(pduSource[1]))
        ) 
      
        iocb = IOCB(request)            
        iocb.context=device,key
        iocb.add_callback(read or self.readBack)
        self.request_io(iocb)
    def readBack(self,iocb):
        apdu=iocb.ioResponse
        if not isinstance(apdu, ReadPropertyACK):return
        if iocb.context[1]=='objectList':
            value=apdu.propertyValue.cast_out(ArrayOf(ObjectIdentifier))
            value=["%s:%s"%(v[0],v[1]) for v in value]
        else:
            datatype = get_datatype(apdu.objectIdentifier[0], apdu.propertyIdentifier)
            if issubclass(datatype, Array) and (apdu.propertyArrayIndex is not None):
                if apdu.propertyArrayIndex == 0:
                    value = apdu.propertyValue.cast_out(Unsigned)
                else:
                    value = apdu.propertyValue.cast_out(datatype.subtype)
            else:
                value = apdu.propertyValue.cast_out(datatype)
        iocb.context[0][iocb.context[1]]=value
        #function.log('resulttest1',id(iocb.context[0]),iocb.context[0])
    def writeValue(self,addr,obj_id,prop_id,value,indx=None,priority=None):
        if isinstance(obj_id,str):
            obj_id=obj_id.split(':')
            obj_id[1]=int(obj_id[1])
        addr=RemoteStation(addr[0],bytearray(addr[1]))
        datatype = get_datatype(obj_id[0],prop_id)
        if datatype is None:return
        if (value == 'null'):
            value = Null()
        elif issubclass(datatype, AnyAtomic):
            dtype, dvalue = value.split(':', 1)
            datatype = {
                'b': Boolean,
                'u': lambda x: Unsigned(int(x)),
                'i': lambda x: Integer(int(x)),
                'r': lambda x: Real(float(x)),
                'd': lambda x: Double(float(x)),
                'o': OctetString,
                'c': CharacterString,
                'bs': BitString,
                'date': Date,
                'time': Time,
                'id': ObjectIdentifier,
                }[dtype]
            value = datatype(dvalue)
        elif issubclass(datatype, Atomic):
            if datatype is Integer:
                value = int(value)
            elif datatype is Real:
                value = float(value)
            elif datatype is Unsigned:
                value = int(value)
            value = datatype(value)
        elif issubclass(datatype, Array) and (indx is not None):
            if indx == 0:
                value = Integer(value)
            elif issubclass(datatype.subtype, Atomic):
                value = datatype.subtype(value)
            elif not isinstance(value, datatype.subtype):
                raise TypeError("invalid result datatype, expecting %s" % (datatype.subtype.__name__,))
        elif not isinstance(value, datatype):
            raise TypeError("invalid result datatype, expecting %s" % (datatype.__name__,))
        # build a request
        request = WritePropertyRequest(
            objectIdentifier=tuple(obj_id),
            propertyIdentifier=prop_id,
            destination=addr
        )
        # save the value
        request.propertyValue = Any()
        request.propertyValue.cast_in(value)
        if indx is not None:
            request.propertyArrayIndex = indx
        if priority is not None:
            request.priority = priority
        iocb = IOCB(request)
        self.request_io(iocb)

BACNETAPP=BacnetApp(LocalDeviceObject(vendorIdentifier=123,objectIdentifier=127),('0.0.0.0',47808))
_thread.start_new_thread(run,())
BACNETAPP.i_am()
BACNETAPP.who_is({'lowlimits':2,'highlimits':10})
class Bacnet(Device):
    def __init__(self,Id,parent,**kwargs):
        self.param=function.copy(msg.Bacnet.p)
        Device.__init__(self,Id,parent,**kwargs)
    def deviceWrite(self,propertyIdentifier,value,**kwargs):
        BACNETAPP.writeValue(
            self.config['bacip'],propertyIdentifier,'presentValue',value)
    def deviceRead(self,propertyIdentifier,timeOut=1,**kwargs):
        result={}
        BACNETAPP.read(
                self.config['bacip'],propertyIdentifier,'presentValue',device=result)
        time.sleep(timeOut)
        #function.log('resulttest2',result,id(result))
        rt=result.get("presentValue",kwargs['value'])
        return rt

    def query(self,cls,Id,**kwargs):
        # if cls==Identifier:
        #     f=Device._search(self,cls,Id)
        #     for key in ['propertyIdentifier']:
        #         kwargs[key]=f[0].config[key]
        #     if kwargs['value']==-1:
        #         return self.deviceRead(**kwargs)
        #     else:
        #         self.deviceWrite(**kwargs)
        # else:
        return Device.query(self,cls,Id)
class CanDevice(Device):
    def __init__(self,*arg,**kwargs):
        self.buff=""
        self.param=function.copy(msg.CanDevice.p)
        Device.__init__(self,*arg,**kwargs)
    def initFinish(self):
        s,p=self.config['Id'],self.config['bitrate']
        os.system('ip link set %s down'%s)
        os.system('ip link set %s up type can bitrate %s'%(s,p))
        _thread.start_new_thread(self.run,(s,))
        _thread.start_new_thread(self.loop,())
    def run(self,name):
        f=os.popen('candump %s'%name)
        size=50
        while self.config['enable']:
            if size!=1:
                s=f.read(size)
                size=1
                function.log('can readfirst',s)
            else:
                s=f.read(size)
                self.buff+=s
    def deviceRead(self,Id,**kwargs):
        b=self.buff
        self.buff=''
        return b
    def deviceWrite(self,Id,value,**kwargs):
        os.system('cansend %s %s'%(Id,value))
        return None
    def updateBefore(self,cls,Id,value):
        if self.config['enable']!=value.get('enable',True):
            if value['enable']:
                self.initFinish()
class Terminal(Device):
    sysIden=['L0','L1']
    regValue={
        "/dev/outcontro":[0,0],
        "/dev/ad542":[0,0,0],
        "/dev/mcp4725":[0,0,0,0],
        "/dev/ad779":[0,1,1,0],
        "/dev/dev_74hc59":[0,0],
        '/dev/iocontro':[0,0,0,0,0,0,0,0,0]
    }
    def __init__(self,Id,**kwargs):
        # self.param['children']=[
        #     [name,MoutbusSerial.__name__] for name in msg.COM_NAMES
        # ]
        self.param=msg.Device().param()
        self.param['children']=[]
        kwargs["interval"]=10
        for key in msg.REG_MAP:
            self.param['children'].append([key,Identifier.__name__,msg.REG_MAP[key]])
        for i in range(0,4):
            self.param['children'].append(['CAN_'+str(i+1),CanDevice.__name__,{}])
        #self.param['children'].append(['232_1',MoutbusSerial.__name__,{"port":0}])
        for i in range(1,5):
            self.param['children'].append(['485_'+str(i),MoutbusSerial.__name__,{"port":i}])
        self.updateFiles={}
        self.resources={}
        Device.__init__(self,Id,None,**kwargs)
    def initFinish(self):
        #self.write({})
        _thread.start_new_thread(self.runTer,())
        _thread.start_new_thread(self.loop,())
    def runTer(self):
        function.log('runTer')
        while True:
            for key in self.sysIden:
                value=DEVICES_TREE[key].config
                if key=='L0':
                    if self.io.flag==1:
                        value['value']=1
                    else:
                        value['value']=0
                    self.deviceWrite(**value)
                elif key=='L1':
                    if self.io.flag==2:
                        value['value']=1
                    else:
                        value['value']=0
                    self.deviceWrite(**value)
            self.io.flag=0
            time.sleep(1.5)
    def call(self,cls,Id,tp,data,**kwargs):
        if tp=="shell":
            os.system(data)
    def add(self,cls,Id,**kwargs):
        if cls==Identifier:
            if Id in msg.REG_MAP and Id not in self.sysIden:
                kwargs.update(msg.REG_MAP[Id])
            else:
                return self.error("invaliable Id %s"%Id)
        elif cls==MoutbusSerial:
            pass
            # if kwargs['port']<0 or kwargs['port']>=len(msg.COM_NAMES):
            #     return self.error('port should be [0-5]')
            # else:
            #     kwargs['port']=msg.COM_NAMES[kwargs['port']]
        return Device.add(self,cls,Id,**kwargs)
    def upload(self,cls,Id,index,total,data,**kwargs):
        if Id not in self.updateFiles:
            self.updateFiles[Id]=dict(data=[],writeFinish=False)
        self.updateFiles[Id]['data']+=data
        if index==total and self.updateFiles[Id]['writeFinish']==False:
            with open(Id,'wb') as f:
                f.write(bytearray(self.updateFiles[Id]['data']))
                self.updateFiles[Id]['data']=[]
                self.updateFiles[Id]['writeFinish']=True
                f.close()
        if all(map(lambda p: p['writeFinish'],self.updateFiles.values())):
            os.system('sh start.sh')
        return dict(index=index+1)
    def dump(self):
        return {
            "deviceid":self.config['Id'],
            "device-type":self.config['class'],
            "device-name":self.config.get('device-name',''),
            "version":msg.VER,
            "datetime":function.nowTs(tp='date')
        }
    def search(self,cls,Id,**kwargs):
        if cls==Bacnet:
            _thread.start_new_thread(self.writeDelay,(BACNETAPP.who_is,cls,Id,kwargs))
        elif cls==Device:
            return [d for d in self.config['children'] if not d.has_thread]
        return Device.search(self,cls,Id)
    def query(self,cls,Id,**kwargs):
        # if cls==Identifier:
        #     f=Device._search(self,cls,Id)
        #     for key in ['path','index','num','openMode','defaultValue']:
        #         kwargs[key]=f[0].config[key]
        #     if kwargs['value']!=-1:
        #         self.deviceWrite(**kwargs)
        #     else:
        #         return dict(Id=f[0].config['Id'],value=self.deviceRead(**kwargs))
        # else:
        return Device.query(self,cls,Id)
    def deviceWrite(self,path,index,openMode,value,**kwargs):
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
    def deviceRead(self,path,index,openMode,**kwargs):
        if path=='/virture/value':
            return kwargs['value']
        data=self.regValue[path[:-1]]
        if path=='/dev/ad7795':
            mp=[5,4,3,2,1,6]
            data[3]=mp[int(kwargs['Id'][-1:])]
            #function.log('read',kwargs['Id'],data)
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
        rt=[int(d) for d in myio.run(path,way,data,0).split(',')]
        return rt
    def updateBefore(self,cls,Id,value):
        if 'datetime' in value and os.name != "nt":
            from datetime import datetime
            t=value['datetime']
            if isinstance(t,int):
                t=datetime.fromtimestamp(t).strftime('%Y.%m.%d-%H:%M:%S')
            os.system('date -s %s'%t)
            os.system('hwclock -w')
            dt = datetime.now()
            function.log('now_data %s',dt.strftime('%Y-%m-%d %H:%M:%S'))
from common.modbus import ModbusRtu
class MRtu(ModbusRtu):
    regValue=Terminal.regValue
    def __init__(self):
        self.map=[None]*len(msg.REG_MAP.keys())
        for key in msg.REG_MAP:
            self.map[msg.REG_MAP[key]['regaddr']]=key
        ModbusRtu.__init__(self,'/dev/ttyO1' if os.name!='nt' else 'COM1',9600)
    def modbusRead(self,addr,index,num):
        #print('read',addr,index,num)
        rt=[0]*num
        for i in range(num):
            if index+i<len(self.map):
                v= DEVICES_TREE[self.map[index+i]].config
                if v['openMode'][0]!='w':
                    value=Terminal.deviceRead(self,**v)
                    if value is None:
                        rt[i]=v['value']
                    else:
                        v['value']=rt[i]=value
        return rt
    def modbusWrite(self,addr,index,value):
        #print('write',addr,index,value)
        if index<len(self.map):
            va=DEVICES_TREE[self.map[index]].config
            va['value']=value
            Terminal.deviceWrite(self,**va)

    def Write(self,*args,**kwargs):
        return Terminal.Write(self,*args,**kwargs)
MRtu()

for cls in Base.__subclasses__()+Device.__subclasses__()+[MoutbusSerial]:
    Base.clsMap[cls.__name__]=cls
for key in ['DO','DI','AO','AI']:
    Base.clsMap[key]=Identifier
Base.clsMap['485']=Base.clsMap['232']=MoutbusSerial
Base.clsMap['CAN']=MoutbusSerial

class InterfaceThread(Thread):
    DEVICES_TREE=None
    protos=[None,BacHelp(),None,Mhelp(),Mhelp(),Terminal(),None,Tc]
    def __init__(self,id,config):
        self.id=id
        self.config=config
        self.num=0
        self.devices=[]
        Thread.__init__(self,daemon=True)
    def update(self,cg):
        self.config=cg
    def run(self):
        while True:
            if self.config['enable']:
                for d in self.devices:
                    if self.num%d.config['interval']==0:
                        d.loop()
                self.num=(self.num+1)%10000000
            time.sleep(self.config['interval'])
        print(self.id,'exit')
    def read(self,p,kwrags):
        if kwrags['enable'] and p.config['protocol']<len(self.protos) and self.protos[p.config['protocol']]:
            rt=self.protos[p.config['protocol']].deviceRead(self.config,p,kwrags)
            if rt is not None:
                kwrags['value']=rt
        return rt
    def write(self,p,kwrags):
        if kwrags['enable'] and p.config['protocol']<len(self.protos):
            if isinstance(kwrags['value'],str):
                kwrags['value']=int(kwrags['value'])
            self.protos[p.config['protocol']].deviceWrite(self.config,p,kwrags)
class Interface:
    def __init__(self,mp):
        self.threadDict={}
        self.interface=None
        self.update(mp)
    def update(self,mp):
        self.interface=mp
        for key in mp:
            if key not in self.threadDict:
                self.threadDict[key]=InterfaceThread(key,mp[key])
                self.threadDict[key].start()
            else:
                self.threadDict[key].update(mp[key])

    def dump(self):
        return self.interface
    
    def set(self,key,v):
        if key in self.threadDict:
            if v.interface==self.threadDict[key]:return
            if v.interface:
                v.interface.devices.remove(v)
            v.interface=self.threadDict[key]
            self.threadDict[key].devices.append(v)
