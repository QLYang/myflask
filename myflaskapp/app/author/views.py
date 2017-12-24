#!/usr/bin/env python
#-*-coding:utf-8-*-
from flask import render_template,redirect,url_for,flash,request
from . import auth
from .forms import loginForm
from ..model import User,db
from flask_login import login_user,logout_user,login_required,current_user
from ..email import send_email
from .forms import RegistrationForm

@auth.route('/login',methods=["GET","POST"])
def login():
    form=loginForm()
    if form.validate_on_submit():
        user=User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user,form.rememberme.data)
            return redirect(request.args.get("next") or url_for("main.index"))
        flash("输入无效！不存在的用户")
    return render_template('auth/login.html',form=form)

@auth.route("/logout")
@login_required
def logout():
    logout_user()
    flash("您已经退出")
    return redirect( url_for( 'main.index' ) )

@auth.route('/register', methods = ['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data,
                    username=form.username.data,
                    password=form.password.data)
        db.session.add(user)
        db.session.commit()
        token = user.generate_confirmation_token()
        send_email(user.email, '验证您的账户',
                   'auth/email/confirm', user=user, token=token)
        flash('验证邮件已经发到您的邮箱')
        login_user(user)
        return redirect(url_for('main.index'))
    return render_template('auth/register.html', form=form)

@auth.route("/confirm/<token>")
@login_required
def confirm(token):
    if current_user.confirmed:#用current_user获取User模型(需要登陆)
        return redirect( url_for( 'main.index' ) )
    if current_user.confirm( token ):
        flash( '您的账号已确认，谢谢！')
    else:
        flash( '确认链接已过期')
    return redirect( url_for( 'main.index' ) )

@auth.before_app_request#获取权限时需要确认账户,若未确认，则跳转到/unconfirmed
def before_request():
    if current_user.is_authenticated :
        current_user.ping()#刷新用户访问时间
        if not current_user.confirmed \
            and request.endpoint [ :5 ] != 'auth.'\
            and request.endpoint != 'static':
            return redirect( url_for( 'auth.unconfirmed'))

@auth.route("/unconfirmed")
@login_required
def unconfirmed():
    if current_user.is_anonymous or current_user.confirmed:
        return redirect( url_for( 'main.index' ) )
    return render_template( 'auth/unconfirmed.html',user=current_user)#"点击此链接确认账户"

@auth.route("/confirm")#重新发送确认邮件
@login_required
def resend_confirmation():
    token = current_user.generate_confirmation_token( )
    send_email( current_user.email, '确认您的账户','auth/email/confirm',\
                user=current_user, token=token)
    flash( '确认链接已发送到您的邮箱！' )
    return redirect( url_for( 'main.index' ) )

if __name__ == "__main__":
    pass