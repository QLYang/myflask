#!/usr/bin/env python
#-*-coding:utf-8-*-
from flask_wtf import FlaskForm
from wtforms import PasswordField,StringField,SubmitField,BooleanField
from wtforms.validators import DataRequired,Length,Email,EqualTo,Regexp
from ..model import User
from wtforms import ValidationError

class loginForm(FlaskForm):
    email=StringField("邮箱",validators = [DataRequired(),Length(1,64),Email()])
    password=PasswordField("密码",validators = [DataRequired(),])
    rememberme=BooleanField("记住我")
    submit=SubmitField("确定")

class RegistrationForm(FlaskForm):
    email = StringField('邮箱', validators=[DataRequired(), Length(1, 64),
                                             Email()])
    username = StringField('用户名', validators=[DataRequired(), Length(1, 64), Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
                                          'Usernames must have only letters, '
                                          'numbers, dots or underscores')])
    password = PasswordField('密码', validators=[DataRequired(), EqualTo('password2', message='密码不匹配')])
    password2 = PasswordField('再次输入密码', validators=[DataRequired()])
    submit = SubmitField('注册')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('此邮箱已经注册！')
    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('用户名已被使用')

if __name__ == "__main__":
    pass