
from common.proto import BaseWeb
import base64
from .tool import *
from .device import DeviceManage,crc16
Messages = []

def recv_msg(msg_type,msg_value=''):
    if not DB['check']():
        send_command(msg='connect_db')
        SYS.VIEW = LOGIN_STR
    else:
        if msg_type=='jump':
            SYS.VIEW=msg_value
            if msg_value not in [LOGIN_STR,MENU_STR] and SYS.device_enable==False:
                return
            send_command(msg='jump',array=[msg_value])
        elif msg_type=='login':
            session = DB['db'].session()
            msg_value=msg_value.upper()
            if SYS.VIEW==LOGIN_STR or SYS.VIEW==LOGIN_CHECK:
                Login.post(msg_value,session)
            elif SYS.VIEW==OLD_NEW_STR or SYS.VIEW==RETURN_STR:
                query=session.query(ShBorrow,ShGood,ShGoodsstorage).join(
                    ShGood, ShGood.id==ShBorrow.goods_id
                ).outerjoin(
                    ShGoodsstorage,ShGoodsstorage.pid==ShGood.id
                ).filter(
                    ShBorrow.qr_code==msg_value,
                    ShBorrow.borrow_num>0
                ).group_by(ShBorrow.qr_code).one_or_none()
                send_command(s=MyJson(msg='get_qr',array=[query,msg_value]))
            session.close()
        else:
            send_command(msg=msg_type,array=msg_value)
OB.subscribe(CWG_MSG,recv_msg)

class Index(BaseWeb):
    #db,CWG_CONFIG['ip']=connect_db(SELF_IP,CWG_CONFIG)
    device=None
    def init(self):
        self.rt=MyJson(statu=0,msg='',array=[],data={})
        self.db=DB['check']()
        if self.db:
            self.session=self.db.session()
            self.user=self.session.query(ShUser).filter(
                ShUser.id==SYS.USER_ID
            ).one_or_none()
            SYS.device_enable,SYS.device_rest_time=self.device_auto()
            send_command(statu=UPDATE_IP_REST_DAY, array=[SELF_IP,SYS.device_rest_time,SYS.device_enable],data=SYS.device_id)
            if SYS.device_enable == False and SYS.VIEW != LOGIN_STR:
                self.post = self.error
        else:
            self.post = self.error
    def error(self,**kargs):
        self.rt.statu=-1
        return self.rt.json_dumps()
    def device_auto(self):
        self.device=self.session.query(ShDevice).filter(
            ShDevice.ip==SELF_IP
        ).one_or_none()
        if self.device is None:
            if '127' not in SELF_IP:
                src_s="%s,%s"%(SELF_IP,get_cpu_id())
                ds=base64.b64encode(src_s.encode('utf-8')).decode('utf-8')
                self.device=ShDevice(ip=SELF_IP,flag=True,count=0,name='',number=ds,pk=0)
                self.session.add(self.device)
        if self.device.pk == 0:
            return False, '0天'
        else:
            SYS.device_id=self.device.id
            de = MyEdCryption(pk=self.device.pk)
            rs = de.decode(get_cpu_id(), self.device.code)
            end_t = get_end_time(rs)
            if end_t == -1:
                return True, '永久使用'
            elif end_t > int(time.time()):
                return True, '%s天' % (end_t - int(time.time()) / 24 / 3600)
            else:
                return False, '0天'

    def get(self,*args):
        return open('app/static/cwg/index.html','rb').read().decode('utf_8')

Device=DeviceManage(CWG_CONFIG,DB)
class Login:
    param = dict(card='')
    @staticmethod
    def post(card,session,**kwargs):
        rt=MyJson(sttau=0,msg='',array=[],data={})
        user=session.query(ShUser).filter(
            ShUser.card==card
        ).one_or_none()
        if SYS.VIEW==LOGIN_STR:
            if user is None:
                rt.statu=LOGIN_FAIL
            else:
                SYS.USER_NUMBER = card
                SYS.USER_ID=user.id
                if not SYS.device_enable:
                    rt.statu=DEVICE_ENABLE
                else:
                    rt.statu=LOGIN_SUCCESS
            rt.data=user
        elif SYS.VIEW==LOGIN_CHECK:
            rt.msg='show_check_statu'
            if card==SYS.USER_NUMBER:
                rt.array = [LOGIN_SUCCESS]
            else:
                rt.array=[LOGIN_FAIL]
        send_command(s=rt)
        return rt.json_dumps()
class Img(Index):
    def get(self):
        if self.input.get('name')=='feature':
            from tool.image import Api
            return Api.dump_img(Device.device_com.img,Device.device_com.IMG_WIDTH,Device.device_com.IMG_HEIGHT)
        if self.input.get('name')=='SeeFeature':
            return '<img src="/app/cwg/img/feature" style="border:1px solid #000">'
        img=self.session.query(ShImagedatum).filter(
            ShImagedatum.id==self.input['icon']
        ).one_or_none()
        if img is None:
            return read_file('app/static/cwg/img/head.png')
        else:
            return img.data
class System(Index):
    param = dict(msg_name='',msg_value='')
    not_require = ['msg_value']
    def get(self):
        return self.rt.json_dumps()
    def post(self,msg_name,msg_value,**kwargs):
        OB.publish(CWG_MSG,msg_name,msg_value)
        return self.rt.json_dumps()
class DeviceGetInfo(Index):
    param = dict(method="device")
    def post(self,method,**kwargs):
        if method=='menu_info':
            self.rt.data.ip=SELF_IP
            self.rt.data.rest_time=SYS.device_rest_time
        elif method=='device':
            self.rt.msg=Device.device_com.get_id()
            self.rt.data=Device.device_com.get_statu()
class GoodsQuery(Index):
    param = dict(method='get_types',gid=0)
    def post(self,method,gid,**kwargs):
        if method=='get_types':
            self.rt.array=self.session.query(ShGoodsrel).all()
        elif method=='get_goods_list':
            self.rt.array=self.session.query(ShGood,ShGoodsstorage).filter(
                ShGood.kind == gid[0],
                ShGood.brand == gid[1],
                ShGood.g_type == gid[2],
                ShGoodsstorage.err != ERR_HD_STATU,
                ShGoodsstorage.pid == ShGood.id,
                ShGoodsstorage.rsg>0,
                ShGoodsstorage.did==self.device.id
            ).all()
        elif method=='get_goods_info':
            self.rt.array=self.session.query(ShGood,ShGoodsstorage).filter(
                ShGood.id==gid,
                ShGoodsstorage.err != ERR_HD_STATU,
                ShGoodsstorage.pid == ShGood.id,
                ShGoodsstorage.rsg>0,
                ShGoodsstorage.did==self.device.id
            ).all()
        return self.rt.json_dumps()

class DeviceMotor(Index):
    param = dict(number=1,type=['test','print'],data={},s='print')
    test_num=0
    not_require = ['data','number']
    def post(self,number,type,data,s,**kwargs):
        # if type=='test':
        #     DeviceMotor.test_num=(DeviceMotor.test_num+1)%100
        #     if DeviceMotor.test_num%10==0:
        #         self.rt.statu=0
        #     else:
        #         self.rt.statu=DEVICE_BUSY

        if type=='print':
            Device.dy_com.Print(s)
        elif type=='run':
            DeviceMotor.test_num=(DeviceMotor.test_num+1)%40
            self.rt.statu=0 if DeviceMotor.test_num%10==9 else 1
        return self.rt.json_dumps()
class Return(Index):
    param = dict(method='list_all',value=1,data=dict(id=0,statu=0))
    not_require= ['data','value','method']
    def post(self,method,value,data,**kwargs):
        if method=='list_all':
            self.rt.array=self.session.query(ShBorrow).filter(
                ShBorrow.borrow_num!=0
            ).all()
        if method=='return':
            borrow=self.session.query(ShBorrow).filter(
                ShBorrow.id==data['id']
            ).one()
            borrow.borrow_num-=value
            self.session.add(ShReturn(
                user_id=self.user.id,
                device_id=self.device.id,
                goods_id=borrow.goods_id,
                borrow_id=borrow.id,
                return_num=value,
                statu=data['statu'],
                time=nowt()
            ))

        return self.rt.json_dumps()
class User(Index):
    param = dict(method='query_shop',value=-1)
    not_require = ['value']
    def post(self,method,value,**kwargs):
        if method=='query_shop':
            query=self.session.query(ShBorrow,ShGood,ShGoodsstorage).join(
                ShGood, ShGood.id==ShBorrow.goods_id
            ).outerjoin(
                ShGoodsstorage,ShGoodsstorage.pid==ShGood.id
            ).filter(
                ShBorrow.device_id==self.device.id,
                ShBorrow.user_id==self.user.id,
                ShBorrow.borrow_num>0
            ).group_by(ShBorrow.id)
            print(query)
            self.rt.array=query.all()
        return self.rt.json_dumps()
from app.route.url import Moutbus
from common.server import MoutbusClient
class GetDebug(Moutbus):
    com=MoutbusClient(dict(ip=38400,port=CWG_CONFIG["device_com"]))
