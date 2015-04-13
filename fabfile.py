from fabric.api import put, task, cd, env
from fabric.contrib.project import rsync_project


env.hosts = ['pyformat@pyformat.info']


@task
def deploy():
    with cd('/var/www/pyformat.info'):
        put('index.html', './')
    rsync_project('/var/www/pyformat.info/', 'assets')
