#!/usr/bin/env python
#-*-coding:utf-8-*-
from . import db
from  datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin,AnonymousUserMixin
from . import login_manager
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app
from markdown import markdown
import bleach

class Follow(db.Model):
    __tablename__='follows'
    follower_id=db.Column(db.Integer,db.ForeignKey('users.id'),
                          primary_key=True)
    followed_id=db.Column(db.Integer,db.ForeignKey('users.id'),
                          primary_key=True)
    timestamp=db.Column(db.DateTime,default=datetime.utcnow())

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    password_hash = db.Column(db.String(128))
    posts = db.relationship( 'Post', backref = 'author', lazy = 'dynamic' )
    confirmed = db.Column( db.Boolean, default = False )

    name=db.Column(db.String(64))
    about_me=db.Column(db.Text())
    member_since=db.Column(db.DateTime(),default=datetime.utcnow())
    last_seen=db.Column(db.DateTime(),default=datetime.utcnow())

    comments=db.relationship('Comment',backref='author',lazy='dynamic')

    followed=db.relationship('Follow',
                             foreign_keys=[Follow.follower_id],
                             backref=db.backref('follower',lazy='joined'),
                             lazy='dynamic',
                             cascade='all,delete-orphan')
    followers = db.relationship( 'Follow',
                                foreign_keys = [Follow.followed_id] ,
                                backref = db.backref( 'followed', lazy = 'joined' ),
                                lazy = 'dynamic',
                                cascade = 'all,delete-orphan')

    def __init__(self,**kwargs):
        super(User,self).__init__(**kwargs)#调用基类构造函数，如没有定义角色，则添加
        if self.role is None:
            if self.email==current_app.config["FLASKY_ADMIN"]:
                self.role=Role.query.filter_by(permissions=0xff).first()
            else:
                self.role=Role.query.filter_by(default=True).first()
        self.follow(self)#用户关注自己
    #把所有用户设为他自己的关注者
    @staticmethod
    def add_self_follows():
        for user in User.query.all():
            if not user.is_following(user):
                user.follow(user)
                db.session.add(user)
                db.session.commit()
    #获取关注的文章
    @property
    def followed_posts(self):
        return (Post.query.join( Follow, Follow.followed_id == Post.author_id )\
                .filter(Follow.follower_id==self.id))
    #关注关系的辅助方法
    def follow(self,user):
        if not self.is_following(user):
            f=Follow(follower=self,followed=user)
            db.session.add(f)
    def unfollow(self,user):
        f=self.followed.filter_by(followed_id=user.id).first()
        if f:
            db.session.delete(f)
    def is_following(self,user):
        return self.followed.filter_by(followed_id=user.id).first() is not None
    def is_followed_by(self,user):
        return self.followers.filter_by(follower_id=user.id).first() is not None

    #刷新最后访问时间
    def ping(self):
        self.last_seen=datetime.utcnow()
        db.session.add(self)
    #检查用户权限
    def can(self,permissions):
        return (self.role is not None) and ((self.role.permissions & permissions) ==permissions)
    def is_administrator(self):
        return self.can(Permission.ADMINISTER)

    #设置、验证密码
    @property
    def password( self ):
        raise AttributeError( 'password is not a readable attribute' )

    @password.setter
    def password( self, password ):
        self.password_hash = generate_password_hash( password )

    def verify_password( self, password ):
        return check_password_hash( self.password_hash, password )
    #创建、验证令牌
    def generate_confirmation_token( self, expiration = 3600 ):
        s = Serializer( current_app.config[ 'SECRET_KEY' ], expiration )
        return s.dumps( { 'confirm': self.id})

    def confirm( self, token ):
        s = Serializer( current_app.config[ 'SECRET_KEY' ] )
        try:
            data = s.loads( token )
        except:
            return False
        if data.get( 'confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add( self )
        return True

    #生成虚拟用户和虚拟博客文章
    @staticmethod
    def generate_fake(count=500):
        from sqlalchemy.exc import IntegrityError
        from random import seed
        import forgery_py

        seed()
        for i in range(count):
            u=User(email=forgery_py.internet.email_address(),
                   username=forgery_py.internet.user_name(True),
                   password=forgery_py.lorem_ipsum.word(),
                   confirmed=True,
                   name=forgery_py.name.full_name(),
                   about_me=forgery_py.lorem_ipsum.sentence(),
                   member_since=forgery_py.date.date(True))
            db.session.add(u)
            #用户名和电子邮件可能有重复值，需要回滚
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()

class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)
    users = db.relationship('User', backref='role', lazy='dynamic')

    @staticmethod#修改现有角色，添加权限
    def insert_roles():
        roles={
            "User":(Permission.FOLLOW|
                    Permission.COMMIT|
                    Permission.WRITE_ARTICLE,True),
            "Moderator":(Permission.FOLLOW|
                         Permission.COMMIT|
                         Permission.WRITE_ARTICLE|
                         Permission.MODERATE_COMMENTS,False),
            "Administrator":(0xff,False)
        }
        for r in roles:
            role=Role.query.filter_by(name=r).first()
            if role is None:
                role=Role(name=r)
            role.permissions=roles[r][0]
            role.default=roles[r][1]
            db.session.add(role)
        db.session.commit()

class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    body_html=db.Column(db.Text)

    comments=db.relationship('Comment',backref='post',lazy='dynamic')

    """生产虚拟文章"""
    @staticmethod
    def generate_fake( count = 500 ):
        from random import seed, randint
        import forgery_py

        seed( )
        user_count = User.query.count( )
        for i in range( count ):
            u = User.query.offset( randint( 0, user_count - 1 ) ).first( )#跳过
            p = Post( body = forgery_py.lorem_ipsum.sentences( randint( 1, 3 ) ),
                      timestamp = forgery_py.date.date( True ),
                      author = u )
            db.session.add( p )
            db.session.commit( )
    """生成markdown文本"""
    @staticmethod
    def on_changed_body(target,value,oldvalue,initiator):
        allowed_tags=['a','abbr','acronym','b',
                      'blockquote','code','em',
                      'i','li','ol','pre','strong',
                      'ul','h1','h2','h3','p']
        #把纯文本中url转换成适当的<a>标签
        target.body_html=bleach.linkify(bleach.clean(markdown(value,output_format="html"),
                                        tags=allowed_tags ,strip=True))
db.event.listen(Post.body,"set",Post.on_changed_body)#函数作为对象传入

class Comment(db.Model):
    __tablename__='comments'
    id=db.Column(db.Integer,primary_key=True)
    body=db.Column(db.Text)
    body_html=db.Column(db.Text)
    timestamp=db.Column(db.DateTime,index=True,default=datetime.utcnow())
    disabled=db.Column(db.Boolean)
    author_id=db.Column(db.Integer,db.ForeignKey('users.id'))
    post_id=db.Column(db.Integer,db.ForeignKey('posts.id'))

    @staticmethod
    def onchange_body(target,value,oldvalue,initiator):
        allowed_tags=['a','abbr','acronym','b','code','em','i','strong']
        target.body_html=bleach.linkify(bleach.clean(markdown(value,output_format='html'),
                                                     tags=allowed_tags,strip=True))
db.event.listen(Comment.body,'set',Comment.onchange_body)

class Permission():
    FOLLOW=0x01
    COMMIT=0x02
    WRITE_ARTICLE=0x04
    MODERATE_COMMENTS = 0x08
    ADMINISTER = 0x80


class AnoymousUser(AnonymousUserMixin):
    """继承自AnoymousUserMixin类，设为用户未登录时的current_user
        未登录的用户无法搜索到id(load_user)
    """
    def can(self,permissions):
        return False
    def is_administrator(self):
        return False

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

"""处理匿名用户用AnoymousUser类"""
login_manager.anonymous_user=AnoymousUser

if __name__ == "__main__":
    pass