# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making 蓝鲸智云(BlueKing) available.
Copyright (C) 2017 THL A29 Limited, a Tencent company. All rights reserved.
Licensed under the MIT License (the "License"); you may not use this file except in compliance with the License.
You may obtain a copy of the License at http://opensource.org/licenses/MIT
Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on
an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and limitations under the License.
"""

from common.mymako import render_mako_context
from django.http import HttpResponse
from app_base.models import AppPriStbyCfg
from oracle.dg_switch import check_dg_oracle_status
from oracle.dg_switch import start_pri_stby_switch
import json


def home(request):
    """
    首页
    """
    return render_mako_context(request, '/home_application/home.html')


def dev_guide(request):
    """
    开发指引
    """
    return render_mako_context(request, '/home_application/dev_guide.html')


def contactus(request):
    """
    联系我们
    """
    return render_mako_context(request, '/home_application/contact.html')


def get_app_pri_stby_cfg(request, platform_id, app_type):
    """
    获取某个平台的某个应用类型的所有主备配置
    :param request: http请求
    :param platform_name: 平台名
    :param app_type:应用类型
    :return:查询结果
    """
    query_list = AppPriStbyCfg.objects.filter(platform__platform_id=platform_id, app_template__app_type=app_type)
    ret_list = list()
    for cfg in query_list:
        app_cfg = dict()
        app_cfg['platform_name'] = cfg.platform.platform_name
        app_cfg['platform_id'] = cfg.platform.platform_id
        app_cfg['app_template_id'] = cfg.app_template.id
        app_cfg['app_type'] = cfg.app_template.app_type
        app_cfg['domain_name'] = cfg.domain.domain_name
        app_cfg['domain_id'] = cfg.domain.domain_id
        app_cfg['nj_agent_host_ip'] = cfg.nj_agent_server.host_ip
        app_cfg['nj_agent_host_name'] = cfg.nj_agent_server.host_name
        app_cfg['nj_agent_server_id'] = cfg.nj_agent_server.id
        app_cfg['nj_agent_user'] = cfg.nj_agent_user.login_name
        app_cfg['nj_agent_user_password'] = cfg.nj_agent_user.pass_word
        app_cfg['nj_agent_user_id'] = cfg.nj_agent_user.id
        app_cfg['available_ip'] = cfg.available_ip
        app_cfg['primary_app_cfg'] = __get_app_config(cfg.primary_app)
        app_cfg['standby_app_cfg'] = __get_app_config(cfg.standby_app)
        ret_list.append(app_cfg)
    return HttpResponse(json.dumps(ret_list, ensure_ascii=False), content_type="application/json,charset=utf-8")


def get_app_pri_stby_status(request, cfg_id):
    app_pri_stby_cfg = AppPriStbyCfg.objects.get(id=cfg_id)
    if not app_pri_stby_cfg:
        return HttpResponse('错误的主备配置id', content_type="application/json,charset=utf-8")
    pri_ora_cfg = __get_app_config(app_pri_stby_cfg.primary_app)
    stby_ora_cfg = __get_app_config(app_pri_stby_cfg.standby_app)
    ora_dg_status = check_dg_oracle_status(pri_ora_cfg, stby_ora_cfg)
    return HttpResponse(json.dumps(ora_dg_status, ensure_ascii=False), content_type="application/json,charset=utf-8")


def start_pri_stby_switch(request, app_pri_stby_cfg_id, switch_method):
    app_pri_stby_cfg = AppPriStbyCfg.objects.get(id=app_pri_stby_cfg_id)
    if app_pri_stby_cfg:
        return HttpResponse('错误的主备配置id', content_type="application/json,charset=utf-8")
    pri_ora_cfg = __get_app_config(app_pri_stby_cfg.primary_app)
    stby_ora_cfg = __get_app_config(app_pri_stby_cfg.standby_app)
    ret = start_pri_stby_switch(pri_ora_cfg, stby_ora_cfg, switch_method, app_pri_stby_cfg.availble_ip)
    return ret


def __get_app_config(app_cfg):
    """
    将数据库存储的应用配置转换成容易使用的dict()
    :param app_cfg: 数据库存储的应用配置
    :return: 易于使用的用dict类型应用配置
    """
    cfg = dict()
    cfg['app_template_id'] = app_cfg.app_template.id
    cfg['app_type'] = app_cfg.app_type
    cfg['app_name'] = app_cfg.app_name
    cfg['app_alias'] = app_cfg.app_alias
    cfg['base_path'] = app_cfg.base_path
    cfg['host_ip'] = app_cfg.server.host_ip
    cfg['host_name'] = app_cfg.server.host_name
    cfg['root_user'] = app_cfg.root_user.login_name
    cfg['root_password'] = app_cfg.root_user.pass_word
    cfg['app_user'] = app_cfg.app_user.login_name
    cfg['app_user_password'] = app_cfg.app_user.pass_word
    cfg['app_cfg_id'] = app_cfg.id
    cfg['server_id'] = app_cfg.server.id
    cfg['root_user_id'] = app_cfg.root_user.id
    cfg['app_user_id'] = app_cfg.app_user.id
    cfg['service_name'] = app_cfg.service_name
    cfg['ssh_port'] = app_cfg.server.ssh_port
    return cfg
