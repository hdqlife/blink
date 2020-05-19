import sys
import os
import platform
import re
import _thread
print('welcom yly_tool 1.5')
import time
def kill(pt):
    if platform.system() == 'Linux':
        s=os.popen('lsof -i:%s | grep LISTEN'%pt).read().split(' ')
        if len(s)>1:
            print('kill',s)
            os.system('kill -9 '+s[1])
        # s = os.popen(killcmd).read()
        # match = re.compile('''python3[\.|\d]{0,2} (\d*)''').search(s)
        # if match:
        #     os.system('kill -9 %s' % match.groups()[0])
        # time.sleep(1.5)
if 'blog'==sys.argv[1]:
    from app.url import app
    from common import web
    command = '''cmd /k "e: & cd E:\Life\js\ele\electron-quick-start\OutApp\myapp-win32-ia32 & myapp.exe http://127.0.0.1:50001/app/static/cwg/index.html?width=1&height=1"'''
    _thread.start_new_thread(app.run,('50001',))
    _thread.start_new_thread(app.run, ('websocket 55000', web.httpserver.StaticMiddleware))
    os.system(command)
elif 'ele_run' == sys.argv[1]:
    pass
elif 'package'==sys.argv[1]:
    from common.windowstool.tool import package_out
    from common.function import filesCopy
    if 'cwg' in sys.argv:
        print(os.getcwd())
        package_out('test.py','app\\\\cwg\\\\all\\\\client\\\\sensehome.exe',show_cmd=True)
    elif 'tsfxy' in sys.argv:
        # filesCopy('test/package',[
        #     'app/tsfxy/release',
        #     'app/route/html',
        #     'app/static/yui',
        #     'app/static/upload/json'
        # ])
        package_out('main.py','main.exe',icon="app/static/favicon.ico",show_cmd=True)
    elif 'blink' in sys.argv:
        from app.bLink.client.common import msg
        cpfile='tar -czvf out/blinK/%s.tar %s'%(msg.VER," ".join(msg.CODE_FILES))
        print('cmd',cpfile)
        os.system(cpfile)
        if not os.path.exists('out/blinK/blink%s'%msg.VER):
            os.mkdir('out/blinK/blink%s'%msg.VER)
        os.system('tar -xzvf out/blinK/blink%s.tar -C out/blinK/%s'%(msg.VER,msg.VER))
        os.chdir('out/blinK/blink%s'%msg.VER)
        os.system('python3 -m app.bLink.client.client')
elif 'web' == sys.argv[1]:
    import _thread
    from common import web
    from common.proto import BaseWeb
    from common.proto import MyDb
    from common.model import Base
    if 'ljfy' in sys.argv:
        BaseWeb.db = MyDb('mysql+pymysql://root:xykj20160315@119.3.248.55/base?charset=utf8')
    else:
        BaseWeb.db = MyDb('mysql+pymysql://root:xykj20160315@127.0.0.1/base?charset=utf8')
    BaseWeb.db.execute('''set @@global.sql_mode=(select replace(@@global.sql_mode,'ONLY_FULL_GROUP_BY',''))''')
    BaseWeb.db.update(Base)
    web.config.debug = False
    if web.config.get('session') is None:
        web.config.session_parameters.cookie_path = '/'
    if 'cwg' in sys.argv:
        from app import cwg,route
        web.config.app=web.application((
            '/app/cwg',cwg.app,
            '/app/route',route.app
        ))
        session = web.session.Session(web.config.app, web.session.DiskStore('test/session'), dict(id=''))
        c=cwg.tool.Mouse()
        cwg.url.connect_db()
        if 'activeAuto' in sys.argv:
            time.sleep(2)
            cwg.url.authorization_update()
        web.config.session = session
        _thread.start_new_thread(web.config.app.run, ('websocket 55000',))
        web.config.app.run('8080')
    elif 'btj' in sys.argv:
        kill(52000)
        from app.btj import app
        session = web.session.Session(app, web.session.DiskStore('test/session'), dict(id=''))
        web.config.session = session
        app.run('52000')
    elif 'fyj' in sys.argv:
        kill(50001)
        from app import fyj
        from app import route
        import _thread
        web.config.app=web.application((
            '/app/fyj',fyj.app,
            '/app/route',route.app
        ))
        from app.fyj import newTcp
        #_thread.start_new_thread(web.config.app.run, ('tcp /FyjPro 58200',))
        _thread.start_new_thread(web.config.app.run, ('websocket 55000', web.httpserver.StaticMiddleware))
        web.config.app.run('50001')
    elif 'dy' in sys.argv:
        kill(8080)
        BaseWeb.db = MyDb('mysql+pymysql://root:xykj20160315@122.112.201.243/base?charset=utf8')
        from app import dy,route
        web.config.app=web.application((
            '/app/dy',dy.app,
            '/upload',dy.url.RemoteUpload,
            '/app/route',route.app,
            '/(.*)',dy.url.Index,
        ))
        if 'debug' in sys.argv:
            username='xykj-yly'
        else:
            username='Low-key'
        def topicmap(msg):
            name= msg.topic.replace('$USR/Dev2App/%s/'%username, '')
            return '$USR/DevRx/' + name
        from common.web import tcpserver
        tcpserver.IGNAMES=topicmap
        if 'mqtt' in sys.argv:
            _thread.start_new_thread(web.config.app.run,('mqtt clouddata.usr.cn /DyPro %s jx201809 APP:%s $USR/Dev2App/%s/+'%(username,username,username),))
        _thread.start_new_thread(dy.api.loop,())
        #_thread.start_new_thread(web.config.app.run, ('tcp /DyPro 5',))
        _thread.start_new_thread(web.config.app.run, ('websocket 65000', web.httpserver.StaticMiddleware))
        web.config.app.run('8080')
    elif 'xykj' in sys.argv:
        kill(55000)
        from app import route
        from app import loratc
        from app import tsfxy
        from app import xykj,apiUtil,bLink,blog
        from common.proto import Upc
        Upc.projectFile['tes']=[
            ["http://127.0.0.1:50001/app/lora/static/lora/rs485","test/static/lora/rs485"],
        ]
        web.config.app=web.application((
            '/app/route',route.app,
            '/app/lora',loratc.app,
            '/app/tsfxy',tsfxy.app,
            '/app/xykj',xykj.app,
            '/app/upload',route.url.Upload,
            '/app/apiUtil',apiUtil.app,
            '/app/bLink',bLink.app,
            '/app/blog',blog.app,
        ))
        _thread.start_new_thread(web.config.app.run, ('tcp /LoaPro 60001',))
        #_thread.start_new_thread(web.config.app.run, ('udp /upc 50000',))
        # _thread.start_new_thread(web.config.app.run, ('tcp /Api 60009',))
        _thread.start_new_thread(web.config.app.run, ('websocket / 55000',))
        # _thread.start_new_thread(web.config.app.run,('tcp /JsonShell 60002',))
        # _thread.start_new_thread(web.config.app.run, ('tcp /LockTranslate 60000',))
        # _thread.start_new_thread(web.config.app.run, ('tcp /tsfxyFpga 12346',))
        # _thread.start_new_thread(web.config.app.run, ('tcp /Moutbus 12345',))

        from tool.tcptransport import TranslateServer
        def f(port):
            TranslateServer(('0.0.0.0',port)).start()
        if 'tcptransport' in sys.argv:
            _thread.start_new_thread(f,(54323,))
            _thread.start_new_thread(f,(54325,))
        web.config.app.run('50001')
    elif 'air' in sys.argv:
        kill(50001)
        from app import airdatafilter
        from app import route
        web.config.app = web.application((
            '/app/route', route.app,
            '/app/air',airdatafilter.app
        ))
        _thread.start_new_thread(web.config.app.run, ('websocket 55000', web.httpserver.StaticMiddleware))
        web.config.app.run('50000')
    elif 'ui' in sys.argv:
        kill(50001)
        from app import route
        from app import ui
        web.config.app = web.application((
            '/app/ui', ui.app,
            '/app/route',route.app,
        ))
        _thread.start_new_thread(web.config.app.run, ('websocket 55000', web.httpserver.StaticMiddleware))
        web.config.app.run('50001')
    elif 'blog' in sys.argv:
        kill(50001)
        from app import route,blog,blog,game
        web.config.app = web.application((
            '/app/route', route.app,
            '/app/blog',blog.app,
            '/app/game',game.app,
        ))
        _thread.start_new_thread(web.config.app.run, ('tcp /Api 60009',))
        _thread.start_new_thread(web.config.app.run, ('websocket 4000', web.httpserver.StaticMiddleware))
        web.config.app.run('50000')
elif 'qf_com'==sys.argv[1] or 'qf_fpga'==sys.argv[1] :
    from app.tsfxy.fpgacome import QfServer,MoutbusServer
    if 'qf_com'==sys.argv[1]:
        MoutbusServer(('0.0.0.0',int(sys.argv[2]))).start()
    else:
        QfServer(('0.0.0.0',int(sys.argv[2]))).start()
elif 'sql_gen'==sys.argv[1]:
    cwg_sql='mysql+pymysql://root:4r7cIWIVtz@192.168.1.11/daotest?charset=utf8'
    btj_sql='mysql+pymysql://root:xykj20160315@114.115.219.15/gbg?charset=utf8'
    url=sys.argv[2] if len(sys.argv)>2 else btj_sql
    file=sys.argv[3] if len(sys.argv)>3 else 'app/fphs/model'
    from sqlacodegen.main import convert
    convert(url,file+'.py')
    convert(url, file+'.json')
    convert(url, file + '.docx')
elif 'qt_px_del'==sys.argv[1]:
    from tool.files_del import FileDeal
    FileDeal(sys.argv[2]).run()

elif 'lora_client'==sys.argv[1]:
    from app.loratc.armpy2.main import run
    run()

elif 'db'==sys.argv[1]:
    if 'fyj' in sys.argv:
        from app.fyj.model import db,MyDb,Base
        db.copy(
            MyDb(url='mysql+pymysql://root:xykj20160315@lin.eanttech.com/fyj?charset=utf8', db_name="mysql"),
            'fyj',
            Base
        )
elif 'keyboard'==sys.argv[1]:
    import time
    time.sleep(float(sys.argv[2]))
    from pynput.keyboard import Key, Controller
    keyboard = Controller()
    keyboard.type(sys.argv[3]+'\n')





