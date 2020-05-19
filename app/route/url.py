from common.proto import BaseWeb,BaseWebAttr,URL_RECORD_CONFIG,ConnectConfig,select_field
from common.model import tb_log,tb_task,tb_config
from common.function import read_file,writeFile,MyJson,json,watchDir
from common import function
from common.tm import Tm,time
from common import web
import os
import requests
from tool.image import Api
import time
class Img(BaseWeb):
    def get(self,name):
        img=Api.get(name)()
        img.run(**self.input)
        return img.dumps()
    def post(self,name):
        return self.rt.json_dumps()

class Upload(BaseWeb):
    param = dict(name='tmp',f_file='',type=select_field(["file","image"]))
    logShow=False
    def post(self,name,f_file,type,**kwargs):
        if type=="image":
            name=str(time.time())+name
        print(name,len(f_file),type)
        path='app/static/upload/'+name
        with open(path,'wb') as f:
            if isinstance(f_file,str):
                f_file=f_file.encode('utf_8')
            f.write(f_file)
        self.rt.msg=path
        return self.rt.json_dumps()
class DbSave(BaseWeb):
    param=dict(key='',value='')
    def get(self):
        self.rt.data=self.session.query(tb_config).filter(
            tb_config.type==self.input.get('key',None),
            tb_config.type=='dbSave',
        ).one_or_none()
        return self.rt.json_dumps()
    def post(self,key,value):
        query=self.session.query(tb_config).filter(
            tb_config.type == key,
            tb_config.type == 'dbSave',
        ).one_or_none()
        if query is None:
            self.session.add(tb_config(type="dbSave",name=key,value=value))
        else:
            query.value=value
        return self.rt.json_dumps()

class Log(BaseWeb):
    param = dict(name='',data='')
    def get(self):
        query=self.session.query(tb_log).filter(
            tb_log.t < self.input['et'],
            tb_log.t > self.input['bt']
        )
        if 'url' in self.input:
            self.rt.array=query.filter(tb_log.url == self.input['url']).order_by(tb_log.t.desc()).all()
        elif 'device_id' in self.input:
            self.rt.array = query.filter(tb_log.userid == self.input['device_id']).order_by(tb_log.t.desc()).all()
        return self.rt.json_dumps()

class UrlConfig(BaseWeb):
    param = dict(path='',login=False,record=False,show=False)
    def get(self,*args,**kwargs):
        if self.input.get('path','')=='':
            self.rt.data = web.config.app.dumps_api_json()
        elif self.input.get('path','')=='all':
            self.rt.data=URL_RECORD_CONFIG.value
        else:
            self.rt.data = URL_RECORD_CONFIG[self.input['path']]
        return self.rt.json_dumps()
    def post(self,path,record,login,show,**kwargs):
        self.rt.data=URL_RECORD_CONFIG[path]=dict(login=login,record=record,show=show)
        return self.rt.json_dumps()
class ConnectManage(BaseWeb):
    param = dict(id_name='',method=['send'],param='')
    def get(self):
        method=self.input.get('method',None)
        if method is None:
            self.rt.array = [c.id for c in web.clients.c]
            self.rt.array.append('errorData')
        elif method=='get_config':
            if self.input['id_name']=='all':
                self.rt.data=ConnectConfig.value
            else:
                self.rt.data=ConnectConfig[self.input['id_name']]
        return self.rt.json_dumps()
    def post(self,id_name,method,param,timeout=0,**kwargs):
        if method=='send':
            if id_name[0:5]=='lora/':
                from app.loratc.proto import LoaPro
                LoaPro.sendData=param
            self.rt.msg=web.clients.send(id_name,param)
            if timeout:
                oldT=time.time()
                time.sleep(timeout)
                self.rt.array=self.session.query(tb_log).filter(
                    tb_log.t>oldT,
                    tb_log.userid==id_name
                ).order_by(tb_log.t.desc()).limit(3).all()
                print(self.rt.array)
        if method=='set_config':
            ConnectConfig[id_name]=param
        return self.rt.json_dumps()

class Index(BaseWeb):
    def get(self,*args,**kwargs):
        print('get',self.path[1:])
        data=read_file(self.path[1:])
        if '.py' in self.path:
            if self.input.get('user')!='yly':
                data=b'who are you'    
        if '.css' in self.path:
            web.header('content-type','text/css')
        return data
    def post(self,*args,**kwargs):
        self.rt.statu=404
        return self.rt.json_dumps()
from common.db import MyDb
from app.route.model import test_config
class Sql(BaseWeb):
    param =dict(sql='select 1')
    dbs=None
    def post(self,sql,**kwargs):
        if Sql.dbs is None:
            Sql.dbs=MyDb('mysql+pymysql://root:xykj20160315@119.3.248.55/testdb?charset=utf8')
            Sql.dbs.update(test_config)
        try:
            sql=sql.replace(r'\'',"'").replace(r'\"','"')
            self.rt.msg=sql
            header=sql.split(' ')[0]
            if header=='select':
                self.rt.array=self.dbs.execute(sql)
            else:
                self.rt.statu=self.dbs.execute(sql)
        except Exception as e:
            pass
        return self.rt.json_loads()
class DataCheck(BaseWeb):
    def post(self,value,datatype,**kwargs):
        if value[2:3]==" ":
            try:
                value=[int(d,16) for d in value.split(' ')]
            except Exception as e:
                value=None
                self.rt.msg=str(e)
        else:
            value=[ord(d) for d in value]
        if value:
            if datatype=='crc16':
                crc=function.crc16(value)
                self.rt.msg="%x %x"%(crc[0],crc[1])
            elif datatype=='sum':
                s=sum(value)&0xffff
                self.rt.msg="%x %x"%((s>>8)&0xff,s&0xff)
        return self.rt.json_dumps()
class SaveFile(BaseWeb):
    param = dict(name='tmp', f_file=b'')
    def post(self, name, f_file,**kwargs):
        writeFile(name,f_file)
        self.rt.msg = name
        return self.rt.json_dumps()

class NotFund(BaseWeb):
    def init(self):
        self.rt=MyJson(statu=404,body={},ok=False)

from common.tool.phone import PhoneCache
from common.model import tb_seesion
class SendMsg(BaseWeb):
    param=dict(method=["email","phone","verify"],addr="",code="")
    phoneChache=PhoneCache(tb_seesion().init(BaseWeb.db))
    def post(self,method,addr,code,**kwargs):
        if method!="verify":
            self.rt.data=self.phoneChache.send(addr,method)
        else:
            self.rt.ok=self.phoneChache.verify(addr,code)
            if self.rt.ok:
                self.verifySuccess(self.phoneChache.get(addr))
        return self.rt.json_dumps()
    def verifySuccess(self,addr):
        pass

from common.server import MoutbusClient
class Moutbus(BaseWeb):
    param = dict(method=["init","write"],data=dict(index=0,value=0,command=0))
    com=None
    def post(self,method,data,**kwargs):
        if method=="init":
            if Moutbus.com is None:
                Moutbus.com=MoutbusClient(data)
            else:
                Moutbus.com.device.update(data['ip'],data['port'])
            time.sleep(1.5)
            if Moutbus.com.device.isEnable():
                self.rt.msg="打开成功" 
            else:
                self.rt.msg="打开失败"
        else:
            self.rt.array=Moutbus.com.read(data["command"],data["index"],data["value"],data['addr'])
        return self.rt.json_dumps()
class Node(BaseWeb):
    def get(self,*args):
        p=read_file(self.input['url'][1:],decode='utf-8')
        return p.replace('export default','var %s='%self.input['call'])

from threading import Thread
from common.db import or_,and_
class TimeHelpThread(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.start()
    def run(self):
        if BaseWeb.db is None:
            return
        session=BaseWeb.db.session()
        while True:
            tasks=session.query(tb_task).filter(
                or_(
                    tb_task.statu==-2,
                    and_(
                        tb_task.statu==0,
                        tb_task.runT<time.time()+3,
                        tb_task.runT>time.time()-3
                    )
                )
            ).all()
            for task in tasks:
                try:
                    responce=requests.post(task.url,json=json.loads(task.param),timeout=1.5)
                    task.statu=1
                    task.callBackParam=responce.content
                except Exception as e:
                    task.statu=-1
                    task.callBackParam=json.dumps(dict(error=str(e)))
            session.commit()
            time.sleep(0.5)
class Task(BaseWebAttr):
    taskUtil=TimeHelpThread()
    ip='http://127.0.0.1:8080'
    def add(self):
        if 't' in self.input:
            self.input['runT']=self.input['t']
        self.errOut('任务时间已过期',self.input["runT"]<Tm().time())
        self.session.add(tb_task(
            url=self.ip+self.input["url"],
            param=json.dumps(self.input["param"]),
            runT=self.input["runT"]
        ))
    def list(self):
        self.rt.array=self.session.query(tb_task).all()
    
    def edit(self):
        self.session.query(tb_task).filter(
            tb_task.id==self.input['id'],
        ).update(dict(
            url=self.input["url"],
            param=json.dumps(self.input["param"]),
            runT=self.input["runT"],
            statu=self.input["statu"]
        ))

class FileManage(BaseWeb):
    def get(self,**kwargs):
        if self.input['path']=='':
            self.rt.array=['C:','D:','E:','F:','G:','H:']
        elif os.path.isdir(self.input['path']):
            try:
                self.rt.array=list(os.listdir(self.input['path']))
            except:
                self.rt.array=[]
        return self.rt.json_dumps()
import importlib
from imp import reload
class Py(BaseWeb):
    param=dict(path="",method="",args=[])
    def post(self,path,method,args,**kwargs):
        moudle=importlib.import_module(path)
        moudle=reload(moudle)
        py=getattr(moudle,method,None)
        self.rt.data=py(*args)
        return self.rt.json_dumps()


from common.db import MyDb
class FileWatch(BaseWeb):
    watchPaths={'app/blog/js/tmp.js':0}
    def post(self,watchFiles,**kwargs):
        for filePath in watchFiles:
            FileWatch.watchPaths[filePath]=0
        return self.rt.json_dumps()
    @staticmethod
    def updateFile(a):
        src_path=a.src_path.replace("\\",'/')
        if a.event_type=='modified':
            if time.time()-FileWatch.watchPaths.get(src_path,0)<1.5:return
            FileWatch.watchPaths[src_path]=time.time()
            if 'app/blog/分类/' in src_path:
                from app.blog.model import blog_article
                from app.blog.url import Index
                if os.path.isdir(src_path):return
                data=read_file(src_path,decode='utf-8')
                if data is None:return
                if BaseWeb.db is None:return
                session=BaseWeb.db.session()
                paths=src_path.split('/')[3:]
                paths.append(paths.pop().replace('.js',''))
                node=session.query(blog_article).filter(
                    blog_article.title==paths[0]
                ).one_or_none()
                for path in paths[1:]:
                    print('wact blog path',path)
                    if node is None:return
                    node=session.query(blog_article).filter(
                        blog_article.title==path,
                        blog_article.parentId==node.id
                    ).one_or_none()
                node.content=data
                Index.selectId=node.id
                session.commit()
                try:
                    dbs=MyDb('mysql+pymysql://root:xykj20160315@119.3.248.55/base?charset=utf8')
                    s=dbs.session()
                    vs=s.query(blog_article).filter(
                        blog_article.title==node.title
                    ).one_or_none()
                    if vs is None:
                        s.add(blog_article(title=node.title,content=node.content))
                        print('add',Index.selectId,node.title)
                    else:
                        vs.content=read_file(src_path,decode='utf-8')
                        print(Index.selectId,node.title,vs.content[0:20])
                    s.commit()
                    s.close()
                except Exception as e:
                    print('nee error',e)
                web.clients.send('blog',dict(msg='/'+src_path))
            else:
                web.clients.send('debugWatch',dict(msg='/'+src_path))
watchDir("app",FileWatch.updateFile)