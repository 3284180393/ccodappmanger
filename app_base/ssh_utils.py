# -*- coding: utf-8 -*-
from fabric.api import *
from datetime import datetime
from common.log import logger


def create_connection(host_ip, ssh_port, user, password):
    """
    创建一个ssh连接
    :param host_ip:主机ip
    :param ssh_port: ssh端口
    :param user: 登录用户
    :param password: 登录密码
    :return: 如果创建连接成功返回连接，连接超时返回'TIMEOUT'，如果认证失败返回"AUTH_FAIL"
    """
    logger.info("准备创建ssh连接,host_p=%s,ssh_port=%d,user=%s,password=%s" %(host_ip, ssh_port, user, password))



