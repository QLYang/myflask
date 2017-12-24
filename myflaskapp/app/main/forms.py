#!/usr/bin/env python
#-*-coding:utf-8-*-
from flask_wtf import FlaskForm
from wtforms import StringField,TextAreaField,SubmitField,BooleanField,SelectField
from wtforms.validators import Length,DataRequired,Regexp,Email,ValidationError
from ..model import Role,User
from flask_pagedown.fields import PageDownField

class EditProfileForm(FlaskForm):
    """用户级别资料编辑"""
    name=StringField("真实姓名",validators = [Length(0,64)])
    about_me=TextAreaField("个人简介",validators = [Length(0,64)])
    submit=SubmitField("提交")

class EditProfileAdminForm(FlaskForm):
    """管理员级别资料编辑"""
    email=StringField('邮箱',validators = [DataRequired(),Length(1,64),Email()])
    username=StringField('用户名',validators = [DataRequired(),Length(1,64),Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,'用户名不合法！')])
    confirmed=BooleanField('已认证')
    role=SelectField('Role',coerce = int)#将字符串转换为整数
    name=StringField('真实姓名',validators = [Length(0,64)])
    about_me=TextAreaField('个人简介')
    submit=SubmitField('提交')

    def __init__(self,user,*args,**kwargs):
        """构造函数接收用户对象为参数"""
        super(EditProfileAdminForm,self).__init__(*args,**kwargs)
        """SelectField必须在choice属性中设置各选项
        """
        self.role.choices=[(role.id,role.name)for role in Role.query.order_by(Role.name).all()]
        self.user=user

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first() and \
                field.data!=self.user.email:
            raise ValidationError('此邮箱已经注册！')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first() and \
                field.data!=self.user.username:
            raise ValidationError('用户名已被使用')

class PostForm(FlaskForm):
    body=PageDownField("写点儿什么...",validators = [DataRequired()])
    submit=SubmitField('发表')

class CommentForm(FlaskForm):
    body=StringField('',validators = [DataRequired()])
    submit=SubmitField('提交')

if __name__ == "__main__":
    pass