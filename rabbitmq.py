# coding: utf-8

import re
from fabkit import sudo, Package, env
from fablib.base import SimpleBase

re_centos6 = re.compile('CentOS 6.*')
re_centos7 = re.compile('CentOS 7.*')


class RabbitMQ(SimpleBase):

    def __init__(self):
        self.data_key = 'rabbitmq'
        self.data = {

        }
        self.services = {
            'CentOS[67].*': ['rabbitmq-server']
        }

    def setup(self):
        data = self.get_init_data()

        if re_centos6.match(env.node['os']):
            Package('epel-release').install(
                'http://dl.fedoraproject.org/pub/epel/7/x86_64/e/epel-release-7-5.noarch.rpm')
        elif re_centos7.match(env.node['os']):
            Package('epel-release').install()

        Package('rabbitmq-server-3.5.2').install('https://www.rabbitmq.com/releases/rabbitmq-server/v3.5.2/rabbitmq-server-3.5.2-1.noarch.rpm')  # noqa
        self.enable_services().start_services()
        sudo('rabbitmqctl status')
        sudo('rabbitmq-plugins enable rabbitmq_management')

        result = sudo('rabbitmqctl list_vhosts | grep -v Listing')
        vhosts = result.split('\r\n')
        for vhost in data['vhosts'].values():
            if vhost not in vhosts:
                sudo('rabbitmqctl add_vhost {0}'.format(vhost))

        result = sudo('rabbitmqctl list_users | grep -v Listing | awk \'{print $1}\'')
        users = result.split('\r\n')
        if 'guest' in users:
            sudo('rabbitmqctl delete_user guest')

        for user in data['users'].values():
            if user['user'] not in users:
                sudo('rabbitmqctl add_user {0[user]} {0[password]}'.format(user))
            for permission in user['permissions']:
                sudo('rabbitmqctl set_permissions -p {1[vhost]} {0[user]} {1[permissions]}'.format(
                    user, permission))
