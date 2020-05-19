from app.dy.model import db,dy_device
from app.dy.models.env import Env2V,Env
from app.dy.message import get_f,PARAM
from app.dy.models.model11 import yd,wd
from app.dy.calc import Calc
from .util import DyBase,Relation,gj,XhPrepare
from common.function import copy
DEVICE_VER = "DT_%s_V1.5"
class Error(XhPrepare):
    ErrorStatu=['','AB切换故障']
    ErrorIndex=0
    def __init__(self):
        self.children=[XhPrepare(),gj()]
        self.relation=Relation([
            [0,1,'min([min(d) for d in select_v])<gj_min_v']
        ])
        XhPrepare.__init__(self)
    def hasError(self):
        if self.env.dji.value!=self.env.dji.last_value:
            self.ErrorIndex=1
        else:
            self.ErrorIndex=0
        return self.ErrorIndex!=0
    def s_name(self):
        return XhPrepare.s_name(self)+'_'+self.ErrorStatu[self.ErrorIndex]
class Base(DyBase):
    def __init__(self,tp,**kwargs):
        self.name=DEVICE_VER%tp
        self.children=[wd(),yd(),Error()]
        self.relation=Relation([
            [0,[2,1],['after.hasError()','i1[2]>yd_wd_i1 and agz==0 and bgz==0']],
            [1,[2,0],['after.hasError()','i1[2]<yd_wd_i1']],
            [2,[0,1],['not pre.hasError() and self.last_statu==0','not pre.hasError() and self.last_statu==1']]
        ])
        DyBase.__init__(self,**kwargs)
    def get_info(self):
        run=[d.key for d in self.get_run()]
        rt=dict(
            run=run,
            names=self.getState(lambda f:f.s_name()),
            state=self.get_state()
        )
        self.lastRun = run
        return rt
    def s_name(self):
        return self.name

import pickle
import time
class Dy:
    def __init__(self,tp,id):
        self.tp=tp
        self.env=DyBase.env=Env(tp,id) if tp in [10,11] else Env2V(tp,id)
        self.last_data=PARAM(self.env)
        
        #self.root=self.env._root
        self.root=Base(tp)
        self.env._root=self.root
        self.root.set_env(self.env)
        self.env.load(**self.last_data)
        #self.root.run()
        #self.root.test()
        self.calc = Calc(self)
    def run(self,kwargs):
        self.last_data=kwargs
        self.last_data['t']=time.time()
        self.env.load(**kwargs)
        self.root.run()
        info=self.root.get_info()
        kwargs.update(info)
        self.calc.run(kwargs)
    def dump(self):
        return self.root.dump()
    def dumps(self):
        #pickle.dumps(self)
        return dict(
            env=self.env.json_dumps(),
            root=self.root.json_dumps(),
            last_data=self.last_data
        )
    def loads(self,data):
        self.last_data=data['last_data']
        self.env.json_loads(data['last_data'])
        self.root.json_loads(data['root'])
    def out(self):
        return self.env.dump()
    def out_info(self):
        return {}
class DyDevices:
    def __init__(self):
        self.map={}
    def __getitem__(self,key):
        return self.map[key]
    def __setitem__(self,key,value):
        self.map[key]=value
def load_all_device():
    rt={}
    session=db.session()
    for device in session.query(dy_device).all():
        if device.jb:
            rt[device.nb_id]=Dy(device.type,device.nb_id)
            if (DEVICE_VER%device.type)!=rt[device.nb_id].root.name:
                rt[device.nb_id]=Dy(device.type,device.nb_id)
            else:
                rt[device.nb_id] = pickle.loads(device.jb)
        else:
            rt[device.nb_id]=Dy(device.type,device.nb_id)
    for key in [10,20,21,11]:
        rt['stand'+str(key)]=Dy(key,'stand'+str(key))
    session.close()
    return rt
if __name__=="__main__":
    a=Dy(20,'test')
    Dy.loads(Dy.dumps())