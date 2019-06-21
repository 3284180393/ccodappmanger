# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import models


# Create your models here.
class AppTemplate(models.Model):
    app_type = models.CharField(u'应用类型，例如oracle,mysql,slee等', max_length=40, null=False, blank=False)
    app_name = models.CharField(u'缺省应用的名称,例如oracle中的实例名', max_length=40, null=False, blank=False)
    app_alias = models.CharField(u'缺省应用的别名称,例如oracle中的别名,例如oracle中的db_unique_name', max_length=40, null=False, blank=False)
    server_name = models.CharField(u'如果应用对外提供服务缺省应用的服务名称,例如oracle中的别名,例如oracle中的service', max_length=40, null=True)
    base_path = models.CharField(u'缺省应用的base路径，例如$ORACLE_HOME，通过base路径可以使用相对路径去访问文件或是执行命令', max_length=512, null=False, blank=False)
    thread_filter_regex = models.CharField(u'缺省相关应用进程过滤正则表达式', max_length=100, null=True)
    relative_port = models.CharField(u'缺省应用关联端口,多个端口用;分割', max_length=40, null=True)
    profile = models.CharField(u'缺省应用的环境变量文件,多个文件用;分割', max_length=1024, null=True)
    cfg_file = models.CharField(u'缺省应用配置文件,多个配置文件用;分割', max_length=1024, null=True)
    log_file_dir = models.CharField(u'缺省应用日志文件所在目录', max_length=255, null=True)
    log_file_name = models.CharField(u'缺省当前正在使用日志文件名,多个日志文件用;分割', max_length=255, null=True)
    log_file_name_regex = models.CharField(u'缺省应用日志文件名正则表达式，用来匹配所有的应用的日志文件', max_length=512, null=True)
    include_dir = models.CharField(u'缺省不在base目录下且同应用关联的目录,多个目录用;分割', max_length=1024, null=True)
    ignore_dir = models.CharField(u'缺省在base目录下但无需关注的目录,多个目录用;分割', max_length=1024, null=True)
    ignore_ext = models.CharField(u'缺省应用base目录下无需关注的文件类型,多个ext用;分割', max_length=255, null=True)
    comment = models.CharField(u'备注', max_length=512, null=True)
    create_time = models.DateTimeField(u'创建时间', null=True)
    update_time = models.DateTimeField(u'最后一次修改时间', null=True)

    def __unicode__(self):
        return self.app_name

    class Meta:
        verbose_name = u'应用定义模板'
        verbose_name_plural = u'应用定义模板'


class Server(models.Model):
    host_ip = models.CharField(u'主机ip', max_length=40, null=False, blank=False)
    host_name = models.CharField(u'主机名', max_length=40, null=False, blank=False)
    server_type = models.IntegerField(u'服务器类型1、linux服务器，2、windows服务器')
    access_type = models.IntegerField(u'访问方式，1、ssh登录，2、通过蓝鲸agent访问')
    status = models.IntegerField(u'服务器当前状态，1、正常使用，2、不在使用，3、维修中')
    ssh_port = models.IntegerField(u'ssh登录端口')
    comment = models.CharField(u'备注', max_length=255, null=True)

    def __unicode__(self):
        return self.host_ip + '(' + self.host_name + ')'

    class Meta:
        verbose_name = u'应用服务器'
        verbose_name_plural = u'应用服务器'


class ServerUser(models.Model):
    server = models.ForeignKey(Server)
    login_name = models.CharField(u'用户登录名', max_length=40, null=False, blank=False)
    pass_word = models.CharField(u'用户登录密码', max_length=20, null=False, blank=False)

    def __unicode__(self):
        return self.login_name

    class Meta:
        verbose_name = u'服务器用户'
        verbose_name_plural = u'服务器用户'


# Create your models here.
class AppCfg(models.Model):
    app_template = models.ForeignKey(AppTemplate)
    server = models.ForeignKey(Server)
    root_user = models.ForeignKey(ServerUser, related_name='root_user')
    app_user = models.ForeignKey(ServerUser, related_name='app_user')
    app_type = models.CharField(u'应用类型，例如oracle,mysql,slee等', max_length=40, null=False, blank=False)
    app_name = models.CharField(u'应用的名称,例如oracle中的实例名', max_length=40, null=False, blank=False)
    app_alias = models.CharField(u'应用的别名称,例如oracle中的别名,例如oracle中的db_unique_name', max_length=40, null=False, blank=False)
    server_name = models.CharField(u'如果应用对外提供服务应用的服务名称,例如oracle中的别名,例如oracle中的service', max_length=40, null=True)
    base_path = models.CharField(u'应用的base路径，例如$ORACLE_HOME，通过base路径可以使用相对路径去访问文件或是执行命令', max_length=512, null=False, blank=False)
    thread_filter_regex = models.CharField(u'相关应用进程过滤正则表达式', max_length=100, null=True)
    relative_port = models.CharField(u'应用关联端口,多个端口用;分割', max_length=40, null=True)
    profile = models.CharField(u'应用的环境变量文件,多个文件用;分割', max_length=1024, null=True)
    cfg_file = models.CharField(u'应用配置文件,多个配置文件用;分割', max_length=1024, null=True)
    log_file_dir = models.CharField(u'应用日志文件所在目录', max_length=255, null=True)
    log_file_name = models.CharField(u'当前正在使用日志文件名,多个日志文件用;分割', max_length=255, null=True)
    log_file_name_regex = models.CharField(u'应用日志文件名正则表达式，用来匹配所有的应用的日志文件', max_length=512, null=True)
    include_dir = models.CharField(u'不在base目录下且同应用关联的目录,多个目录用;分割', max_length=1024, null=True)
    ignore_dir = models.CharField(u'在base目录下但无需关注的目录,多个目录用;分割', max_length=1024, null=True)
    ignore_ext = models.CharField(u'应用base目录下无需关注的文件类型,多个ext用;分割', max_length=255, null=True)
    comment = models.CharField(u'备注', max_length=512, null=True)
    create_time = models.DateTimeField(u'创建时间', null=True)
    update_time = models.DateTimeField(u'最后一次修改时间', null=True)

    def __unicode__(self):
        return self.app_name + '(' + self.app_alias + ')'

    class Meta:
        verbose_name = u'应用配置'
        verbose_name_plural = u'应用配置'


class Platform(models.Model):
    platform_id = models.CharField(u'平台id', max_length=40, null=False, blank=False, primary_key=True)
    platform_name = models.CharField(u'平台名', max_length=40, null=False, blank=False)
    status = models.IntegerField(u'平台状态1、启用,0、停用', default=1)
    comment = models.CharField(u'平台备注', max_length=255, null=True, blank=True)
    create_time = models.DateTimeField(u'创建时间', null=True)
    update_time = models.DateTimeField('最后一次修改时间', null=True)

    def __unicode__(self):
        return self.platform_name + '(' + self.platform_id + ')'

    class Meta:
        verbose_name = 'ccod平台'
        verbose_name_plural = 'ccod平台'


class Domain(models.Model):
    domain_id = models.CharField(u'域id', max_length=40, null=False, blank=False, primary_key=True)
    domain_name = models.CharField(u'域名', max_length=40, null=False, blank=False)
    platform = models.ForeignKey(Platform)
    status = models.IntegerField(u'域状态1、启用,0、停用', default=1)
    comment = models.CharField(u'域备注', max_length=255, null=True, blank=True)
    create_time = models.DateTimeField(u'创建时间', null=True)
    update_time = models.DateTimeField('最后一次修改时间', null=True)

    def __unicode__(self):
        return self.domain_name + '(' + self.domain_id + ')'

    class Meta:
        verbose_name = 'ccod域'
        verbose_name_plural = 'ccod域'


class AppPriStbyCfg(models.Model):
    app_template = models.ForeignKey(AppTemplate)
    platform = models.ForeignKey(Platform)
    domain = models.ForeignKey(Domain)
    primary_app = models.ForeignKey(AppCfg, related_name='pri_app')
    standby_app = models.ForeignKey(AppCfg, related_name='stby_app')
    nj_agent_server = models.ForeignKey(Server, related_name='nj_agent_server')
    nj_agent_user = models.ForeignKey(ServerUser, related_name='nj_agent_user')
    tag = models.CharField(u'主备配置标签', max_length=128, null=False, blank=False)
    availble_ip = models.CharField(u'同一网段中可以用来切换用的未被使用ip', max_length=40, null=False, blank=False)

    def __unicode__(self):
        return self.tag

    class Meta:
        verbose_name = '应用主备配置'
        verbose_name_plural = '应用主备配置'