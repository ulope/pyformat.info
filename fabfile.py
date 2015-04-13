from fabric.api import put, task, cd, env, local
from fabric.contrib.project import rsync_project

env.hosts = ['pyformat@pyformat.info']


@task
def generate():
    local("pyformat generate")


@task(default=True)
def deploy():
    with cd('/var/www/pyformat.info'):
        put('index.html', './')
    rsync_project('/var/www/pyformat.info/', 'assets')
