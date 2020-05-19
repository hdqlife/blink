from bacpypes.core import deferred,run
from bacpypes.local.device import LocalDeviceObject
from bacpypes.app import BIPSimpleApplication
from bacpypes.apdu import ReadPropertyRequest,ReadPropertyACK,WritePropertyRequest
from bacpypes.iocb import IOCB
from bacpypes.primitivedata import Null, Atomic, Boolean, Unsigned, Integer, \
    Real, Double, OctetString, CharacterString, BitString, Date, Time, ObjectIdentifier,Tag
from bacpypes.constructeddata import Array, Any, AnyAtomic,ArrayOf
from bacpypes.object import get_datatype 
from bacpypes.pdu import Address,RemoteStation
import time
class BacnetApp(BIPSimpleApplication):
    def __init__(self,*args,**kwarg):
        self.userdata=None
        device=LocalDeviceObject(vendorIdentifier=47808,objectIdentifier=47808)
        print('BacnetAppInit',*args,**kwarg)
        BIPSimpleApplication.__init__(self,device,*args,**kwarg)
        #time.sleep(0.8)#等待bac run
        self.whoisback=None
        self.who_is({})
        #self.i_am()
    def do_IAmRequest(self,apdu):
        print('iam',apdu.iAmDeviceIdentifier)
        device=dict(
            bacnetid="%s:%s"%(apdu.iAmDeviceIdentifier[0],apdu.iAmDeviceIdentifier[1]),
            address=list(apdu.pduSource.addrTuple)#[apdu.pduSource.addrNet,[d for d in apdu.pduSource.addrAddr]],
        )
        if self.userdata is not None:
            self.userdata.append(device)
        if self.whoisback:
            self.whoisback(device)
        else:
            pass
            #self.read(device['address'],device['bacnetid'],'objectList',device)
            #self.read(device['address'],device['bacnetid'],'objectList',device if self.whoisback is None else self.whoisback)
    def who_is(self,config,back=None):
        #self.i_am()
        print('whoIs',config)
        self.userdata=[]
        self.whoisback=back
        BIPSimpleApplication.who_is(self,
            low_limit=config.get('lowlimits',0),
            high_limit=config.get('highlimits',10000)
        )
        return self.userdata
    def read(self,pduSource,obj_id,key,device):
        #function.log('request',pduSource,obj_id,key,device)
        if isinstance(obj_id,str):
            obj_id=obj_id.split(':')
            obj_id[1]=int(obj_id[1])
        if isinstance(pduSource,str):
            pduSource=pduSource.split(':')
            pduSource[1]=int(pduSource[1])
        request=ReadPropertyRequest(
            objectIdentifier=tuple(obj_id),
            propertyIdentifier=key,
            #destination=RemoteStation(pduSource[0] or 0,bytearray(pduSource[1]))
            destination=Address(tuple(pduSource))
        )
        iocb = IOCB(request)            
        iocb.context=device,pduSource,key,obj_id
        iocb.add_callback(self.readBack)
        self.request_io(iocb)
    def readBack(self,iocb):
        apdu=iocb.ioResponse
        if not isinstance(apdu, ReadPropertyACK):
            #self.read(iocb.context[0]['address'],iocb.context[0]['bacnetid'],'objectList',iocb.context[0])
            return
        if iocb.context[1]=='objectList':
            value=apdu.propertyValue.cast_out(ArrayOf(ObjectIdentifier))
            value=["%s:%s"%(v[0],v[1]) for v in value]
        else:
            datatype = get_datatype(apdu.objectIdentifier[0], apdu.propertyIdentifier)
            if issubclass(datatype, Array) and (apdu.propertyArrayIndex is not None):
                if apdu.propertyArrayIndex == 0:
                    value = apdu.propertyValue.cast_out(Unsigned)
                else:
                    value = apdu.propertyValue.cast_out(datatype.subtype)
            else:
                value = apdu.propertyValue.cast_out(datatype)
        if isinstance(iocb.context[0],dict):
            iocb.context[0][iocb.context[1]]=value
        else:
            iocb.context[0](value,*iocb.context[1:])
        #function.log('resulttest1',id(iocb.context[0]),iocb.context[0])
    def writeValue(self,addr,obj_id,prop_id,value,indx=None,priority=None):
        if isinstance(obj_id,str):
            obj_id=obj_id.split(':')
            obj_id[1]=int(obj_id[1])
        addr=Address(tuple(addr))
        datatype = get_datatype(obj_id[0],prop_id)
        if datatype is None:return
        if (value == 'null'):
            value = Null()
        elif issubclass(datatype, AnyAtomic):
            dtype, dvalue = value.split(':', 1)
            datatype = {
                'b': Boolean,
                'u': lambda x: Unsigned(int(x)),
                'i': lambda x: Integer(int(x)),
                'r': lambda x: Real(float(x)),
                'd': lambda x: Double(float(x)),
                'o': OctetString,
                'c': CharacterString,
                'bs': BitString,
                'date': Date,
                'time': Time,
                'id': ObjectIdentifier,
                }[dtype]
            value = datatype(dvalue)
        elif issubclass(datatype, Atomic):
            if datatype is Integer:
                value = int(value)
            elif datatype is Real:
                value = float(value)
            elif datatype is Unsigned:
                value = int(value)
            value = datatype(value)
        elif issubclass(datatype, Array) and (indx is not None):
            if indx == 0:
                value = Integer(value)
            elif issubclass(datatype.subtype, Atomic):
                value = datatype.subtype(value)
            elif not isinstance(value, datatype.subtype):
                raise TypeError("invalid result datatype, expecting %s" % (datatype.subtype.__name__,))
        elif not isinstance(value, datatype):
            raise TypeError("invalid result datatype, expecting %s" % (datatype.__name__,))
        # build a request
        request = WritePropertyRequest(
            objectIdentifier=tuple(obj_id),
            propertyIdentifier=prop_id,
            destination=addr
        )
        # save the value
        request.propertyValue = Any()
        request.propertyValue.cast_in(value)
        if indx is not None:
            request.propertyArrayIndex = indx
        if priority is not None:
            request.priority = priority
        iocb = IOCB(request)
        self.request_io(iocb)
if __name__=='__main__':
    import time
    import _thread
    print('bac')
    app=BacnetApp(('0.0.0.0',47808))
    tmp={}
    def loop():
        time.sleep(1)
        app.writeValue(["192.168.1.35",47808],"analogInput:2","presentValue",5)
        app.read(["192.168.1.35",47808],"analogInput:2","presentValue",tmp)
        time.sleep(2)   
        print(app.userdata,tmp)
    def readojlist(*args):
        print('readojlist',*args)
    def whoisback(device):
        app.read(device['address'],device['bacnetid'],"objectList",readojlist)
        print('whoisback',device)

    def loop2():
        app.who_is({},whoisback)
    loop2()
    #_thread.start_new_thread(loop,())
    run()
    
