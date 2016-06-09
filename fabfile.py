from datetime import datetime
from fabric.api import task, env, settings, cd, sudo, run, local, put, path

stamp = datetime.now().strftime("v%Y%m%d%H%M%S")
stamptar = "hnfp-" + stamp + ".tar"
stampzip = stamptar + ".gz"

env.stamp = stamp
env.stamptar = stamptar
env.stampzip = stampzip

@task
def live():
    env.hosts = [
        "crow.endrun.org"
    ]

@task
def deploy():
    local('find . \( -name "*.pyc" -or -name "*.pyo" -or -name "*py.class" \) -delete')

    local('tar cf %(stamptar)s _requirements/' % env)
    local('tar rf %(stamptar)s firebase/' % env)
    local('tar rf %(stamptar)s frontpage/' % env)
    local('tar rf %(stamptar)s services/' % env)
    local('tar rf %(stamptar)s main.py' % env)
    local('tar rf %(stamptar)s run.sh' % env)
    local('gzip %(stamptar)s' % env)

    put(stampzip, '/tmp/%(stampzip)s' % env)

    local('rm %(stampzip)s' % env)

    with settings(sudo_user='hn_frontpage'):

        with cd('/home/hn_frontpage/run'):
            sudo('mkdir -p %(stamp)s/src' % env)
            sudo('mkdir -p %(stamp)s/venv' % env)

        with cd('/home/hn_frontpage/run/%(stamp)s' % env):
            sudo('tar xfz /tmp/%(stampzip)s -C ./src/' % env)

    sudo('rm /tmp/%(stampzip)s' % env)

    with settings(sudo_user='hn_frontpage'):

        with cd('/home/hn_frontpage/run/%(stamp)s' % env):
            sudo('virtualenv venv -p $(pyenv prefix 2.7.11)/bin/python' % env)

            with path('./venv/bin', behavior='prepend'):
                sudo('pip install --quiet --no-cache-dir -r ./src/_requirements/default.txt' % env)

        with cd('/home/hn_frontpage/run/current/src/'):
            sudo('./run.sh stop')

        with cd('/home/hn_frontpage/run'):
            sudo('ln -nsf $(basename $(readlink -f current)) previous' % env)
            sudo('ln -nsf %(stamp)s current' % env)

        with cd('/home/hn_frontpage/run/current/src/'):
            sudo('./run.sh start')

@task
def clean():
    with settings(sudo_user='hn_frontpage'):
        with cd('/home/hn_frontpage/run'):
            sudo('current=$(basename $(readlink -f current)) && previous=$(basename $(readlink -f previous)) && for dir in $(ls -dt */ | egrep -v "current|previous|$current|$previous"); do rm -r $dir; done')
