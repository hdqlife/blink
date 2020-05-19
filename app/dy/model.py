from common.db import MyTable,TEXT,Index,Column,Text,String,Integer,Float,MyDb,LargeBinary
Base=MyTable
class dy_log(Base):
    __tablename__ = 'dy_log'
    __table_args__ = (
        Index('time', 'user_id', 't', unique=True),
    )
    user_id=Column(String(64))
    i=Column(TEXT)
    o=Column(TEXT)

class dy_err(Base):
    __tablename__ = 'dy_err'
    user_id=Column(String(64))
    info=Column(Text)
    data=Column(Text)
    err_type=Column(String(64))

class dy_value_change(Base):
    __tablename__='dy_value_change'
    src_time=Column(Integer)
    src_value=Column(String(128))
    dst_value=Column(String(128))
    param=Column(Text)
    key_name=Column(String(64))
    device_id=Column(String(64))

class dy_msg(Base):
    __tablename__='dy_msg'
    msg_name=Column(String(256))
    msg_value=Column(Text)
    msg_type=Column(Integer)

class dy_device(Base):
    __tablename__= 'dy_device'
    nb_id = Column(String(128),default='')
    device_id = Column(String(128),unique=True)
    name = Column(String(128), default="")
    type = Column(Integer, default=20)
    addr = Column(String(128),default='')
    dc_type=Column(String(32),default='')
    stand_i=Column(Float(10,2),default=0)
    stand_bc=Column(Float(10,2),default=0)
    number=Column(String(128),default='')
    station_code=Column(String(128),default='')
    addr_number=Column(String(128),default='')
    line_length=Column(Float(10,2),default=0)
    jb=Column(TEXT)
    env=Column(Text)

# class dy_station(Base):
#     __tablename__='dy_station'

class dy_record(Base):
    __tablename__='dy_record'
    bsid=Column(String(128),default="")
    deviceid=Column(String(128),default="")
    dc_type=Column(String(128),default="")
    line_length=Column(String(128),default="")
    pictures=Column(Text,default="[]")
    stand_i=Column(Float(10,2),default=0)
    stand_bc=Column(Float(10,2),default=0)
    station_id=Column(String(128),default="")
    userid=Column(String(128),default="")
class TbWxUser(Base):
    __tablename__='wx_user'
    userid=Column(String(128),unique=True)
    password=Column(String(128),default="")
    openId=Column(String(128),default="")
    name=Column(String(128),default="")
    mobile=Column(String(128),default="")
    address=Column(String(128),default="")
    service=Column(String(128),default="")
    email=Column(String(128),default="")
    switch=Column(Integer,default=0)
class dy_station(Base):
    __tablename__='dy_station'
    station_id=Column(String(128),default='')
    station_name=Column(String(128),default='')
    station_addr=Column(String(128),default='')
    station_code=Column(String(128),default='')

class dy_addr(Base):
    __tablename__='dy_addr'
    addrCode=Column(String(128))
    parentId=Column(Integer,default=-1)
    addr=Column(String(128))
    def __init__(self,addrCode,parentId,addr,**kwargs):
        Base.__init__(self,addrCode=addrCode,parentId=parentId,addr=addr,**kwargs)

db=MyDb(url='mysql+pymysql://root:xykj20160315@127.0.0.1/base?charset=utf8',db_name='mysql',debug=False)
db.execute("drop table dy_device")
db.update(Base,'')
try:
    session=db.session()
    session.add(TbWxUser(userid='admin',password='admin'))
    session.commit()
except:
    pass
def update():
    db1 = MyDb(url='mysql+pymysql://root:xykj20160315@122.112.201.243/base?charset=utf8', db_name='mysql', debug=False)
    c=MyDb(url='mysql+pymysql://root:xykj20160315@122.112.201.243/dy?charset=utf8',db_name='mysql',debug=False)
    s=c.execute("select info,nb_id from tb_device")
    session=db1.session()
    import json
    from common.function import parseFloat
    for d in s:
        data=json.loads(d['info'])
        data["addr"]=data["dc_addr"]
        data["stand_i"]=parseFloat(data["stand_i"])
        data["stand_bc"] = parseFloat(data["stand_bc"])
        del data["dc_addr"]
        print(session.query(dy_device).filter(
            dy_device.nb_id==d["nb_id"]
        ).update(data))
    session.commit()
    session.close()
def initAddr():
    from common.function import read_file,json
    values=json.loads(read_file('app/static/upload/json/areadata.json'))
    db.execute('delete from dy_addr')
    session=db.session()
    def h(c,p=None):
        if p:
            c['label']=(p['label']+'/'+c['label']).replace('addr/','')
            print(c['label'],c['value'],p.get('parentId',-1))
            md=dy_addr(c['value'],p.get('parentId',-1),c['label'])
            session.add(md)
            session.commit()
            c['parentId']=md.id
        for child in c.get('children',[]):
            h(child,c)
    h(values)
    session.commit()
    session.close()

    #print(RelationMange(db).dumpJson()[0])
    print('initAddr')
import sys
if __name__=='__main__' or 'initAddr' in sys.argv:
    initAddr()
