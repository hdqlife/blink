import sys
sys.path.append('common/qtui')
from myqlabel import MyQLabel,Vue,VueModel
from .qtui.main_ui import Ui_Form
from .qtui.homepage_ui import Ui_HomePage
from .qtui.userinfo_ui import Ui_Form as Ui_UserInfo
from .qtui.get_ui import Ui_Form as UI_Get
from PyQt5 import Qt
from PyQt5.QtCore import *
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QLabel,QHBoxLayout,QApplication,QWidget
from PyQt5.QtWidgets import QScroller,QLayout,QVBoxLayout
from flowlayout import FlowLayout
from common import function
class CwgModel(VueModel):
    now_date='xxx'
    username=""
    rest=0
    restj=0
CWGMODEL=CwgModel(Vue())
def init():
    CWGMODEL._resources=lambda path:(
        print('load',path),
        ''
        #'app/cwg/qtui/head.png'
    )[-1]
    MyQLabel.setModel(CWGMODEL)
def clearLayout(layout:QLayout):
    s=layout.takeAt(0)
    index=0
    while s:
        index+=1
        wg=s.widget()
        layout.removeItem(s)
        layout.removeWidget(wg)        
        wg.setVisible(False)
        s=layout.takeAt(0)
    return index
def clearWidget(widget:QWidget):
    num=0
    for d in widget.children():
        #d.close()
        if isinstance(d,QLayout):
            clearLayout(d)
        else:
            d.close()
        d.deleteLater()
        num+=1
    return num


class GetLaftLabelUtil():
    styles=[
'QLabel{font-size: 30px;background:%s;padding:10 4 10 4;border-radius:10px;color:white;}',
'color:%s;font-size:25px;',
'color:%s;font-size:25px;'
    ]
    def __init__(self,widgets,listwidget):          
        self.widgets=[self.load(i,widgets[i]) for i in range(len(widgets))]
        self.listwidget=listwidget
        self.selectcolor="#24C5BB"
        self.click(0,0)
    def load(self,index,widget):
        flow=widget.layout()
        if flow is None:
            flow=FlowLayout(hSpacing=10,vSpacing=15)
            widget.setLayout(flow)
        return dict(index=index,select=0,flow=flow)
    def click(self,index,num):
        if index>=len(self.widgets):
            self.drawlist()
            return
        text="xx" if index==0 else str(self.widgets[index-1]['select'])
        self.widgets[index]['select']=num
        data=[text+str(i) for i in range(10*(index+1))]
        print('clear',index,clearLayout(self.widgets[index]['flow']))   
        for i in range(len(data)):
            tmp=MyQLabel(data[i],data=i,on_click=lambda c:self.click(index,c.data))
            self.widgets[index]['flow'].addWidget(tmp)
            if i==num:
                tmp.setStyleSheet(self.styles[index]%'#000000')
            else:
                tmp.setStyleSheet(self.styles[index]%self.selectcolor)
        self.click(index+1,0)
    def drawlist(self):
        layout=self.listwidget.layout()
        clearLayout(layout)
        for d in range(10):
            vbox=QVBoxLayout()
            vbox.addWidget(mylabel())
            mylabel=MyQLabel(str(d))
            layout.addWidget(mylabel,int(d/2),d%2)
            layout.addLayout(vbox,int(d/2,d%2))
def load(main:Ui_Form,homepage:Ui_HomePage,get:UI_Get,
        userinfo:Ui_UserInfo,*args):
    # while main.stackedWidget.count()>0:
    #     main.stackedWidget.removeWidget(main.stackedWidget.currentWidget())
    
    init()
    main.stackedWidget.addWidget(homepage._widget)
    QScroller.grabGesture(get.scrollArea,QScroller.LeftMouseButtonGesture)
    get.verticalLayout_3.insertWidget(0,userinfo._widget)
    GetLaftLabelUtil([get.left_widget_1,get.left_widght_2,get.left_widget_3],get.widgetright)
    def getshow(*args):
        get.scrollWidgetItem.setMaximumWidth(get.scrollWidget.width())
    get._widget.showEvent=getshow
    
    
    main.stackedWidget.addWidget(get._widget)
    main.stackedWidget.setCurrentIndex(1)
    main._widget.setWindowFlags(Qt.FramelessWindowHint)#WindowStaysOnTopHint
    main._widget.show()


    # homepage.label_2.setPixmap(QPixmap("app/cwg/qtui/head.png"))
    # main.label.setPixmap(QPixmap("app/cwg/qtui/img/logo.png"))
 
 
    print('count',main.stackedWidget.count())




def loop(num):
    CWGMODEL.now_date=function.nowTs(tp="datatime")
if __name__ == "__main__":
    app=QApplication(['app'])
    args=[Ui_Form(),Ui_HomePage(),UI_Get(),Ui_UserInfo()]
    for arg in args:
        setattr(arg,'_widget',QWidget())
        arg.setupUi(arg._widget)
    load(*args)
    num=0
    def tmptmp(*args):
        global num
        loop(num)
        num=(num+1)%10000
    basectm=QTimer()
    basectm.timeout.connect(tmptmp)
    basectm.start(200)
    # wg=QWidget()
    # Ui_Form().setupUi(wg)
    # wg.show()
    app.exec_()