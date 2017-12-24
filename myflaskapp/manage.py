#!/usr/bin/env python
#-*-coding:utf-8-*-
import os
from app import create_app
from flask_script import Manager, Shell
from app.model import db,Post,User,Role
from flask_migrate import Migrate,MigrateCommand
import os

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
manager = Manager(app)
migrate=Migrate(app,db)

def make_shell_context():
    return dict(app=app, db=db, Post=Post,User=User,Role=Role)

manager.add_command("shell", Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)

@manager.command
def test(coverage=False):
    COV = None
    if coverage:
        import coverage
        COV=coverage.coverage(branch=True,include = 'app/*')
        COV.start()

    import unittest
    tests=unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity = 2).run(tests)
    if COV is not None:
        COV.stop()
        COV.save()
        print('测试覆盖报告')
        COV.report()
        basedir=os.path.abspath(os.path.dirname(__file__))#获得该文件所在文件夹
        covdir=os.path.join(basedir,'tmp/coverage')
        COV.html_report(directory = covdir)
        print('报告的HTML版本位于 %s'%covdir)
        COV.erase()


if __name__ == "__main__":
    manager.run( )