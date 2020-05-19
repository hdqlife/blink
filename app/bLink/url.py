from common.proto import BaseWeb
from common.function import json,MyJson
from common import web
from app.apiUtil.client import api
from imp import reload
import inspect
class CallUtil():
    def __init__(self,f):
        self.call=f
        self.name=f.__name__
        self.param={}
        self.doc=f.__doc__ or ''
        for i in range(f.__code__.co_argcount):
            self.param[f.__code__.co_varnames[i]]=f.__defaults__[i]
    def run(self,**kwargs):
        return self.call(**kwargs)
    def dump(self):
        return dict(name=self.name,param=self.param,doc=self.doc)
def load(s):
    rt=[]
    for k in dir(s):
        f=getattr(s,k)
        if inspect.isfunction(f):
            rt.append(CallUtil(f))
    return rt
class Index(BaseWeb):
    def get(self,*args):
        Api=load(reload(api))
        for d in Api:
            self.rt.array.append(d.dump())
        return self.rt.json_dumps()
    def post(self,**kwargs):
        return self.rt.json_dumps()
import _thread
import time
from paho.mqtt.client import Client
from collections import defaultdict
class MqttConnect(BaseWeb):
    mqtt=None
    ip=None
    G=defaultdict(str)
    def __init__(self,*args,**kwargs):
        if len(args)==0:
            self.topics=None
            self.callback=None
            BaseWeb.__init__(self,*args,**kwargs)
        else:
            self.topics=args[0]
            self.callback=args[1]
            self.rt=MyJson(msg="")
    def on_log(self,*args):
        if args[2]==8:
            print('mqtt_log',*args)
    def on_connect(self,client,userdata, flags, rc):
        if rc==0:
            self.rt.msg="连接成功"
            if self.topics is None:
                MqttConnect.mqtt.subscribe('/#')
            else:
                for tp in self.topics:
                    MqttConnect.mqtt.subscribe(tp)
            print('mqtt connect sucess')
        else:
            print('mqtt connect error')
    def on_message(self,client,userdata,msg):
        #print('recv not json',msg.payload,self.callback)
        try:
            c=json.loads(msg.payload)
            if '_replay' in msg.topic:
                MqttConnect.G[c['id']]=json.dumps(c,indent=4)
        except Exception as e:
            print('recv not json',e,msg.payload)
        if self.callback:
            self.callback(msg.topic,msg.payload)
        else:
            web.clients.send('bLinkHelp',dict(
                id=msg.topic,
                t=time.time(),
                i=msg.payload,
                o=''
            ))
    def loop(self,ip,port,clientId='',username='',
        password='',**kwargs):
        if MqttConnect.mqtt:
            MqttConnect.mqtt.loop_stop()
        mqtt=Client(clientId)
        mqtt.username_pw_set(username,password)
        mqtt.connect(ip,int(port))
        mqtt.on_log=self.on_log
        mqtt.on_connect=self.on_connect
        mqtt.on_message=self.on_message
        mqtt.loop_start()
        MqttConnect.mqtt=mqtt
    def post(self,ip,port,**kwargs):
        if MqttConnect.ip!=ip:
            self.rt.msg='连接失败'
            self.loop(ip,port,**kwargs)
            time.sleep(1)
        MqttConnect.ip=ip
        return self.rt.json_dumps()
    def get(self,*args):
        self.rt.array=[dict(name=self.input['v'])]
        return self.rt.json_dumps()
class Send(BaseWeb):
    ID=0
    def get(self,*args):
        from imp import reload
        from app.bLink.client.common import device,msg
        if self.input['method']=='topics':
            self.rt.array=msg.TPOICS
        elif self.input['method']=='type':
            self.rt.array=['add','update','delete','upload','query','search']
        elif self.input['method']=='cls':
            for key in dir(msg):
                if key[0:5]=='CLASS':
                    keys="".join(map(lambda p: p[0:1]+p[1:].lower(),key.split('_')))
                    self.rt['array'].append(keys.replace('Class',''))
        elif self.input['method']=='data':
            newcls=""
            for v in self.input['cls']:
                if ord(v)<=ord('Z') and ord(v)>=ord('A'):
                    newcls+='_'+v
                else:
                    newcls+=v
            self.rt.data=getattr(msg,'CLASS'+newcls.upper(),{})
        elif self.input['method']=='class':
            try:
                device=reload(device)
                for s in device.Base.__subclasses__():
                    p=getattr(s,'p',None)
                    if p:
                        self.rt.data[s.__name__]=p()
            except Exception as e:
                self.rt.data=dict(error=str(e))
        return self.rt.json_dumps()
    def post(self,topic,data,wait=0,**kwargs):
        if MqttConnect.mqtt is None:
            self.rt.msg="请先连接服务器" 
        else:
            rs=''
            for d in data:
                if ord(d) in [0xa0,0xc2] or ord(d)>128:
                    continue
                rs+=d
            Send.ID=(Send.ID%1000000000+1)
            data=rs
            try:
                data=json.loads(data)
            except Exception as e:
                self.rt.data="error json:"+data
                return self.rt.json_dumps()
            if wait:
                data['id']=str(Send.ID)
            MqttConnect.mqtt.publish(topic,payload=json.dumps(data))
            self.rt.msg='发送成功'
            self.rt.data='{}'
            MqttConnect.G[data['id']]=""
            while wait>0:
                if MqttConnect.G[data['id']]:
                    self.rt.data=MqttConnect.G[data['id']]
                    break
                wait-=0.1
                time.sleep(0.1)
        return self.rt.json_dumps()