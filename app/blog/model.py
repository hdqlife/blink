from common.db import *
class blog_article(MyTable):
    __tablename__='blog_article'
    __table_args__ = (
        Index('title_type', 'title', 'parentId', unique=True),
    )
    title=Column(String(32),default='')
    content=Column(Text)
    char_num=Column(INTEGER,default=0)
    allow_comments=Column(INTEGER,default=0)
    vote_num=Column(INTEGER,default=0)
    parentId=Column(INTEGER,default=0)
    type=Column(String(256),default='content')
def init_db():
    db= MyDb('mysql+pymysql://root:xykj20160315@127.0.0.1/base?charset=utf8', db_name="mysql")
    db.update(MyTable,'drop')
if __name__=='__main__':
    init_db()