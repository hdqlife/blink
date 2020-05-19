
window.CALLS={}
window.SENDID=1
function recv(s){
    console.log('recv',s)
    if(s.id&&window.BB.bVue){
        var fv=window.BB.bVue.filterText
        if(s.i.indexOf(fv)!=-1){
            var data=null
            try {
                var jsons=s.i.replace("b'",'').replace("'",'')
                data=JSON.parse(jsons)
           
            } catch (error) {
                console.log('recv',error)
            }
            if(data){
                if(s.id.indexOf('replay')!=-1&&window.CALLS[data.id]){
                    window.CALLS[data.id](data)
                    window.CALLS[data.id]=null
                }
            }
            window.BB.bVue.log=[s].concat(window.BB.bVue.log)
        }
        
    }
}
window.BSOCKET=window.BSOCKET||new Socket({
    onopen(){
        this.send_json({srcid:'bLinkHelp'})
    },
    recv_json(s){
        recv(s)
    },
})
var CLASSARRAY=['Device','Identifier','Task','Event']
export default {
    load(el,path){
        console.log('path',path)
        el.html('')
        var value=Net.get_now(path)
        var num=1
        var that=this
        this.initset(el)
        this.div=el.append('div')
        var rtps=[]
        if(!path) return
        var f=this.div.html('').append('iframe').attr('src',path).style('width','100%')
            .style('height','100%').on('load',function(){
                var body=d3.select(this.contentDocument.body)
                var ps=body.selectAll('p').nodes().map((p,pnum)=>{
                    
                    if(p.innerHTML=='下发'){
                        d3.select(p).style('color','#ff0').html('下发'+pnum)
                        var root=p.parentElement.nextElementSibling
                        if(root==null){
                            root=p.parentElement.parentElement.nextElementSibling.firstElementChild
                        }
                        if(root==null){
                            console.log('rootnull',p.parentElement.innerHTML)
                        }
                        //console.log(p,root)
                        var ts=root.children[1].innerText
                        // try{
                        //     //ts=ts.replace(/true/g,'True')
                        //     ts=eval(ts)
                        // }catch(e){
                        //     console.log('parseError',ts,e)
                        // }
                        var tmp=d3.select(root)
                        num+=1
                        tmp.html('').append('p').html('结果')
                        var tmp1=tmp.append('div')
                        p._outrsrc=tmp1.append('pre').style('width','50%').style('float','left').html(ts)
                        p._out=tmp1.append('pre').style('width','50%').style('float','left').html('{}')
                                .style('min-height',p._outrsrc.style('height'))
                        p.onclick=function(){
                            //d3.select(p).style('color','#ff0')
                            var inputStr=this.nextElementSibling.innerText
                            var senddata={
                                topic:that.defaultdata['topic'],
                                data:inputStr,
                                wait:4
                            }
                            console.log('send',senddata,this)
                            this._out.html('')
                            Net.post('/app/bLink/send',senddata,(v)=>{
                                Log.success(v.msg)
                                this._out.html(v.data||'error')
                            })
                            //console.log('pclick',this._out)
                        }
                        p.onclick()
                    }
                })
            })
     
    },
    logshow(el){
        var that=this
        this.div=el.append('div')
        var leftdiv=this.div.html('').style('text-align','left').style('display','flex').style('height','90%')
            .append('div').style('width','15%')
        var rightdiv=this.div.append('div').style('border','1px solid #000')
        .style('width','83%').style('height','100%').style('overflow','auto')
        this.fileterInput=leftdiv.append('input')
        leftdiv.append('button').html('send').on('click',function(){
            var senddata={
                topic:that.defaultdata['topic'],
                data:that.text.text(),
            }
            Net.post('/app/bLink/send',senddata,(v)=>{
                Log.success(v.msg)
            })
        }).style('margin-left',3)
        

        leftdiv.append('button').html('clear').on('click',function(){
            rightdiv.html('')
        }).style('margin-left',3)
       
        leftdiv.append('br')
        this.text=leftdiv.append('textarea').html(JSON.stringify({
            "id": "123",
            "class": "AI",
            "type": "query",
            "data": [
           
            ]
        },null,4)).style('width','100%').style('height','100%')
    },
    send(data,callback,Id){
        if(typeof data=="string"){
            try {
                data=JSON.parse(data)
            } catch (error) {
                data={}
            }
        }

        data.id=window.SENDID+''
        window.SENDID+=1
        window.CALLS[data.id]=callback             
        Id=Id||this.bVue.Id
        var senddata={
            topic:this.defaultdata['topic'].replace(this.bVue.Id,Id),
            data:JSON.stringify(data),
            wait:0
        }
        Net.post('/app/bLink/send',senddata,(v)=>{
            //Log.success(v.msg)
        })
    },
    logVue(el){
        var that=this;
        this.bVue=new Vue({
            el:el.html('').node(),
            template:`
<div style="overflow: hidden;width:100%;height:100%">
    <my-arealayout :value="array"  class_name="main" ref="layout">
        <div slot="0" style="overflow: auto;height: 100%;width:100%">
            <el-tree
                class="filter-tree"
                :data="data"
                :highlight-current="true"
                @node-click="nodeClick"
                default-expand-all
                node-key="id"
                ref="tree">
                <p slot-scope="{ node, data }" style="width: 100%;">
                    <span style="float: left;max-width: 80px;">{{data.Id}}</span>
                    <i :class="v" v-for="(v,i) in data.methodtype"
                            @click.stop="() => edit(v,data,node)" style="float: right;margin-left:8px;" ></i>
                </p>
            </el-tree>
        </div>
 
        <div slot="1" class="main">
            <el-input type="textarea" v-model="senddata" rows="8" style="height:100%;display:none"></el-input>
            <my-tb title="blink" rows="10" ref="senddata"></my-tb>
        </div>
        <div slot="2" class="main">
            <el-button  @click="send" style="width:50%">发送</el-button>
            <el-button @click="log=[]" style="width:50%">清空</el-button>
        </div>
        <div slot="3" class="main">
            <div ref="setdiv"></div>
            <el-button @click="save('update')">update</el-button>
            <el-button @click="save('read')">read</el-button>
            <el-button @click="save('write')">write</el-button>
        </div>
        <div slot="4">
            <my-form :model="url_config" inline ref="config_param" style="height:100%;overflow:hiddden"></my-form>
        </div>
 
        <div slot="5" style="overflow-y:auto;height:100%;width:100%">
            <div v-for="item in log">
                <p>{{item.id}}:{{item.t.toDateStr()}}</p>
                <p>{{item.i}}</p>
                <br>
            </div>
        </div>
        
    </my-arealayout>
    <el-dialog :visible.sync="drawer2" :show-close="true" >
        <my-form :model="add_data" ref="add_form" inline style="max-height:400px;overflow-y:auto"></my-form>
        <el-button @click="add">add</el-button>
    </el-dialog>
</div>
            `,
            data:{
                array:[[15,10,2],[6,45,45]],
                filterText:"",
                Id:"",
                data:[],
                add_data:{},
                drawer2:false,
                url_config:{},
                selectNode:{
                    nid:-1,
                    value:"",
                    icon:"",
                },
                log:[],
                senddata:JSON.stringify({
                    "Id":"",
                    "class": "AI",
                    "type": "query",
                    "deviceid":"",
                    
                    
                },null,4)
            },
            methods:{
                filterNode(value, data) {
                    if (!value) return true;
                    return data.label.indexOf(value) !== -1;
                },
                update(b){
                    var el=d3.select('#eval')
                    el.html('').style('width','100%').style('height','100%')
                    var div=el.append('div').style('width','100%').style('height','100%')
                    Net.loadJs(b.msg,(f)=>{
                        f.init(div)
                        window.MathJax.Hub.Queue(["Typeset", MathJax.Hub, el.node()]);
                    },(f)=>{
                        div.append('pre').style('font-size','24px')
                        .style('overflow','scroll').style('text-align','left')
                        .style('margin','10px').style('height','100%').html(f)
                    })
                },
                getId(a){
                    var Id=""
                    var tmp=a
                    console.log('getid',a)
                    for(i=0;i<5;i++){
                        if(tmp){
                            if(tmp.class=='Device'&&tmp.Id!='Device'){
                                Id=tmp.Id+'_'+Id
                                console.log('tmpa',tmp.Id,tmp.class,tmp)
                            }
                            tmp=tmp.parent
                        }else{
                            break
                        }
                    }
                    return Id.substr(0,Id.length-1)
                },
                nodeClick(a,b){                   
                    this.edit('el-icon-refresh',a,b)
                },
                send(){
                    window.SEND_ADD_ID=(window.SEND_ADD_ID||0)+1
                    var data=this.$refs.senddata.textarea
                    var deviceId='aca213cfac04'
                    try {
                        var data1=JSON.parse(this.$refs.senddata.textarea)
                        var senddata={id:window.SEND_ADD_ID,data:[{}]}
                        
                        if(data1['deviceid']){deviceId+=('_'+data1['deviceid'])}
                        for(var key in data1){
                            if(key=='type'||key=='class'){
                                senddata[key]=data1[key]
                            }else if(key=='deviceid'){
                                continue
                            }else{
                                senddata['data'][0][key]=data1[key]
                            }
                        }
                        data=JSON.stringify(senddata)
                    } catch (error) {
                        data=senddata
                    }
                    that.send(data,null,deviceId)
                },
                edit(v,data,node){
                    this.selectNode=[data,node]
                    var a=data
                    var b=node
                    if(v=='el-icon-plus'){
                        var value=Net.get_now('/app/bLink/send',{method:"class"}).data
                        this.add_data=value[data.class]
                        this.drawer2=true
                    }else if(v=='el-icon-delete'){
                        that.send({
                            type:'delete',class:data.class,
                            data:[{Id:data.Id}],
                        },undefined,this.getId(data))
                        data.parent.children=[]
                    }else if(v=='el-icon-refresh'){
                        var s={type:"query",class:a.class}
                        console.log(a,b)
                        var that1=this
                        var Id=this.getId(a)
                        this.url_config={}
                        if(CLASSARRAY.indexOf(a.Id)!=-1){
                            s.type="search"
                            s.class=a.Id
                            s.data=[{class:a.Id,type:"all"}]
                            a.children=[]
                            that.send(s,(v)=>{
                                v.data.map((v1)=>this.childNode(v1,a)).forEach(v1=>{
                                    console.log('append',v1,b)
                                    this.$refs.tree.append(v1,b)
                                })
                            },Id)
                        }else{
                            s.data=[{class:a.class,Id:a.Id}]
                            that.send(s,(v)=>{
                                this.url_config=v.data[0]||{}
                                console.log('recvd',v,b,a)
                            },Id)
                        }
                    }
                    console.log(v,data,node)
                },
                add(){
                    var value=this.$refs.add_form.get_value()
                    var Id=this.getId(this.selectNode[0])
                    that.send({
                        type:'add',class:this.selectNode[0].class,
                        data:[value],
                    },(v)=>{
                        if(v.msg){
                            Log.error(v.msg)    
                        }
                        if(v.code==200){
                            this.drawer2=false
                        }
                        
                        console.log('addback',v)
                    },Id)
                    console.log(value)
                },
                submit(){
          
                },
                expend(a,b){
                   
                },
                update(data){
                    this.Id=data.topic.split('/')[3]
                    var dt={Id:this.Id,class:'Device',methodtype:['el-icon-refresh']}
                    this.data=[this.childNode(dt,null)]
                },
                childNode(a,p){
                    var rt=[]
                    var array=CLASSARRAY.slice(p==null?0:1)
                    a.parent=p
                    a.children=[]
                    if(a.class=='Device'){
                        for(var i=0;i<array.length;i++){
                            var s={Id:array[i],class:array[i],methodtype:['el-icon-refresh',"el-icon-plus"],children:[],parent:a}
                            a.children.push(s)
                        }
                    }
                    if(a.methodtype==undefined){a.methodtype=['el-icon-refresh','el-icon-delete']}
                    return a
                },
                save(tp){
                    var data=this.$refs.config_param.get_value()
                    data['Id']=this.selectNode[0].Id
                    that.send({type:tp,class:this.selectNode[0].class,data:[
                        data
                    ]},(d)=>{
                        if(d.data[0]){
                            BB.bVue.$refs.config_param.update('value',d.data[0]['value'])
                        }
                    },this.getId(this.selectNode[0]))
                }
                    
                
            },
            mounted(){
                setTimeout(()=>{
                    that.initset(d3.select(this.$refs.setdiv),this.update)
                },20)
            }
        })
    },
    connect(sucess){
        console.log(this.defaultdata)
        Net.post('/app/bLink/mqttConnect',this.defaultdata,(v)=>{
            Log.success(v.msg)
            if(sucess){
                sucess(this.defaultdata)
            }
        })
    },
    init(el){
        window.BB=this
        Net.get_param['type']!='html'?this.logVue(el):this.load(el,'')
    },
    initset(el,sucess){
        var that=this
        var clientid=new Date().getTime()+''
        this.defaultdata={
            ip:'171.221.238.16',port:1883,clientId:clientid,
            username:'username',password:'password',
            topic:'/sys/1235401760240529409/aca213cfac04/config/push'
        }
        var inputs=el.append('input').attr('value',JSON.stringify(this.defaultdata)).style('width',900)
        .style('margin','0 10px')
        el.append('button').html('设置').on('click',function(){
            try{
                var value=JSON.parse(inputs.node().value)
                that.defaultdata=value;
                that.connect(sucess)
            }catch{
                Log.error('输入不是一个合法的json')
            }
        }).style('margin','0 10px')
        var nameNode=el.append('input').attr('value','blinktest.html').style('margin','0 10px')
        el.append('input').attr('type','file').on('change',function(v){
            Net.upload_file('/app/route/upload',{f_file:this.files[0],name:nameNode.node().value},(d)=>{
                Log.success(d.msg)
            })
        }).style('margin','0 10px')
        var sendnumss=0
        el.append('button').html('全部测试').on('click',function(){
            sendnumss+=1
            that.load(el,'/app/static/upload/'+nameNode.node().value+'?x='+sendnumss)
        }).style('margin','0 10px')
        this.connect(sucess)
        //this.load('/app/static/upload/blinktest.html',defaultS)
    }
}
        