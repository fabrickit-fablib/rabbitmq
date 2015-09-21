# coding: utf-8

import socket
from fabkit import sudo, filer, env, Editor, api
from fablib.base import SimpleBase


class RabbitMQ(SimpleBase):

    def __init__(self):
        self.data_key = 'rabbitmq'
        self.data = {}
        self.services = {
            'CentOS Linux 7.*': ['rabbitmq-server']
        }
        self.packages = {
            'CentOS Linux 7.*': [
                'epel-release',
                {
                    'name': 'rabbitmq-server-3.5.2',
                    'path': 'https://www.rabbitmq.com/releases/rabbitmq-server/v3.5.2/rabbitmq-server-3.5.2-1.noarch.rpm',  # noqa
                },
            ]
        }

    def init_after(self):
        for cluster in self.data.values():
            if env.host in cluster['hosts']:
                self.data['rabbitmq_cluster'] = cluster
                break

    def setup(self):
        self.init()
        cluster = self.data['rabbitmq_cluster']

        if self.is_tag('package'):
            self.install_packages()

        if self.is_tag('conf'):
            filer.template('/var/lib/rabbitmq/.erlang.cookie',
                           src_str=cluster['cookie'],
                           mode='400',
                           owner='rabbitmq:rabbitmq')

            etc_hosts = Editor('/etc/hosts')
            for i, host in enumerate(cluster['hosts']):
                ip = socket.gethostbyname(host)
                etc_hosts.a('{0} rabbit{1}'.format(ip, i))

            node_index = cluster['hosts'].index(env.host)
            nodename = 'rabbit@rabbit{0}'.format(node_index)
            filer.template('/etc/rabbitmq/rabbitmq-env.conf',
                           src_str='NODENAME={0}'.format(nodename),
                           mode='644',
                           owner='rabbitmq:rabbitmq')

        if self.is_tag('service'):
            self.enable_services().start_services()

        if self.is_tag('data'):
            sudo('rabbitmq-plugins enable rabbitmq_management')

            if nodename == 'rabbit@rabbit0':
                result = sudo('rabbitmqctl list_vhosts | grep -v Listing')
                vhosts = result.split('\r\n')
                for vhost in cluster['vhosts'].values():
                    if vhost not in vhosts:
                        sudo('rabbitmqctl add_vhost {0}'.format(vhost))

                result = sudo('rabbitmqctl list_users | grep -v Listing | awk \'{print $1}\'')
                users = result.split('\r\n')
                if 'guest' in users:
                    sudo('rabbitmqctl delete_user guest')

                for user in cluster['users'].values():
                    if user['user'] not in users:
                        sudo('rabbitmqctl add_user {0[user]} {0[password]}'.format(user))
                    for permission in user['permissions']:
                        sudo('rabbitmqctl set_permissions -p {1[vhost]} {0[user]} {1[permissions]}'.format(user, permission))  # noqa

    def setup_cluster(self):
        if self.is_tag('data'):
            self.init()
            cluster = self.data['rabbitmq_cluster']

            if env.host == cluster['hosts'][0]:
                for vhost in cluster['vhosts'].values():
                    sudo('rabbitmqctl set_policy all \'^.*\' \'{{"ha-mode": "all"}}\' -p {0}'.format(vhost))  # noqa
            else:
                with api.warn_only():
                    result = sudo('rabbitmqctl cluster_status | grep rabbit@rabbit0')
                if result.return_code != 0:
                    sudo('rabbitmqctl stop_app')
                    sudo('rabbitmqctl reset')
                    sudo('rabbitmqctl join_cluster rabbit@rabbit0')
                    sudo('rabbitmqctl start_app')
