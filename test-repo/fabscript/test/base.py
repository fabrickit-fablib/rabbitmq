# coding: utf-8

from fabkit import task
from fablib.rabbitmq import RabbitMQ

rabbitmq = RabbitMQ()


@task
def setup():
    rabbitmq.setup()
