#!/usr/bin/env python
#-*-coding:utf-8-*-
"""蓝本"""
from flask import Blueprint
from ..model import Permission

main = Blueprint('main', __name__)
from . import views, errors

@main.app_context_processor#在模板中创建Permission的上下文
def inject_permission():
    return dict(Permission=Permission)

if __name__ == "__main__":
    pass