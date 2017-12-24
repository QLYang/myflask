#!/usr/bin/env python
#-*-coding:utf-8-*-
from flask import render_template,abort,flash,redirect,url_for,request,current_app,make_response
from . import main
from ..model import User,db,Role,Permission,Post,Comment,Follow
from flask_login import login_required,current_user,AnonymousUserMixin
from .forms import EditProfileForm,EditProfileAdminForm,PostForm,CommentForm
from ..decorators import admin_required,permission_required

@main.route('/',methods=['GET','POST'])
def index():
    """首页"""
    form=PostForm()
    """有权限的用户才能显示编辑文章表格"""
    if current_user.can(Permission.WRITE_ARTICLE)\
        and form.validate_on_submit():
        """author字段引用User
             current_user只是轻度包装
        """
        post=Post(body=form.body.data,author=current_user._get_current_object())
        db.session.add(post)
        return redirect(url_for('.index'))

    """显示用户关注的人的文章"""
    show_followed=False#匿名用户默认为False
    if current_user.is_authenticated:
        show_followed=bool(request.cookies.get('show_followed',''))
    if show_followed:
        query=current_user.followed_posts
    else:
        query=Post.query
    """所有博客按时序列出（分页）"""
    page = request.args.get( 'page', 1, type = int )#默认第一页
    #Pagination类对象 (flask-sqlalchemy)
    pagination = query.order_by( Post.timestamp.desc( ) ).paginate(page,#唯一必须的参数
                per_page = current_app.config[ 'FLASKY_POSTS_PER_PAGE' ],
                error_out = False )#超出范围时返回空列表
    posts = pagination.items
    return render_template('index.html',form=form,posts=posts,show_followed=show_followed,pagination=pagination)

@main.route('/all')
def show_all():
    resp=make_response(redirect(url_for('.index')+'#showed_all'))
    resp.set_cookie('show_followed','',max_age=30*24*60*60)
    return resp

@main.route('/followed')
@login_required
def show_followed():
    resp=make_response(redirect(url_for('.index')+'#showed_followed'))
    resp.set_cookie('show_followed','1',max_age=30*24*60*60)
    return resp

@main.route('/user/<username>')
def user(username):
    """用户资料页"""
    user=User.query.filter_by(username=username).first()
    if user is None:
        abort(404)
    page = request.args.get( 'page', 1, type = int )  # 默认第一页
    pagination = Post.query.filter_by(author=user).order_by( Post.timestamp.desc( ) ).\
        paginate( page,  # 唯一必须的参数
                per_page = current_app.config [
                'FLASKY_POSTS_PER_PAGE' ],
                error_out = False )  # 超出范围时返回空列表
    posts = pagination.items
    return render_template("user.html",user=user,posts=posts,pagination=pagination)

@main.route('/edit_profile',methods=['GET','POST'])
@login_required
def edit_profile():
    form=EditProfileForm()
    if form.validate_on_submit():
        current_user.name=form.name.data
        current_user.about_me=form.about_me.data
        db.session.add(current_user)
        flash("您的资料已变更")
        return redirect(url_for('main.user',username=current_user.username))
    form.name.data=current_user.name
    form.about_me.data=current_user.about_me
    return render_template('edit_profile.html',form=form)

@login_required
@admin_required
@main.route('/edit-profile/<int:id>',methods=['GET','POST'])
def edit_profile_admin(id):
    user=User.query.get_or_404(id)#查找不到就404
    form=EditProfileAdminForm(user=user)#传给构造函数
    if form.validate_on_submit():
        user.email=form.email.data
        user.username=form.username.data
        user.about_me=form.about_me.data
        user.confirmed=form.confirmed.data
        user.role=Role.query.get(form.role.data)#
        user.name=form.name.data
        db.session.add(user)
        flash('用户资料已变更')
        return redirect(url_for('main.user',username=user.username))
    form.email.data=user.email
    form.username.data=user.username
    form.confirmed.data=user.confirmed
    form.role.data=user.role_id#
    form.name.data=user.name
    form.about_me.data=user.about_me
    return render_template('edit_profile.html',form=form,user=user)

@main.route('/post/<int:id>',methods=['GET','POST'])
def post(id):
    """文章固定链接"""
    post=Post.query.get_or_404(id)
    form=CommentForm()
    if form.validate_on_submit():
        comment=Comment(body=form.body.data,
                        post=post,
                        author=current_user._get_current_object())
        db.session.add(comment)
        flash('评论已提交')
        return redirect(url_for('.post',id=post.id,page=-1))
    page=request.args.get('page',1,type=int)
    if page==-1:
        page=(post.comments.count()-1)/current_app.config['FLASKY_COMMENTS_PER_PAGE']+1
    pagination=post.comments.order_by(Comment.timestamp.asc()).paginate(
        page,per_page = current_app.config['FLASKY_COMMENTS_PER_PAGE'],
        error_out = False
        )
    comments=pagination.items
    return render_template('post.html',posts=[post],form=form,comments=comments,pagination=pagination)

@main.route('/edit/<int:id>',methods=['GET','POST'])
@login_required
def edit(id):
    """编辑文章"""
    post=Post.query.get_or_404(id)
    if current_user != post.author and \
            not current_user.can( Permission.ADMINISTER ):
        abort( 403 )
    form = PostForm( )
    if form.validate_on_submit( ):
        post.body = form.body.data
        db.session.add( post )
        flash( '文章已修改' )
        return redirect( url_for( '.post', id = post.id ) )
    form.body.data = post.body
    return render_template( 'edit_post.html', form = form )

@main.route('/moderate')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate():
    """评论管理"""
    page=request.args.get('page',1,type=int)
    pagination=Comment.query.order_by(Comment.timestamp.desc()).paginate(
        page,per_page = current_app.config['FLASKY_COMMENTS_PER_PAGE'],
        error_out = False)
    comments=pagination.items
    return render_template('moderate.html',comments=comments,
                           pagination=pagination,page=page)

@main.route('/moderate/enable/<int:id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_enable(id):
    comment=Comment.query.get_or_404(id)
    comment.disabled=False
    db.session.add(comment)
    return redirect(url_for('.moderate',page=request.args.get('page',1,type=int)))

@main.route('/moderate/disable/<int:id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_disable(id):
    comment=Comment.query.get_or_404(id)
    comment.disabled=True
    db.session.add(comment)
    return redirect(url_for('.moderate',page=request.args.get('page',1,type=int)))

@main.route('/follow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def follow(username):
    user=User.query.filter_by(username=username).first()
    if user is None:
        flash("非法用户")
        return redirect(url_for('.index'))
    if current_user.is_following(user):
        flash('你已经关注了这个用户')
        return redirect(url_for('.user',username=username))
    current_user.follow(user)
    flash('你刚刚关注了%s'%username )
    return redirect(url_for('.user',username=username))

@main.route('/unfollow/<username>')
@login_required
def unfollow(username):
    user = User.query.filter_by( username = username ).first()
    if user is None:
        flash( "非法用户" )
        return redirect( url_for( '.index' ) )
    print(type(user))
    if not current_user.is_following(user):
        flash('你还没有关注这个用户')
        return redirect(url_for('.user',username=username))
    current_user.unfollow(user)
    flash('您已取消了对 %s 的关注'% username)
    return redirect(url_for('.user',username=username))

@main.route('/followers/<username>')
def followers(username):
    user=User.query.filter_by(username=username).first()
    if user is None:
        flash('非法用户')
        return redirect(url_for('.index'))
    page=request.args.get('page',1,type=int)
    pagination=user.followers.order_by(Follow.timestamp.desc()).paginate(
        page,per_page = current_app.config['FLASKY_FOLLOWERS_PER_PAGE'],
        error_out = False
    )
    follows=[{'user':item.follower,'timestamp':item.timestamp}
             for item in pagination.items]
    return render_template('followers.html',user=user,title='谁关注ta',
                           endpoint='.followers',pagination=pagination,
                             follows =follows)

@main.route('/followed_by/<username>')
def followed_by(username):
    user=User.query.filter_by(username=username).first()
    if user is None:
        flash('非法用户')
        return redirect(url_for('.index'))
    page=request.args.get('page',1,type=int)
    pagination=user.followed.order_by(Follow.timestamp.desc()).paginate(
        page,per_page = current_app.config['FLASKY_FOLLOWERS_PER_PAGE'],
        error_out = False
    )
    followed=[{'user':item.followed,'timestamp':item.timestamp}
             for item in pagination.items]
    print(page,pagination.iter_pages())
    for i in pagination.iter_pages():
        print(i)
    return render_template('followers.html',user=user,title='ta关注的人',
                           endpoint='.followed_by',pagination=pagination,
                             follows =followed)
if __name__ == "__main__":
    pass