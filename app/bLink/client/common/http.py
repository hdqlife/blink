import json
from . import msg
from common import function
import os
from http.server import HTTPServer,BaseHTTPRequestHandler
HTTP_S='''HTTP/1.1 200 OK
Server: nginx
Date: Mon, 20 Feb 2017 09:13:59 GMT
Content-Type: text/html;charset=UTF-8
Vary: Accept-Encoding
Connection: Keep-Alive
Cache-Control: no-store
Pragrma: no-cache
Expires: Thu, 01 Jan 1970 00:00:00 GMT
Cache-Control: no-cache
Content-Length:%s

%s'''

class MYHTTPServer(HTTPServer):
    allow_reuse_address = 0 
class MyHttpHander(BaseHTTPRequestHandler):
    def do_GET(self):       
        function.log(self.path)
        paths=self.path.split('?')
        path=None
        if len(paths)>=2:
            inp={}
            path,paramStr=paths
            rt=dict(statu=0,msg="",data={},array=[])
            paramStr=paramStr.replace('\\&','(').replace('\\=',')')
            for keyValue in paramStr.split('&'):
                pm=keyValue.split('=')
                if len(pm)==2:
                    inp[pm[0]]=pm[1].replace('(','&').replace(')','=')
            function.log('input',inp,paths[0],paramStr)
            if inp.get('account',None)!=msg.FG['account'] or inp.get('password',None)!=msg.FG['password']:
                rt['msg']="用户名或者密码错误"
                rt["statu"]=-1
            elif path=='/login':
                rt["statu"]=0
            elif path in ['/savePf','/saveMqtt','/saveNet','/saveUser','/recover','/restart']:
                if inp.get('method',None)=='get':
                    if path=='/saveNet':
                        data=function.networkInfo(inp.get('name',msg.FG["localcom"]))
                        msg.FG.update(dict(
                            localcom=inp.get('name',msg.FG["localcom"]),
                            mac=data['HWaddr'],localip=data.get('addr',''),
                            netmask=data.get("Mask",''),gateway=data.get('Bcast','')))
                        for key in data:
                            msg.FG[key]=data[key]
                    for name in inp['names'].split(','):
                        rt['array'].append(msg.FG[name])
                elif inp.get('method',None)=='save':
                    rt['msg']="设置成功"
                    if path=='/saveUser':
                        if inp['newpassword1']!=inp['newpassword2']:
                            rt['msg']="两次输入密码不相同"
                        elif inp['password']!=msg.FG['password']:
                            rt['msg']='请确认原密码是否正确'
                        else:
                            msg.FG['password']=inp['password']
                    elif path=='/saveNet':
                        if inp['localcom']=='eth0':
                            with open('/etc/network/interfaces','w') as f:
                                f.write(msg.SET_NETIP%(inp['localip'],inp['netmask']))
                        wifi=msg.WIFISET%(inp['wifiName'],inp['wifiPassword'])
                        print('set wifi %s'%wifi)
                        with open('/etc/wpa_supplicant.conf','w') as f:
                            f.write(wifi)
                    elif path=='/recover':
                        msg.FG.update(msg.DEFAULT_PARAM)
                    elif path=='/restart':
                        os.system('reboot')
                    else:
                        for key in inp:
                            msg.FG[key]=inp[key]
            rs=json.dumps(rt).encode('utf_8')
            function.log('out',rs)
        else:
            with open('app/bLink/client/html/index.html','rb') as f:
                rs=f.read()
        sends=(HTTP_S%(len(rs),rs.decode('utf-8'))).encode('utf-8')
        self.wfile.write(sends)

def initHttp():
    print('http run',8090)
    server=MYHTTPServer(('0.0.0.0',8090),MyHttpHander)
    server.serve_forever()