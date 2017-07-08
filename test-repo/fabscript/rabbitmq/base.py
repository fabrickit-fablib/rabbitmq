# coding: utf-8

from fabkit import task, parallel
from fablib.rabbitmq import RabbitMQ


@task
@parallel
def setup():
    rabbitmq = RabbitMQ()
    rabbitmq.setup()


@task
def setup_cluster():
    rabbitmq = RabbitMQ()
    rabbitmq.setup_cluster()
