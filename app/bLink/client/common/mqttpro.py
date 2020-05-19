import traceback
import json
from common import function
from . import msg
import sys
def read(io,data,f):
    try:
        data=json.loads(data)
        rt=dict(id=data["id"],type=data["type"],code=msg.CODE_RIGHT,data=[],msg="")
        rt['class']=data['class']
    except Exception as e:
        rt=dict(id="none",type="none",code=msg.CODE_DATA_PARSE_ERROR,data=[],msg='data not a right json')
        rt['class']=''
        return rt
    if io.userdata["code"]:
        rt["code"]=io.userdata['code']
        if rt['code']==msg.CODE_DEVICE_BUSY:
            rt["msg"]="device busy"
            return rt
        io.userdata['code']=0
    if len(data["data"])==0:
        data["data"]=[{"id":None}]
    for d in data["data"]:
        try:
            if 'class' not in d:
                d["class"]=data["class"]
            rs=f(data["type"],d)
        except Exception as e:
            rt["code"]=msg.CODE_ERROR
            traceback.print_exc()
            rt["msg"]='trace:%s;error:%s'%(str(traceback.format_exc()),str(e))
            break
        else:
            if isinstance(rs,list):
                for r in rs:
                    rt["data"].append(r)
            elif rs is not None:
                rt["data"].append(rs)
    if io.userdata["msg"]:
        rt["msg"]=io.userdata["msg"]
        io.userdata["msg"]=""
    if not rt["code"]:
        rt["code"]=msg.CODE_RIGHT
    return rt