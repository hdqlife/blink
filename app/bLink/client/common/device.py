
import json
from . import msg
import os
from common import function
import traceback
import collections
from common.server import MqttClient
from .proto import BacHelp,Mhelp,Terminal,Tc,MRtu
MRtu.DEVICES_TREE=DEVICES_TREE=dict()
import time
class Base(object):
    param=None
    clsMap={}
    io:MqttClient
    has_thread=True
    projectKey=msg.FG['productid']
    def __init__(self,id,parent,**kwargs):
        if parent is None:
            self.dir=id
        else:
            self.dir=parent.dir+'/'+id
        self.parent=parent
        self.param.update(kwargs)
        self.param['id']=id
        DEVICES_TREE[id]=self
        self.param['class']=self.__class__.__name__
        oldchild=self.param.get('children',[])
        self.param['children']=[]
        self.param['children'].extend(oldchild)
        self.param['enable']=kwargs.get('enable',True)
        self.lastonline=None
        self.online=None
        self.init()
    def error(self,message,statu=msg.CODE_ERROR):
        self.io.userdata['msg']=message
        self.io.userdata['statu']=statu
        raise Exception('errorDo',statu,message)
    def _remove(self,index):
        self.config['enable']=False
        self.parent.config['children'].pop(index)
        self.parent.save()
        del DEVICES_TREE[self.config['id']]
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
                    did=b['id']
                    del b['id']
                    children[i]=self.clsMap[b['class']](did,self,**b)
            else:
                b=children[i]
                kg={} if len(b)<3 else b[2]
                children[i]=self.clsMap[b[1]](b[0],self,**kg)
            children[i].config['_index']=i               

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

    def init(self):
        self.initdir()
        self.initFinish()
    
    def initFinish(self):
        pass
    
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
        dt['id']=self.config['id']
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


    def setValue(self,key,value,autoSave=True):
        self.config[key]=value
        if autoSave:
            self.save()
    
    def update(self,cls,id,**kwargs):
        self.config.update(kwargs)
        self.save()

class Event(Base):
    @staticmethod
    def p():
        rt={
            "id":"enentid",
            "Identifierid":"VI0",
            "enable": False,
            "alarm": "alarmhh",#alarmhh,alarmh,alarmll,alarml
            "value": 3,
            "state1":None,
            "state2":None,
            "state3":None,
            "state4":None,
            "repeat":12,
            "Link": [
                {
                    "deviceid": "aca213cfac04",#如果是终端设备就从它的子设备和自己中查找，如果是子设备就从它的父设备和父设备的子设备中查找
                    "Identifierid": "VI1",
                    "value": 1,
                }
            ]
        }
        return rt
    def __init__(self,id,parent,**kwargs):
        self.t=collections.defaultdict(int)
        self.param=Event.p()
        Base.__init__(self,id,parent,**kwargs)
    def loop(self):
        identity=self.parent._search(Identifier,self.config['Identifierid'])
        if len(identity)==0:
            #function.log('looptest',self.config['dentifierid'],[d.config['id'] for d in self.parent.config['children']])
            return
        hfun=lambda a,b:a is not None and a>=b
        lfun=lambda a,b:a is not None and a<b
        eventFun=dict(alarmhh=hfun,alarmh=hfun,alarml=lfun,alarmll=lfun)
        ps=eventFun[self.config['alarm']](identity[0].config['value'],self.config['value'])
        if ps:
            for link in self.config['Link']:
                #function.log('loglink',link['deviceid'],self.parent.parent.config['id']
                for aim in self.parent._search(None,link['deviceid']):
                    aim.writeidentity(link['Identifierid'],link['value'])
            self.post(self.config['alarm'])
        else:
            self.config['state']=[
                self.config['state1'],self.config['state2'],
                self.config['state3'],self.config['state4']
            ]
            for i in range(len(self.config['state'])):
                if self.config['state'][i]==self.config['value']:
                    self.post('state%s'%(i+1))
    def post(self,key):
        if time.time()-self.t[key]>self.config['repeat']:
            self.t[key]=time.time()
            self.parent.post(self,key)
class Task(Base):
    @staticmethod
    def p():
        rt={
            "id":"taskid",

            "enable":True,
            "weekday": {
                "monday": True,
                "tuesday": True,
                "wednesday": True,
                "thursday": True,
                "friday": True,
                "saturday": True,
                "sunday": True
            },
            "time": "07:00:00",
            "actions":  [
                {
                    "Identifierid": "VI0",
                    "deviceid":"",
                    "value": 4,
                }
            ]
        }
        return rt
    def __init__(self,id,parent,**kwargs):
        self.param=Task.p()
        Base.__init__(self,id,parent,**kwargs)
    def loop(self):
        datetimes=time.localtime(time.time())
        weekNames=["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]
        task=[self.config['time'].split(':'),self.config['actions'],'run']
        tsToInt=lambda a:int(a[0])*3600+int(a[1])*60+int(a[2])
        if self.config['weekday'][weekNames[datetimes[6]]]:
            b,e=tsToInt(task[0]),tsToInt(datetimes[3:])
            #function.log(task[2],b>e)
            if b>e:   
                self.config[task[2]]=False
            else:
                if self.config.get(task[2],False)==False:
                    for taskdo in task[1]:
                        for aim in self.parent._search(None,taskdo['deviceid']):
                            self.parent.writeidentity(taskdo["Identifierid"],taskdo['value'])
                self.config[task[2]]=True
class Interface(Base):
    protos=[None,BacHelp(),None,Mhelp(3),Mhelp(4),Terminal(),None,Tc]
    def __init__(self, id, parent, **kwargs):
        self.devices=[]
        self.param=Interface.p()
        self.num=0
        super().__init__(id, parent, **kwargs)
    @staticmethod
    def p():
        rt=dict(
            id="Terminal",
            port=1,baudrate=9600,parity='none',interval=1,enable=True,
            ip="",
        )
        return rt
    def initFinish(self):
        _thread.start_new_thread(self.run,())
    def run(self):
        while self.config['enable']:
            #print(self.config['id'],'run',self.num)
            for d in self.devices:
                if self.num%d.config['interval']==0:
                    d.loop()
            self.num=(self.num+1)%10000000
            sleep=self.config['interval']>=1000 if self.config['interval']/1000 else self.config['interval']
            time.sleep(sleep)
        print(self.config['id'],'exit')
    def read(self,p,kwrags):
        rt=None
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
    def update(self,cls,id,**kwarg):
        if kwarg.get('enable')!=self.config['enable'] and self.config['enable']:
            self.initFinish()
        Base.update(self,cls,id,**kwarg)
class Identifier(Base):
    @staticmethod
    def p():
        rt={
            "id":"dentifierid",
            "value":None,
            "last_value":None,
            "datatype":"int",
            "mode":0,#0 on_change 值发生变化时上传，1 on_time 上传. 
                                    #on_pid 表示这个资源，用于pid读
            "convert_k":1,        #数值换算y=kx+b中的K
            "convert_b":0,        #数值换算y=kx+b中的B
            "deadband":0,
            "interval":1,
            "class":"Identifier",#资源共有属性
            "wait":4,
            "check":0,#计算方式0 差值 1 百分比

            "address":1,#moutbus 读寄存器地址
            "count":1,#moutbuss 读寄存器个数
            

            "property_Identifier":"analogOutput:0",#BACNET 设备属性,
            "property_key":"presentValue",
            "enable":False,

           
            "pid_p":1,        #pid中的参数P 
            "pid_i":0,         #pid中的参数I
            "pid_d":0,        #pid中的参数D
            "pid_in":"dentifierid",   #pid中的测量值，自alink属性关联的寄存器读取
            "pid_set":"dentifierid",   #id中的目标值，自alink属性关联的寄存器读取
           
        }
        return rt
    def __init__(self,id,parent,**kwargs):
        self.param=Identifier.p()
        self.pid=function.Pid(kwargs)
        Base.__init__(self,id,parent,**kwargs)
    def initFinish(self):
        self.pid.setPid(self.config)
    def update(self,cls,id,**kwargs):
        self.config.update(kwargs)
        if kwargs.get('mode',None)==2:
            self.pid.setPid(kwargs)
        self.save()
    def loop(self):
        rt=self.parent.deviceRead(self.config)
        if rt is None:return
        self.config['value']=rt
        if self.config['mode']==1:
            if self.config['last_value'] is None:
                self.config['last_value']=self.config['value']
            value=abs(self.config['last_value']-self.config['value'])
            if self.config['check']==1 and self.config['last_value']!=0:
                value=value/self.config['last_value']
            if value>self.config['deadband']:
                self.parent.post(self)
                self.config['last_value']=self.config['value']
        elif self.config['mode']==0:
            self.parent.post(self)
        elif self.config['mode']==2:
            pidSet=self.parent.readidentity(self.config['pid_in'])
            if pidSet is not None:
                rt=self.pid.run(pidSet,self.config['value'])
                self.parent.writeidentity(self.config['pid_set'],rt)
                self.parent.post(self)
                #function.log(self.config['pid_in'],pidSet,self.config['id'],self.config['value'],self.config['pid_set'],rt)
class Download(Base):
    updateFiles=dict()
    def __init__(self, id):
        self.path=id
    def write(self,value,**kwargs):
        if self.path not in Download.updateFiles:
            Download.updateFiles[self.path]=dict(data=[],writeFinish=False)
        message='downloading...'
        
        if kwargs['index']==kwargs['total'] and Download.updateFiles[self.path]['writeFinish']==False:
            writedata=bytearray(Download.updateFiles[self.path]['data'])
            md5dst=function.md5(writedata)
            print('checkmd5',md5dst,kwargs['md5src'])
            if md5dst==kwargs['md5src']:
                function.writeFile(self.path,writedata)
                del Download.updateFiles[self.path]
                if self.path[0:5]=='bLink' and self.path[-4:]=='.tar':
                    os.system('tar -xzvf %s'%self.path)
                    os.system('sh shell/run.sh &')
                message="downloadfinish"
            else:
                message="check md5 error%s"%md5dst
        else:
            Download.updateFiles[self.path]['data']=Download.updateFiles[self.path]['data'][:kwargs["index"]]+value
        return dict(index=kwargs["index"]+len(value),msg=message)
class Shell(Base):
    @staticmethod
    def run(cmd,timeout=3):
        s=['']
        def loop():
            s[0]=os.popen(cmd).read()
        _thread.start_new_thread(loop,())
        while timeout and not s[0]:
            timeout-=0.1
            time.sleep(0.1)
        return s[0]
import _thread
class Device(Base):
    topics=msg.TPOICS
    @staticmethod
    def p():
        rt={
            "id": "deviceid",
            "device_type":"",
            "device_name":"",
            "datetime": "2020-02-10 12:00:00",
            "class":"Device",
            "enable": False,
            "slaveid":1,
            "interval":1,
            "protocol":0,
            "interface":'Terminal',
            "address":['192.168.1.142',47808]
        }
        return rt
    def __init__(self,id,parent,**kwargs):
        self.param=Device.p()
        self.param['children']=[]
        self.num=0
        Base.__init__(self,id,parent,**kwargs)
    def initFinish(self):
        self.has_thread=False
        for topic in self.topics:
            self.io.mySub(self.topicHead+topic,self.callback)
    def callback(self,method,data):
        cls=self.clsMap.get(data.pop('class'),None)
        if cls is None:self.error('error class',msg.CODE_ERROR_CLASS)
        f=getattr(self,method,None)
        if f is None:self.error('error type',msg.CODE_ERROR_TYPE)
        id=self.config['id'] if 'id' not in data else data.pop('id')
        rt=f(cls,id,**data)
        if isinstance(rt,Base):
            rt=rt.dump()
        elif isinstance(rt,list):
            rt=[d.dump() if isinstance(d,Base) else d for d in rt]
        return rt
    def addPre(self,cls,id,**kwargs):
        if len(self._search(cls,id)):
            return self.error('%s is exist'%id)
        if self.parent is None:
            if cls==Identifier:
                if id not in msg.REG_MAP:
                    return self.error('%s not in regmap'%id)
                else:
                    return msg.REG_MAP[id]
            if cls==Device:
                if kwargs['interface'] not in DEVICES_TREE:
                    return self.error('%s not in interfaces'%kwargs['interface'] )
        return kwargs
    def add(self,cls,id,**kwargs):
        rt=self.addPre(cls,id,**kwargs)
        device=cls(id,self,**rt)
        self.config['children'].append(device)
        self.save()
           

    def _search(self,cls,id=None,**kwargs):
        rt=[]
        if id and id in DEVICES_TREE:
            return [DEVICES_TREE[id]]
        if self.parent and self.parent.config['id']==id:
            return [self.parent]
        elif id==self.config['id']:
            return [self]
        for d in self.config['children']:
            if isinstance(d,str):continue
            if (id is None or d.config['id']==id) and (cls is None or d.config['class']==cls.__name__):
                rt.append(d)
        return rt
    def search(self,cls,id,**kwargs):
        if (cls==Device or cls==Identifier) and kwargs.get('type',None) is None:
            interid=kwargs['interface'] if cls==Device else self.parent.config['interface']
            if interid not in DEVICES_TREE:self.error("%s not exist"%interid,msg.CODE_ERROR)
            inter=DEVICES_TREE[interid].config
            kw=kwargs if cls==Device else self.config
            def loop():
                try:
                    rt=Interface.protos[1].search(inter,kw,cls.__name__)
                    self.io.userdata['code']=msg.CODE_DEVICE_BUSY
                    time.sleep(kwargs['waiting'])
                except Exception as e:
                    traceback.print_exc()
                    self.io.userdata['code']=msg.CODE_ERROR
                    self.io.userdata['msg']=str(e)
                else:
                    self.io.userdata['code']=msg.CODE_RIGHT
                    #self.post(rt,'bacnet_search')
                    self.post([])
            _thread.start_new_thread(loop,())
        else:
            return self._search(cls,None)
    def delete(self,cls,id,**kwargs):
        if cls==Device and self.parent:
            self.parent.delete(Device,self.config['id'])
        else:
            index=-1
            for d in self.config['children']:
                index+=1
                if d.config['id']==id and d.config['class']==cls.__name__:
                    d._remove(index)
                    break

    def update(self,cls,id,**kwargs):
        self.updateBefore(cls,id,kwargs)
        if id is None or id==self.config['id']:
            for key in kwargs:
                self.setValue(key,kwargs[key],autoSave=False)
            self.save()
            return self.dump()
        else:
            g=self._search(None,id)
            if len(g):
                return g[0].update(cls,id,**kwargs)
            else:
                self.error('can not find'+id)
    def query(self,cls,id,**kwargs):
        return self._search(cls,id)
    def updateBefore(self,cls,id,value):
        pass
    def post(self,child,message='',code=msg.CODE_RIGHT):
        import uuid
        data=dict(id=str(uuid.uuid1()).replace('-',''),code=code,msg=message,type="upload",data=[])
        data['class']="Props"
        if message=='bacnet_search':
            data['type']="search"
            data['code']=msg.CODE_DEVICE_BUSY
            data['data'].append(child)
            data['class']="Devices"
        elif isinstance(child,Event):
            data['data'].append(dict(value=DEVICES_TREE[child.config['Identifierid']].config['value'],id=child.config['Identifierid']))
        elif isinstance(child,Identifier):
            data['data'].append(dict(value=child.config['value'],id=child.config['id']))
        elif isinstance(child,list):
            data['data']=child
        elif isinstance(child,object):
            data['data'].append(child)

        topic=msg.FG['TP_PARAM_POST'].replace('_reply','')
        self.io.write(self.topicHead+topic,data)

    def loop(self):
        self.online=False
        for child in self.search(Identifier,None):
            if child.config['enable'] and self.num%child.config['interval']==0:
                child.loop()
        for child in self.search(Task,None)+self.search(Event,None):
            if child.config['enable']:
                child.loop()
        if self.lastonline!=self.online:
            DEVICES_TREE[msg.FG['deviceid']].post(dict(
                id=self.config['id'],
                key="online",
                value=self.online
            ))
            self.lastonline=self.online
        self.num=(self.num+1)%100000
    def deviceWrite(self,kwarg):
        DEVICES_TREE[self.config['interface']].write(self,kwarg)
    def deviceRead(self,kwarg):
        if DEVICES_TREE[self.config['interface']].read(self,kwarg) is not None:
            self.online=True
    def writeidentity(self,id,value):
        for taskaim in self._search(Identifier,id):
            taskaim.config['value']=value
            #function.log('writeiden',taskaim.config)
            self.deviceWrite(taskaim.config)
            return dict(id=taskaim.config['id'],value=taskaim.config['value'])
    def readidentity(self,id):
        for taskaim in self._search(Identifier,id):
            #function.log('writeiden',taskaim.config)
            self.deviceRead(taskaim.config)
            return dict(id=taskaim.config['id'],value=taskaim.config['value'])
    def read(self,cls,id,**kwargs):
        if cls==Shell:
            return Shell.run(id,**kwargs)
        return self.readidentity(id)
    def write(self,cls,id,value,**kwargs):
        if cls==Download:
            return Download(id).write(value,**kwargs)
        return self.writeidentity(id,value)
    @property
    def topicHead(self):
        p=self
        ids=[]
        while p:
            ids.append(p.config['id'])
            p=p.parent
        ids.reverse()
        return '/sys/'+self.projectKey+'/'+self.config['id']#"_".join(ids)
    def dump(self):
        rt=Base.dump(self)
        if self.parent is None:
            #rt['interfaces']=Device.interfaces.dump()
            rt['ver']=msg.VER
        return rt

for cls in Base.__subclasses__():
    Base.clsMap[cls.__name__]=cls
for key in ['DO','DI','AO','AI']:
    Base.clsMap[key]=Identifier
Base.clsMap['Devices']=Base.clsMap['Terminal']=Device
Base.clsMap['Tasks']=Task
Base.clsMap['Alarms']=Event
Base.clsMap['Props']=Identifier
Base.clsMap['CAN']=Base.clsMap['485']=Base.clsMap['232']=Base.clsMap['NET']=Interface