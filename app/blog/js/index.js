var Config={
    el:'#app',
    data:{
        array:[[18924,215883],1575753],
        filterText:"",
        data:[],
        drawer2:false,
        selectNode:{
            nid:-1,
            value:"",
            icon:"",
        },
        msg:"/app/blog/js/tmp.js",
        fullscreen:false,
        default_expanded:JSON.parse(localStorage.default_expanded||'[]'),
    },
    watch:{
        filterText(val) {
            this.$refs.tree.filter(val);
        },
        fullscreen(value){
            var oj={'position':'fixed','width':'100%','height':'100%','z-index':100,'left':0,'top':0,'background':'#fff'}
            for(var key in oj){
                d3.select('#evalparent').style(key,value?oj[key]:null)
            }
            this.update({msg:this.msg})
            
        }
    },
    methods:{
        filterNode(value, data) {
            if (!value) return true;
            return data.label.indexOf(value) !== -1;
        },
        update(b){
            console.log('update',b)
            this.msg=b.msg
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
        nodeClick(a){
            localStorage.blogId=a.id
            Net.get('/app/blog/index',{id:a.id,user:Net.get_param.user},(b)=>{
               console.log(b)
               //this.update(b)
            })
            
        },
        edit(v,data,node){
            var map={
                'el-icon-delete':'_del',
                'el-icon-plus':'_add',
                'el-icon-edit':'_update'
            }
            this.selectNode.method=map[v]
            this.selectNode.nid=data.id
            this.selectNode.param=[data,node]
            this.selectNode.icon=v
            if(map[v]!='_del'){
                this.selectNode.value=data.label
            }else{
                this.submit()
            }
            console.log(v,data,node)
        },
        submit(){
            node=this.selectNode.param.pop()
            data=this.selectNode.param.pop()
            Net.post('/app/blog/index',this.selectNode,(d)=>{
                if(this.selectNode.method=="_add"){
                    const newChild = { id: d.data, label: this.selectNode.value, children: [] };
                    if (!data.children) {
                        this.$set(data, 'children', []);
                    }
                    data.children.push(newChild);
                }else if(this.selectNode.method=="_del"){
                    const parent = node.parent;
                    const children = parent.data.children || parent.data;
                    const index = children.findIndex(d => d.id === data.id);
                    children.splice(index, 1);
                }else{
                    data.label=this.selectNode.value
                }
                this.selectNode.nid=-1
                  
            })
        },
        expend(a,b){
            localStorage.default_expanded=JSON.stringify([a.id])
        
        }
    },
    mounted(){
        d3.select('#app').style('visibility','visible')
        Net.post('/app/blog/index',
            {method:'load',nid:0},
            (d)=>{
                this.data=d.array.children
                this.nodeClick({id:(localStorage.blogId||0)})

            }
        )
        
    }
}

function init(params) {
    var socket=new Socket({
        onopen(){
            this.send_json({srcid:'blog'})
        },
        recv_json:function(v){
            if(window.root&&v.msg!="Not"){
                window.root.update(v)
            }
        
        }
    })
    window.root=new Vue(Config)
    
}