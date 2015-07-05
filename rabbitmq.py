# coding: utf-8

from fabkit import sudo
from fablib.base import SimpleBase


class RabbitMQ(SimpleBase):

    def __init__(self):
        self.data_key = 'rabbitmq'
        self.data = {}
        self.services = {
            'CentOS 7.*': ['rabbitmq-server']
        }
        self.packages = {
            'CentOS 7.*': [
                'epel-release',
                {
                    'name': 'rabbitmq-server-3.5.2',
                    'path': 'https://www.rabbitmq.com/releases/rabbitmq-server/v3.5.2/rabbitmq-server-3.5.2-1.noarch.rpm',  # noqa
                },
            ]
        }

    def setup(self):
        data = self.init()
        self.install_packages()
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
