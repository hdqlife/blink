# coding=utf-8
import json as _json
import hashlib
import time
import os
import re
import sys
import requests
import socket
try:
    import _thread
except Exception as e:
    import thread as _thread
import uuid
import shutil
class FileConfig:
    def __init__(self,path,value=None,default_value=lambda :0):
        self.path=path or os.getcwd()+'/config.config'
        self.value=value or {}
        self.default_value=default_value
        try:
            self.load()
        except:
            self.save(self.value)

    def load(self):
        with open(self.path,'r') as f:
            m = json.loads(f.read())
            self.value.update(m)
    def save(self,s):
        self.value.update(s)
        with open(self.path,'w') as f:
            f.write(json.dumps(self.value))

    def __getitem__(self, item):
        return self.value.get(item,self.default_value())
    def __setitem__(self, key, value):
        self.value[key]=value
        self.save(self.value)


class FileConfig2:
    def __init__(self,path,value):
        self.path=path
        self.value=json.loads(json.dumps(value))
        try:
            self.load()
        except:
            self.save()

    def load(self):
        with open(self.path,'r') as f:
            m = json.loads(f.read())
            self.value.update(m)
    def save(self):
        with open(self.path,'w') as f:
            f.write(json.dumps(self.value,indent=4))

    def __getitem__(self, item):
        return self.value.get(item,None)
    def __setitem__(self, key, value):
        oldvalue=self.value.get(key)
        if oldvalue is not None and value!=oldvalue:
            self.value[key]=value
            self.save()
    def update(self,value):
        self.value.update(value)
        self.save()
UID_HELP={}    
def uid(s):
    if s in UID_HELP:
        UID_HELP[s]+=1
    else:
        UID_HELP[s]=0
    return s+'_'+str(UID_HELP[s])
def copy(s,**kwargs):
    a=json.loads(json.dumps(s))
    a.update(kwargs)
    return a

def log(*args):
    print(args)

def rmDir(path):
    shutil.rmtree(path)

def crc16(x,head=None):
    a = 0xFFFF
    b = 0xA001
    for byte in x:
        a ^= byte
        for i in range(8):
            last = a % 2
            a >>= 1
            if last == 1:
                a ^= b
    if head=='int':
        return a
    elif head=='add_tail':
        return  x+bytearray([a&0xff,(a>>8)&0xff])
    elif head=='add_head':
        return  bytearray([a&0xff,(a>>8)&0xff])+x
    else:
        return [a&0xff,(a>>8)&0xff]
def UUID():
    return str(uuid.uuid1()).split('-').pop()

def intToBytes(value,mode="big",num=1):
    if value==0:
        data=[0]
    else:
        if isinstance(value,int):
            value="%x"%value
        if len(value)%2==1:
            value='0'+value
        data=[int(value[i-2:i],16) for i in range(2,len(value)+1,2)]
        if mode=='small':
            data.reverse()
    num=num-len(data)
    if num>0:
        data=[0]*num+data
    return data      
def bytesToint(value,mode="big"):
    r=range(0,len(value)) if mode=='big' else range(len(value)-1,-1,-1)
    rt=0
    for i in r:
        rt=(rt<<8)+value[i]
    return rt

def dumps(v):
    if isinstance(v, (int, float, dict, str)):
        return v
    elif isinstance(v, MyJson):
        return v.json_loads()
    elif isinstance(v, bytes):
        return str(v)
    elif isinstance(v, list):
        return [dumps(d) for d in v]
    elif getattr(v,'_sa_instance_state',None):
        rt={}
        rt.update(v._sa_instance_state.dict)
        rt.pop('_sa_instance_state')
        return rt
    elif getattr(v,'_fields',None):
        return  dict(zip(v._fields, v))
    elif v.__class__.__name__=='Decimal':
        return float(v)
    else:
        return None

def average(data,f=None):
    num=len(data)
    v=0
    for d in data:
        if f:
            v+=f(d)
        else:
            v+=d
    if num:
        v=v/num
    return v 
class json:
    @staticmethod
    def loads(s,*args,**kwargs):
        if isinstance(s,bytes):
            s=s.decode('utf-8')
        return _json.loads(s,*args,**kwargs)

    @staticmethod
    def dumps(args,**kwargs):
        return _json.dumps(args,ensure_ascii=False,default=dumps,**kwargs)
def udpsendmsg(port,read):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(('0.0.0.0',port))
    def r():
        while True:
            data,addr=s.recvfrom(2048)
            rt=read(data)
            if rt:
                s.sendto(rt,addr)
    _thread.start_new_thread(r,())

class UdpClient:
    def __init__(self,addr,read):
        self.addr=addr
        self.read=read
        self.socket=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    def write(self,data):
        try:
            self.socket.send(data)
            return True
        except Exception as e:
            print('udp send error',e)
            return False
    def server_forever(self):
        while True:
            try:
                self.socket.connect(self.addr)
                data=self.socket.recv(2048)
            except Exception as e:
                print('udpread error',e)
                data=None
            if data:
                try:
                    rt=self.read(data)
                except Exception as e:
                    print('udpdata error',e,data)
                    rt=None
                if rt:
                    self.write(rt)        
def bytedumps(array):
    data=bytearray([len(array)])
    for d in array:
        if isinstance(d,int):
            tp,v=0,intToBytes(d)
        elif isinstance(d,float):
            tp,v=1,str(d).encode('utf-8')
        elif isinstance(d,str):
            tp,v=2,d.encode('utf-8')
        elif isinstance(d,(dict,list)):
            tp,v=3,json.dumps(d).encode('utf-8')
        elif isinstance(d,bytes):
            tp,v=4,d
        a,b=len(v)>>8,len(v)&0xff
        data=data+bytearray([tp,a&0xff,b&0xff])+v
    return bytearray(crc16(data,'add_head'))

BYTE_PARSE=[
    lambda a:bytesToint(a),
    lambda a:float(a.decode('utf-8')),
    lambda a:a.decode('utf-8'),
    lambda a:json.loads(a.decode('utf-8')),
    lambda a:a,
]
def byteloads(data):
    if isinstance(data,str):
        data=bytearray([ord(d) for d in data])
    crc=data[0:2]
    arglength=data[2]
    crc_value=crc16(data[2:])
    rt=[]
    if crc[0]==crc_value[0] and crc[1]==crc_value[1]:
        index=3
        while index<len(data) and arglength>0:
            tp,vl=data[index],(data[index+1]<<8)+data[index+2]
            rt.append(BYTE_PARSE[tp](data[index+3:index+3+vl]))
            index=index+3+vl
            arglength-=1
    return rt

def parseFloat(v):
    if isinstance(v, str):
        rt = 0
        num=1
        chuValue=1
        for d in v:
            if '0'<=d <= '9':
                rt=rt*10+int(d)
                chuValue*=num
            elif d=='.':
                num=10
            else:
                return rt
    else:
        return v
def parseInt(v):
    if isinstance(v, str):
        rt = 0
        for d in v:
            if '0'<=d <= '9':
                rt=rt*10+int(d)
            else:
                return rt
    else:
        return v

def networkInfo(name):
    data=os.popen('ifconfig -a %s'%name).read()
    rt=dict(HWaddr="",addr="0.0.0.0",Bcast="",Mask="")
    try:
        with open('/etc/wpa_supplicant.conf','r') as f:
            s=f.read().split('"')
            rt["wifiName"]=s[1]
            rt["wifiPassword"]=s[3]
    except Exception as e:
        print('file not exist /etc/wpa_supplicant.conf')
    if not data:
        return rt
    for key in [' HWaddr',' addr',' Bcast',' Mask']:
        s=data.find(key)
        if s!=-1:
            s+=len(key)+1
            s1=data[s:].find(' ')
            if s1!=-1:
                rt[key[1:]]=data[s:s+s1].replace('\n','')

    print('newworkInfo',rt)
    return rt

def nowTs(n=0,tp=None):
    s=time.time()+n*60
    a=datetime.fromtimestamp(s)
    if tp=='time':
        a=a.strftime('%H:%M:%S')
    elif tp=='datatime':
        a=a.strftime('%Y.%m.%d-%H:%M:%S')
    elif tp=='date':
         a=a.strftime('%Y-%m-%d %H:%M:%S')
    else:
        a=str(a)
    return a
class Pid():
    def __init__(self,v):
        self.p=v.get('p',0)
        self.i=v.get('i',0)
        self.d=v.get('d',0)
        self.setSpeed=0
        self.actualSpeed=0
        self.err=0
        self.errLast=0
        self.integral=0
        self.voltage=0
        self.percent=0
    def run(self,speed,aim):
        if self.setSpeed!=0:
            self.percent=(speed-self.setSpeed)/self.setSpeed
        self.setSpeed=speed
        self.actualSpeed=aim
        self.err=self.setSpeed-self.actualSpeed
        self.integral+=self.err
        self.voltage=self.p*self.err+self.i*self.integral+self.d*(self.err-self.errLast)
        self.errLast=self.err
        self.actualSpeed=self.voltage
        #self.debugLog()
        return min(max(self.actualSpeed,0),10000)
    def setPid(self,v):
        self.p=v['pid_p']
        self.i=v['pid_i']
        self.d=v['pid_d']
    def debugLog(self):
        s=""
        for key in dir(self):
            v=getattr(self,key)
            if isinstance(v,(int,float)):
                s+='%s:%s '%(key,v)
        print(s)
from datetime import datetime
class ReWrite:
    def __init__(self):
        self.stdwrite=sys.stdout
        sys.stderr = self
        sys.stdout = self
        self.lastfilename=None
        self.f=None
    def write(self,*args):    
        try:
            self.stdwrite.write(*args)
            if 'log' in sys.argv:
                self.log(*args)
        except Exception as e:
            self.log(*args)
    def flush(self):
        pass
    def log(self,*args):
        if args[0]=='\n' or args[0]=='\r\n' or args[0]==' ':return
        nows=str(datetime.now()).split(' ')
        filename='test/log/'+nows[0]+'.txt'
        if filename!=self.lastfilename:
            self.lastfilename=filename
            if self.f:
                self.f.close()
            self.f=open(filename,'w')
        s="%s->"%(nows[1])
        for arg in args:
            s+=' '+str(arg)
        s+='\n'    
        self.f.write(s)
        self.f.flush()

REWRITE=ReWrite()
class MyJson:
    _json = True
    def __init__(self, **kwargs):
        self.update(kwargs)
    @staticmethod
    def loads(s):
        return MyJson(**json.loads(s))
    def __setitem__(self, key, value):
        setattr(self,key,value)
    def __getitem__(self, item):
        return getattr(self,item,None)
    def update(self, data,autoInsert=True):
        if isinstance(data, MyJson):
            data = data.json_loads()
        for key in data:
            if autoInsert or getattr(self,key,None) is not None:
                setattr(self, key, data[key])

    def json_loads(self, passkey='_'):
        rt = {}

        for d in dir(self):
            if d[0] == passkey:
                continue

            f = dumps(getattr(self, d))
            if f is not None:
                rt[d] = f

        return rt

    def json_dumps(self, filter_key='_', pass_key=None,**kwargs):
        if pass_key is None:
            pass_key = []
        rt = self.json_loads(filter_key)
        for p in pass_key:
            if p in rt:
                del rt[p]
        return json.dumps(rt)



def int_to_hex(n, size=2):
    rt = []
    while size >= 0:
        rt.append(n & 0xff)
        n >>= 8
        size -= 1
    return bytearray(rt)

def re_match(rs, ds):
    if isinstance(rs, str):
        rs = re.compile(rs)
        rt = rs.match(ds)
    else:
        rt = rs.match(ds)
    if rt is None:
        return False, (ds,)
    else:
        return True, rt.groups()


def console_error(lever, s):
    if lever == 0:
        sys.stderr.write(now_str() + s)


def url_parse(s):
    from urllib import parse
    rt = {}
    url_data = parse.unquote(s)
    for f in url_data.split('&'):
        fs = f.split('=')
        if len(fs) >= 2:
            rt[fs[0]] = fs[1]
    return rt


def url_to_dict(url):
    path = url.split('?')
    rt = {}
    if len(path) >= 2:
        rt = url_parse(path[1])
    return path[0], rt


def console_print(*args,**kwargs):
    try:
        print(now_str(), args,kwargs)
    except:
        pass

def get_cpu_id():
    s=os.popen('wmic cpu get ProcessorId').read().split('\n\n')
    return s[1].split(' ')[0]

def get_host_ip():
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception as e:
        print('get ip error', e)
        return '127.0.0.1'

def md5(f):
    m2 = hashlib.md5()
    if isinstance(f,str):
        f = f.encode("utf8")
    m2.update(f)
    return m2.hexdigest()

def md5File(name):
    if os.path.exists(name):
        with open(name,'rb') as f:
            return md5(f.read())
    return ''


def get_main_path():
    return os.getcwd()


def nowt():
    return time.time()


def now_str(time_stamp=-1, formats="%m-%d %H:%M:%S"):
    if time_stamp == -1:
        time_stamp = nowt()
    return time.strftime(formats, time.localtime(time_stamp))


def read_file(s, decode=None):
    if s[0:4]=='http':
        data=requests.get(s).content
    else:
        try:
            with open(s,'rb') as f:
                data = f.read()
        except Exception as e:
            data=b'not found'
    if decode:
        data = data.decode(decode)
    return data
def writeFile(path,data):
    paths=path.split('/')
    paths.pop()
    pathDir=""
    for d in paths:
        if d:
            pathDir+=d
            if not os.path.isdir(pathDir):
                os.mkdir(pathDir)
            pathDir+='/'
    with open(path,'wb') as f:
        if isinstance(data,str):
            data=data.encode('utf-8')
        f.write(data)


def get_paths_dir(path):
    class MyFiles(MyJson):
        paths = []
        root_dir = ""

    rt = MyFiles(root_dir=path)
    if os.path.isfile(path):
        return path
    elif os.path.isdir(path):
        for root, dirs, files in os.walk(path):
            rt.paths.extend([root + '/' + k for k in dirs])
            rt.paths.extend([root + '/' + k for k in files])
        return rt
    else:
        return rt

class Ob:

    def __init__(self):
        self.task_list = {}

    def subscribe(self, msg_name, back, n=-1):
        if msg_name not in self.task_list:
            self.task_list[msg_name] = [[back, n]]
        else:
            self.task_list[msg_name].append([back, n])

    def publish(self, msg_name, *args, **kwargs):
        calls = self.task_list.get(msg_name, [])
        n = len(calls) - 1
        while n >= 0:
            f, num = calls[n]
            if num != 0:
                if f(*args, **kwargs):
                    calls.pop()
                else:
                    calls[n][1] -= 1
            else:
                calls.pop()
            n -= 1

OB = Ob()




def get_value_from_xml_keys(s, head_str, tail_str):
    begin = end = 0
    sb = ""
    se = ""
    for head_s in head_str:
        begin = s.find(head_s)
        if begin != -1:
            begin += len(head_s)
            sb = head_s
            break
    for tail_s in tail_str:
        end = s.find(tail_s)
        if end != -1:
            se = tail_s
            break
    return s[begin:end], sb, se

class BaseServer:
    proto=None
    cons=None
    def __init__(self):
        pass
    def stop(self):
        pass

def make_many_json(b, a):
    rt = []
    for c in b:
        rs = {}
        for i in range(len(c)):
            rs[a[i]] = c[i]
        rt.append(rs)
    return rt

def array_to_dict(array,key):
    rt={}
    for a in array:
        try:
            rt[a[key]]=a
        except NotImplementedError:
            rt[a.__getattribute__(key)]=a
    return rt
def list_remove(a,*args):
    for b in args:
        if b in a:
            a.remove(b)
def del_files(aim_dir,head='/',aim_type=None,filter_dir=None,rt=None):
    rt=rt or []
    for dir_head in os.listdir(aim_dir):
        path=head+dir_head
        if filter_dir and path in filter_dir:
            continue
        path=aim_dir+'/'+dir_head
        if os.path.isdir(path):
            rt=del_files(path,head+dir_head+'/',aim_type,filter_dir,rt)
        else:
            if path.split('.').pop() in aim_type:
                rt.append(path)
    return rt

def copy(f,a=None):
    rt=json.loads(json.dumps(f))
    if a:
        rt.update(a)
    return rt
def read_dir_last_file(path):
    s=get_paths_dir(path)
    rs=list(map(lambda d:[d,os.path.getmtime(d)],s.paths))
    rs.sort(key=lambda b:b[1])
    return open(rs.pop()[0],'rb').read()

def watchDir(path,callback):
    from watchdog.observers import Observer
    from watchdog.events import LoggingEventHandler
    ob=Observer()
    ob.schedule(MyJson(dispatch=callback),path,recursive=True)
    ob.start()

def filesCopy(src,dst):
    import shutil
    shutil.rmtree(src)
    os.mkdir(src)
    for d in dst:
        pathDir=src+'/'+d
        # paths=d.split('/')
        # pathDir=src
        # for p in paths:
        #     pathDir=pathDir+'/'+p
        #     if not os.path.isdir(pathDir):
        #         os.mkdir(pathDir)
        shutil.copytree(d,pathDir)
        
if __name__ == "__main__":
    # OB.subscribe('f', None, n=2)
    # OB.publish('f', 3)
    # OB.publish('f', 2)
    # OB.publish('f', 1)
    # print(url_to_dict('login?a=cf=b'))
    # input('exit')
    if 'crc' in sys.argv:
        data=[int(d) for d in sys.argv[2:]]
        print('crc',data+crc16(data))
