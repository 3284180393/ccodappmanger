# -*- coding: utf-8 -*-

import sys
import logging as logger
import datetime
import re
import subprocess
import json
import signal,functools
class TimeoutError(Exception):pass
import paramiko
from paramiko.ssh_exception import AuthenticationException
reload(sys)
sys.setdefaultencoding('utf8')
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
logger.basicConfig(filename='my.log', level=logger.DEBUG, format=LOG_FORMAT)

stby_cfg = {'app_user_password': u'oracle', 'app_type': u'oracle', 'app_name': u'ccod', 'service_name': u'db_wending', 'server_id': 1, 'host_ip': u'10.130.41.159', 'base_path': u'/home/oracle/oracle10g/product/10.2.0/oracle/db_1', 'app_template_id': 1, 'app_alias': u'WENDING', 'root_user_id': 1, 'app_user_id': 2, 'host_name': u'ccod-oracle5', 'app_cfg_id': 1, 'app_user': u'oracle', 'root_password': u'123456', 'root_user': u'root', 'ssh_port': 22}
pri_cfg = {'app_user_password': u'oracle', 'app_type': u'oracle', 'app_name': u'ccod', 'service_name': u'db_phystdby', 'server_id': 2, 'host_ip': u'10.130.41.161', 'base_path': u'/home/oracle/oracle10g/product/10.2.0/db_1', 'app_template_id': 1, 'app_alias': u'PHYSTDBY', 'root_user_id': 3, 'app_user_id': 4, 'host_name': u'localhost','app_cfg_id': 2, 'app_user': u'oracle', 'root_password': u'123456', 'root_user': u'root', 'ssh_port': 22}


default_exec_command_timeout = 10
ssh_connect_timeout = 20
script_24_support_version = '^Python 2\.4\.3$'
script_26_support_version = '^Python 2\.6\.6$'
script_3_support_version = '||'
ip_regex = '.*(2(5[0-5]{1}|[0-4]\\d{1})|[0-1]?\\d{1,2})\\.(2(5[0-5]{1}|[0-4]\\d{1})|[0-1]?\\d{1,2})\\.(2(5[0-5]{1}|[0-4]\\d{1})|[0-1]?\\d{1,2})\\.(2(5[0-5]{1}|[0-4]\\d{1})|[0-1]?\\d{1,2}).*'


def timeout(seconds, error_message="Timeout Error: the cmd 30s have not finished."):
    def decorated(func):
        result = ""

        def _handle_timeout(signum, frame):
            global result
            result = error_message
            raise TimeoutError(error_message)

        def wrapper(*args, **kwargs):
            global result
            signal.signal(signal.SIGALRM, _handle_timeout)
            signal.alarm(seconds)

            try:
                result = func(*args, **kwargs)
            finally:
                signal.alarm(0)
                return result
            return result

        return functools.wraps(func)(wrapper)

    return decorated


def __ping_test(host_ip):
    """
    ping一个ip检查该ip是否可以ping通
    :param host_ip: 需要被ping的ip
    :return: SUCC该ip可以ping通，FAIL该ip无法ping通
    """
    logger.info("准备ping ip:" + host_ip)
    ret = {}
    command = 'ping ' + host_ip + ' -c 4'
#    command = 'ping ' + host_ip
    key = 'PING'
    ret['startTime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    ret['command'] = command
    ret['desc'] = '服务器是否在线'
    ret['key'] = key
    ret['command_type'] = 'local/runtime'
    ret['exec_success'] = False
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = process.communicate()[0]
    if process.stdin:
        process.stdin.close()
    if process.stdout:
        process.stdout.close()
    if process.stderr:
        process.stderr.close()
    try:
        process.kill()
    except OSError:
        pass
    command_result = out.decode()
#    command_result = out.decode('gbk')
    str_info = re.compile("(\n)*$")
    command_result = str_info.sub('', command_result)
    ret['endTime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    ret['output'] = command_result
    if re.match(".*ttl=.*", command_result, re.DOTALL) and re.match(".*time=.*", command_result, re.DOTALL):
        ret[key] = 'PING_SUCC'
        ret['exec_success'] = True
    else:
        ret[key] = 'PING_FAIL'
    logger.info("ping " + host_ip + "result : " + ret[key])
    return ret


@timeout(ssh_connect_timeout, "Timeout Error:fail to create connection in " + str(ssh_connect_timeout) + " seconds")
def __create_ssh_connect(host_ip, ssh_port, user, password):
    logger.info("创建ssh连接host_ip=%s, ssh_port=%d, user=%s, password=%s" % (host_ip, ssh_port, user, password))
    ret = {}
    command = 'create ssh connect for ' + user + '@' + host_ip
    key = 'CREATE_SSH_CONNECT'
    ret['startTime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    ret['command'] = command
    ret['desc'] = '为' + user + '创建ssh连接'
    ret['key'] = key
    ret['exec_success'] = False
    ret[key] = 'CREATE_CONN_FAIL'
    ssh_client = None
    try:
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(host_ip, ssh_port, user, password)
        ret['output'] = "create ssh connect for " + user + ":SUCC"
        ret[key] = 'CREATE_CONN_SUCCESS'
        ret['exec_success'] = True
    except AuthenticationException, ae:
        logger.error(user + '登录' + host_ip + '认证失败', ae)
        ret['output'] = str(ae)
        ret[key] = 'AUTH_FAIL'
    except Exception, e:
        logger.error(user + '登录' + host_ip + '失败', e)
        ret['output'] = str(e)
        ret[key] = 'FAIL'
    ret['endTime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    logger.info('ssh连接创建结果:' + ret[key])
    return ret, ssh_client


def command_result_regex_match(command_result, regex, command_type='bash/shell'):
    """
    解析命令输出结果是否满足某个正则表达式，所有的命令结果在解析前需要删掉空行,命令输出结果的最后一个\n也要被去掉,
    bash/shell类型采用多行模式进行匹配,oracle/sql则需要把所有结果拼成一行进行匹配，特别注意的是在拼成一行之前需要把每行前面的空格去掉
    :param command_result:
    :param regex:
    :param command_type:
    :return:
    """
    input_str = re.compile('\s+\n').sub('\n', command_result)
    input_str = re.compile('\n{2,}').sub('\n', input_str)
    input_str = re.compile('\n$').sub('', input_str)
    input_str = re.compile('^\n').sub('', input_str)
    if command_type == 'bash/shell':
        if re.match(regex, input_str, flags=re.DOTALL):
            return True
        else:
            return False
    elif command_type == 'oracle/sql':
        input_str = re.compile('^\s+').sub('', input_str)
        input_str = re.compile('\n').sub('', input_str)
        if re.match(regex, input_str):
            return True
        else:
            return  False
    else:
        logger.error('目前还不支持' + command_type + '类型命令结果解析')
        return False


@timeout(default_exec_command_timeout, error_message="in " + str(default_exec_command_timeout) + " without command return")
def __timeout_exec_command(conn, command, key, result_regex_map, desc, script_type='bash/shell'):
    """
    通过ssh在linux服务器上执行一条命令，命令执行结果会匹配result_regex_map中的正则，
    如果能够匹配某个正则那么返回的key等于正则表达式对应的关键字否则返回失败
    装饰器控制函数决定了执行命令的超时时长
    :param conn: ssh连接会话
    :param command: 需要执行的命令
    :param key: 执行结果对应的key
    :param result_regex_map: 配置命令执行结果的正则表达式
    :param desc: 命令描述
    :param script_type: 命令类型，目前支持bash/shell和oracle/sql
    :return: {'output', 'command', 'key', key, 'desc', 'output', 'startTime', 'endTime'}
    """
    ret = dict()
    ret['startTime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    stdin, stdout, stderr = conn.exec_command('. ./.bash_profile;' + command)
    exec_result = stdout.read()
    err = stderr.read()
    if err:
        exec_result = err
    ret['out'] = exec_result
    logger.info(command + ' exec result:' + ret['out'])
    ret['output'] = result
    ret['command'] = command
    ret['key'] = key
    ret['desc'] = desc
    ret['exec_success'] = False
    ret[key] = 'UNKNOWN'
    for k, v in result_regex_map.iteritems():
        if command_result_regex_match(exec_result, v, script_type):
            logger.info("命令输出结果满足正则表达式:" + v + "," + key + "将返回" + k)
            ret[key] = k
            ret['exec_success'] = True
            break
    ret['endTime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    logger.info('命令执行结果exec_success=' + str(ret['exec_success']) + '输出关键字' + key + '=' + ret[key])
    return ret


def __exec_command(conn, command, key, result_regex_map, desc, command_type):
    """
    通过ssh在linux服务器上执行一条命令，命令执行结果会匹配result_regex_map中的正则，
    如果能够匹配某个正则那么返回的key等于正则表达式对应的关键字否则返回失败
    :param conn: ssh连接会话
    :param command: 需要执行的命令
    :param key: 执行结果对应的key
    :param result_regex_map: 配置命令执行结果的正则表达式
    :param desc: 命令描述
    :param command_type: 脚本类型目前只支持bash/shell和oracle/sql两类
    :return: {'output', 'command', 'key', key, 'desc', 'output', 'startTime', 'endTime'}
    """
    ret = dict()
    ret['startTime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    stdin, stdout, stderr = conn.exec_command('. ./.bash_profile;' + command)
    exec_result = stdout.read()
    err = stderr.read()
    if err:
        exec_result = err
    ret['out'] = exec_result
    logger.info(command + ' exec result:' + ret['out'])
    ret['output'] = result
    ret['command'] = command
    ret['key'] = key
    ret['desc'] = desc
    ret['exec_success'] = False
    ret[key] = 'UNKNOWN'
    for k,v in result_regex_map.iteritems():
        if command_result_regex_match(exec_result, v, command_type):
            logger.info("命令输出结果满足正则表达式:" + v + "," + key + "将返回" + k)
            ret[key] = k
            ret['exec_success'] = True
            break
    ret['endTime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    logger.info('命令执行结果exec_success=' + str(ret['exec_success']) + '输出关键字' + key + '=' + ret[key])
    return ret


def __exec_check(conn, check_item):
    """
    在目标机器上执行某项检查
    :param conn: 连接目标机器的ssh连接
    :param check_item: 需要检查的内容
    :return: 检查结果,返回结果包含：执行命令ret['key'],执行检查项的key以及对应的结果ret['key']、ret[key],执行描述ret['desc']
    是否执行检查成功ret['exec_success'],用来执行的命令类型ret['command_type']，执行检查的开始时间和结束时间ret['startTime'], ret['endTime']
    """
    logger.info('开始执行某项检查,检查内容:' + str(check_item))
    command = check_item['command']
    key = check_item['key']
    desc = check_item['desc']
    result_regex_map = check_item['result_regex_map']
    command_type = check_item['command_type']
    exec_ret = dict()
    exec_ret['startTime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    exec_ret['command'] = command
    exec_ret['key'] = key
    exec_ret['desc'] = desc
    exec_ret['command_type'] = command_type
    exec_ret['exec_success'] = False
    try:
        if [check_item['timeout']]:
            exec_ret = __timeout_exec_command(conn, command, key, result_regex_map, desc, command_type)
        else:
            exec_ret = __exec_check(conn, command, key, result_regex_map, desc, command_type)
    except Exception, err:
        logger.error(desc + "检查异常", err)
        exec_ret['output'] = str(err)
        exec_ret[key] = 'FALSE'
    print(check_item['accept_result'])
    print(exec_ret[key])
    if re.match(check_item['accept_result'], exec_ret[key]):
        exec_ret['exec_success'] = True
    exec_ret['endTime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    logger.info(desc + " check result:" + key + "=" + exec_ret[key] + ',exec_success=' + str(exec_ret['exec_success']))
    return exec_ret


def __timeout_exec_check(conn, check_item):
    """
    在目标机器上执行某项检查
    :param conn: 连接目标机器的ssh连接
    :param check_item: 需要检查的内容
    :return: 检查结果,返回结果包含：执行命令ret['key'],执行检查项的key以及对应的结果ret['key']、ret[key],执行描述ret['desc']
    是否执行检查成功ret['exec_success'],用来执行的命令类型ret['command_type']，执行检查的开始时间和结束时间ret['startTime'], ret['endTime']
    """
    logger.info('开始执行某项检查,检查内容:' + str(check_item))
    command = check_item['command']
    key = check_item['key']
    desc = check_item['desc']
    result_regex_map = check_item['result_regex_map']
    command_type = check_item['command_type']
    exec_ret = dict()
    exec_ret['startTime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    exec_ret['command'] = command
    exec_ret['key'] = key
    exec_ret['desc'] = desc
    exec_ret['command_type'] = command_type
    exec_ret['exec_success'] = False
    try:
        if [check_item['timeout']]:
            exec_ret = __timeout_exec_command(conn, command, key, result_regex_map, desc, command_type)
        else:
            exec_ret = __exec_check(conn, command, key, result_regex_map, desc, command_type)
    except TimeoutError, detail:
        logger.error(desc + "检查超时", detail)
        exec_ret['output'] = str(detail)
        exec_ret[key] = 'TIMEOUT'
    except Exception, err:
        logger.error(desc + "检查异常", err)
        exec_ret['output'] = str(err)
        exec_ret[key] = 'FALSE'
    print(json.dump(exec_ret, ensure_ascii=False))
    if re.match(check_item['accept_result'], exec_ret[key]):
        exec_ret['exec_success'] = True
    exec_ret['endTime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    logger.info(desc + " check result:" + key + "=" + exec_ret[key] + ',exec_success=' + str(exec_ret['exec_success']))
    return exec_ret


def check_dg_primary_oracle_status(pri_ora_cfg, stby_ora_cfg):
    dg_status_ret = dict()
    dg_status_ret['status'] = 'FALSE'
    dg_status_ret['key'] = 'DG_PRIMARY_ORACLE_STATUS_CHECK'
    dg_status_ret['startTime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    dg_status_ret['desc'] = '检查dg oracle中primary oracle的运行状态以及相关配置是否同standby oracle配置匹配'
    dg_status_ret['comment'] = ''
    item_list = list()
    dg_status_ret['item_list'] = item_list
    ora_cfg = pri_ora_cfg
    rltd_ora_cfg = stby_ora_cfg
    host_ip = ora_cfg['host_ip']
    check_result = __ping_test(host_ip)
    item_list.append(check_result)
    if check_result[check_result['key']] != 'PING_SUCC':
        logger.error(host_ip + '服务器不在线，停止检查')
        dg_status_ret['comment'] = '服务器不在线，停止检查'
        dg_status_ret['endTime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        return dg_status_ret
    root_usr = ora_cfg['root_user']
    root_pwd = ora_cfg['root_password']
    ssh_port = ora_cfg['ssh_port']
    check_result, conn = __create_ssh_connect(host_ip, ssh_port, root_usr, root_pwd)
    item_list.append(check_result)
    if not check_result['exec_success']:
        logger.error('为' + root_usr + '创建ssh客户端失败,停止检查')
        dg_status_ret['comment'] = '为' + root_usr + '创建ssh客户端失败,停止检查'
        dg_status_ret['endTime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        return dg_status_ret
    server_check_items = [
        {'desc': '检查服务器终端是否能够正确返回执行结果', 'key': 'CONSOLE', 'command': 'echo 1234567890', 'result_regex_map': {'CONSOLE_RIGHT': '^1234567890$'}, 'accept_result': '^CONSOLE_RIGHT$', 'timeout': False, 'depend_cond': {}, 'command_type': 'bash/shell', 'not_succ_to_break': True},
        {'desc': '检查服务器主机名是否配置正确', 'key': 'HOST_NAME', 'command': 'hostname', 'result_regex_map': {'HOST_NAME_RIGHT': '^' + ora_cfg['host_name'] + '$'}, 'accept_result': '^HOST_NAME_RIGHT$', 'timeout': False, 'depend_cond': {}, 'command_type': 'bash/shell', 'not_succ_to_break': False},
        {'desc': '检查服务器python版本', 'key': 'PYTHON_VERSION', 'command': 'python -V| grep -oP "(?<=^Python )\S+$"', 'result_regex_map': {'V24': script_24_support_version, 'V26': script_26_support_version}, 'accept_result' : '^(V24|V26)$', 'timeout': False, 'depend_cond': {}, 'command_type': 'bash/shell', 'not_succ_to_break': True},
        {'desc': '确认hosts文件存在', 'key': 'HOSTS_FILE', 'command': 'ls /etc/hosts', 'result_regex_map': {'HOSTS_EXIST': '^/etc/hosts$'}, 'accept_result': '^HOSTS_EXIST$', 'timeout': False, 'depend_cond': {}, 'command_type': 'bash/shell', 'not_succ_to_break': False},
        {'desc': 'hosts没有配置备库ip', 'key': 'HOSTS_CFG', 'command': 'grep "' + rltd_ora_cfg['host_ip'] + '" /etc/hosts | grep -v "^\s*#"', 'result_regex_map': {'NOT_CONTENT_STANDBY_IP': '^\s*$'}, 'accept_result': '^NOT_CONTENT_STANDBY_IP$', 'command_type': 'bash/shell', 'timeout': False, 'depend_cond': {}, 'not_succ_to_break': False},
        {'desc': '确认网卡是bond0模式', 'key': 'BOND0', 'command': 'ls /etc/sysconfig/network-scripts/ifcfg-bond0', 'result_regex_map': {'BOND0_EXIST': '^/etc/sysconfig/network-scripts/ifcfg-bond0$'}, 'accept_result': '^BOND0_EXIST$', 'timeout': False, 'depend_cond': {}, 'command_type': 'bash/shell', 'not_succ_to_break': False},
        {'desc': '确认NetworkManager服务未被启动', 'key': 'NETWORKMANAGER_SERVICE', 'command': 'service NetworkManager status|grep -oP "(?<=pid ).*(?=\))" | grep -oP "\d+"', 'result_regex_map': {'SERVICE_NOT_START': '^$', 'SERVICE_START': '^\d+$'}, 'accept_result': '^SERVICE_NOT_START$', 'timeout': False, 'depend_cond': {}, 'command_type': 'bash/shell', 'not_succ_to_break': False},
    ]
    check_k_v = dict()
    err_msg = ''
    for check_item in server_check_items:
        can_exec_check = True
        for k, v in check_item['depend_cond'].iteritems():
            if not check_k_v.has_key(k) or check_k_v[k] != v:
                logger.info(check_item['desc'] + '依赖的的条件:' + k + '=' + v + '不满足,该步骤将不执行')
                can_exec_check = False
                break
        if can_exec_check:
            item_result = __exec_check(conn, check_item)
            item_list.append(item_result)
            check_k_v[check_item['key']] = item_result[check_item['key']]
            if not item_result['exec_success']:
                err_msg = err_msg + check_item['desc'] + '检查失败;'
                if check_item['not_succ_to_break']:
                    logger.error(check_item['desc'] + '执行失败且not_succ_to_break=True,退出检查流程,当前流程执行结果:' + err_msg)
                    dg_status_ret['comment'] = err_msg
                    conn.close()
                    return dg_status_ret
    base_path = ora_cfg['base_path']
    bin_path = (base_path + "/bin/lsnrctl").replace("//", "/")
    tnsnames_path = (base_path + '/network/admin/tnsnames.ora').replace("//", "/")
    listener_path = (base_path + '/network/admin/listener.ora').replace("//", "/")
    ora_check_items = [
        {'desc': '检查base_path配置是否配置正确', 'key': 'BASE_PATH', 'command': 'ls ' + bin_path, 'result_regex_map': {'BASE_PATH_RIGHT': '^' + bin_path + '$'}, 'accept_result': '^BASE_PATH_RIGHT$', 'timeout': False, 'depend_cond': {}, 'command_type': 'bash/shell', 'not_succ_to_break': True},
        {'desc': '检查tnsnames.ora文件存在', 'key': 'TNSNAMES_FILE', 'command': 'ls ' + tnsnames_path, 'result_regex_map': {'TNSNAMES_EXIST': '^' + tnsnames_path + '$'}, 'accept_result': '^TNSNAMES_EXIST$', 'timeout': False, 'depend_cond': {}, 'command_type': 'bash/shell', 'not_succ_to_break': False},
        {'desc': '确认tnsnames.ora中的HOST只能是ip地址', 'key': 'TNSNAMES_CFG', 'command': 'grep -v "\s*#" ' + tnsnames_path + '|grep -oP "(?<=HOST)\s*=\s*\S+\s*(?=\))"|grep -oP "(?<==).*"|grep -vP "^\s*\d+\.\d+\.\d+\.\d+\s*"', 'result_regex_map': {'TNSNAMES_CFG_HOST_USE_IP': '^$'}, 'accept_result' : '^TNSNAMES_CFG_HOST_USE_IP$', 'timeout': False, 'depend_cond': {}, 'command_type': 'bash/shell', 'not_succ_to_break': True},
        {'desc': '确认listener.ora文件存在', 'key': 'LISTENER_FILE', 'command': 'ls ' + listener_path, 'result_regex_map': {'LISTENER_EXIST': '^' + listener_path + '$'}, 'accept_result': '^LISTENER_EXIST$', 'timeout': False, 'depend_cond': {}, 'command_type': 'bash/shell', 'not_succ_to_break': False},
        {'desc': '确认listener.ora的HOST没有用ip表示', 'key': 'LISTENER_CFG', 'command': 'grep -v "^\s*#" ' + listener_path + '|grep -oP "(?<=HOST)\s*=\s*\S+\s*(?=\))"|grep -oP "(?<==).*"|grep -E "^\s*(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\s*$"', 'result_regex_map': {'LISTENER_CFG_HOST_NOT_USE_IP': '^$'}, 'accept_result': '^LISTENER_CFG_HOST_NOT_USE_IP$', 'command_type': 'bash/shell', 'timeout': False, 'depend_cond': {'LISTENER_EXIST' : 'LISTENER_EXIST'}, 'not_succ_to_break': False},
        {'desc': '检查tns服务状态', 'key': 'TNS_SERVICE', 'command': 'lsnrctl status', 'result_regex_map': {'TNS_START': '.*The command completed successfully.*', 'TNS_NOT_START':'.*TNS-12541.*'}, 'accept_result': '^TNS_START$', 'timeout': False, 'depend_cond': {}, 'command_type': 'bash/shell', 'not_succ_to_break': False},
        {'desc': '检查数据库启动状态', 'key': 'DATABASE_STATUS', 'command': 'sqlplus -s / as sysdba <<EOF\nselect status,database_status from v\\$instance;\nEOF', 'result_regex_map': {'MOUNTED': '.*MOUNTED.*ACTIVE.*', 'OPEN': '.*OPEN.*ACTIVE.*', 'SHUTDOWN' : '.*ORA-01034.*'}, 'accept_result': '^OPEN$', 'timeout': False, 'depend_cond': {}, 'command_type': 'oracle/sql', 'not_succ_to_break': False},
        {'desc': '检查oracle的实例名', 'key': 'INSTANCE', 'command': 'sqlplus -s / as sysdba <<EOF\nselect value from v\\$parameter where name=\'instance_name\';\nEOF',
         'result_regex_map': {'INSTANCE_RIGHT': '.*' + ora_cfg['app_name'] + '$'}, 'accept_result': '^INSTANCE_RIGHT$',
         'timeout': False, 'depend_cond': {}, 'command_type': 'bash/shell', 'not_succ_to_break': True},
        {'desc': '检查oracle的unique name(别名)', 'key': 'UNIQUE_NAME', 'command': 'sqlplus -s / as sysdba <<EOF\nselect value from v\\$parameter where name=\'db_unique_name\';\nEOF',
         'result_regex_map': {'UNIQUE_NAME_RIGHT': '.*' + ora_cfg['app_alias'] + '.*'}, 'accept_result': '^UNIQUE_NAME_RIGHT$',
         'timeout': False, 'depend_cond': {}, 'command_type': 'bash/shell', 'not_succ_to_break': False},
        {'desc': '检查主库配置的备库的DB_UNIQUE_NAME是否和备库的unique name一致', 'key': 'DB_UNIQUE_NAME',
         'command': 'sqlplus -s / as sysdba <<EOF\nselect value from v\\$parameter where name=\'log_archive_dest_2\';\nEOF',
         'result_regex_map': {'DB_UNIQUE_NAME_RIGHT': '.*(DB_UNIQUE_NAME|db_unique_name)=' + rltd_ora_cfg['app_alias'] + '(\s|$)'}, 'accept_result': '^DB_UNIQUE_NAME_RIGHT$',
         'timeout': False, 'depend_cond': {}, 'command_type': 'oracle/sql', 'not_succ_to_break': True},
        {'desc': '检查主库配置的备库service是否和备库定义的service_name一致', 'key': 'ORA_DG_SERVICE', 'command': 'sqlplus -s / as sysdba <<EOF\nselect value from v\\$parameter where name=\'log_archive_dest_2\';\nEOF',
         'result_regex_map': {'ORA_DG_SERVICE': '.*(SERVICE|service)='+ rltd_ora_cfg['service_name'] + '(\s|$)'}, 'accept_result': '^ORA_DG_SERVICE_RIGHT$',
         'timeout': False, 'depend_cond': {}, 'command_type': 'oracle/sql', 'not_succ_to_break': False},
        {'desc': '确认listener.ora的HOST没有用ip表示', 'key': 'LISTENER_CFG',
         'command': 'grep -v "^\s*#" ' + listener_path + '|grep -oP "(?<=HOST)\s*=\s*\S+\s*(?=\))"|grep -oP "(?<==).*"|grep -E "^\s*(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\s*$"',
         'result_regex_map': {'LISTENER_CFG_HOST_NOT_USE_IP': '^$'}, 'accept_result': '^LISTENER_CFG_HOST_NOT_USE_IP$',
         'command_type': 'bash/shell', 'timeout': False, 'depend_cond': {'LISTENER_EXIST': 'LISTENER_EXIST'},
         'not_succ_to_break': False},
        {'desc': '检查tns服务状态', 'key': 'TNS_SERVICE', 'command': 'lsnrctl status',
         'result_regex_map': {'TNS_START': '.*The command completed successfully.*', 'TNS_NOT_START': '.*TNS-12541.*'},
         'accept_result': '^TNS_START$', 'timeout': False, 'depend_cond': {}, 'command_type': 'bash/shell',
         'not_succ_to_break': False},
        {'desc': '检查数据库实例运行状态', 'key': 'DATABASE_INSTANCE_STATUS',
         'command': 'sqlplus -s / as sysdba <<EOF\nselect instance_name,status,database_status from v\\$instance;\nEOF',
         'result_regex_map': {'MOUNTED': '.*' + ora_cfg['app_name'] + '.*MOUNTED.*ACTIVE.*', 'OPEN': '.*OPEN.*ACTIVE.*', 'SHUTDOWN': '.*ORA-01034.*'},
         'accept_result': '^OPEN$', 'timeout': False, 'depend_cond': {}, 'command_type': 'oracle/sql',
         'not_succ_to_break': True},
        {'desc': '检查oracle的database role', 'key': 'DATABASE_ROLE',
         'command': 'sqlplus -s / as sysdba <<EOF\nselect database_role from v\\$database;\nEOF',
         'result_regex_map': {'PRIMARY': '.*PRIMARY.*', 'STANDBY': '.*PHYSICAL STANDBY.*'},
         'accept_result': '^PRIMARY$',
         'timeout': False, 'depend_cond': {}, 'command_type': 'oracle/sql', 'not_succ_to_break': False},
        {'desc': '检查oracle的switchover status', 'key': 'SWITCHOVER_STATUS',
         'command': 'sqlplus -s / as sysdba <<EOF\nselect switchover_status from v\\$database;\nEOF',
         'result_regex_map': {'TO_PRIMARY': '.*TO PRIMART.*', 'TO_STANDBY': '.*TO STANDBY.*', 'SESSIONS_ACTIVE': '.*SESSIONS ACTIVE.*', 'ORA_ERROR': '.*ORA-\\d{5,5}(\\D|$)'},
         'accept_result': '^(TO_PRIMARY|SESSIONS_ACTIVE)$',
         'timeout': False, 'depend_cond': {}, 'command_type': 'oracle/sql', 'not_succ_to_break': False},
        {'desc': '检查oracle的archive_gap', 'key': 'ARCHIVE_GAP',
         'command': 'sqlplus -s / as sysdba <<EOF\nselect * from v\\$archive_gap;\nEOF',
         'result_regex_map': {'ARCHIVE_GAP_EMPTY': '.*no rows selected.*', 'ARCHIVE_GAP_NOT_EMPTY': '^((?!no rows selected).)*$'},
         'accept_result': '^ARCHIVE_GAP_EMPTY$',
         'timeout': False, 'depend_cond': {}, 'command_type': 'oracle/sql', 'not_succ_to_break': False},
        {'desc': '检查oracle的archive log', 'key': 'ARCHIVE_LOG',
         'command': 'sqlplus -s / as sysdba <<EOF\nselect (select max(SEQUENCE#) from V\\$archived_log where applied=\'NO\')-(select max(SEQUENCE#) from V\\$archived_log where applied=\'YES\')  as archived_log from dual;\nEOF',
         'result_regex_map': {'ARCHIVE_LOG_OK': '\D(0|1)$'}, 'accept_result': '^ARCHIVE_LOG_OK$',
         'command_type': 'oracle/sql', 'timeout': False, 'depend_cond': {},
         'not_succ_to_break': False},
        {'desc': '检查oracle的表空间', 'key': 'TABLE_SPACE', 'command': 'sqlplus -s / as sysdba <<EOF\nselect TABLESPACE_NAME,FILE_NAME,STATUS from dba_temp_files;\nEOF',
         'result_regex_map': {'TABLE_SPACE_OK': '.*AVAILABLE.*', 'TABLE_SPACE_ERROR': '.*ORA-01110: data file 201.*'},
         'accept_result': '^TABLE_SPACE_OK$', 'timeout': False, 'depend_cond': {}, 'command_type': 'oracle/sql',
         'not_succ_to_break': False}
    ]
    check_result, conn = __create_ssh_connect(host_ip, ssh_port, ora_cfg['app_user'], ora_cfg['app_user_password'])
    item_list.append(check_result)
    if not check_result['exec_success'] :
        logger.error('为' + ora_cfg['app_user'] + '创建ssh客户端失败,停止检查')
        dg_status_ret['comment'] = '为' + ora_cfg['app_user'] + '创建ssh客户端失败,停止检查'
        dg_status_ret['endTime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        return dg_status_ret
    for check_item in ora_check_items:
        can_exec_check = True
        for k, v in check_item['depend_cond'].iteritems():
            if not check_k_v.has_key(k) or check_k_v[k] != v:
                logger.info(check_item['desc'] + '依赖的的条件:' + k + '=' + v + '不满足,该步骤将不执行')
                can_exec_check = False
                break
        if can_exec_check:
            item_result = __exec_check(conn, check_item)
            item_list.append(item_result)
            if not item_result['exec_success']:
                err_msg = err_msg + check_item['desc'] + '检查失败;'
                if check_item['not_succ_to_break']:
                    logger.error(check_item['desc'] + '执行失败且not_succ_to_break=True,退出检查流程,当前流程执行结果:' + err_msg)
                    dg_status_ret['comment'] = err_msg
                    conn.close()
                    return dg_status_ret
    if err_msg == '':
        dg_status_ret['status'] = 'SUCCESS'
        dg_status_ret['comment'] = '主oracle状态检查通过'
    else:
        dg_status_ret['comment'] = err_msg
    logger.info('主oracle状态检查结果' + dg_status_ret['status'] + ':' + dg_status_ret['comment'])


def check_dg_stby_oracle_status(pri_ora_cfg, stby_ora_cfg):
    dg_status_ret = dict()
    dg_status_ret['status'] = 'FALSE'
    dg_status_ret['key'] = 'DG_STANDBY_ORACLE_STATUS_CHECK'
    dg_status_ret['startTime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    dg_status_ret['desc'] = '检查dg oracle中primary oracle的运行状态以及相关配置是否同standby oracle配置匹配'
    dg_status_ret['comment'] = ''
    item_list = list()
    dg_status_ret['item_list'] = item_list
    ora_cfg = stby_ora_cfg
    rltd_ora_cfg = pri_ora_cfg
    host_ip = ora_cfg['host_ip']
    check_result = __ping_test(host_ip)
    item_list.append(check_result)
    if check_result[check_result['key']] != 'PING_SUCC':
        logger.error(host_ip + '服务器不在线，停止检查')
        dg_status_ret['comment'] = '服务器不在线，停止检查'
        dg_status_ret['endTime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        return dg_status_ret
    root_usr = ora_cfg['root_user']
    root_pwd = ora_cfg['root_password']
    ssh_port = ora_cfg['ssh_port']
    check_result, conn = __create_ssh_connect(host_ip, ssh_port, root_usr, root_pwd)
    item_list.append(check_result)
    if not check_result['exec_success']:
        logger.error('为' + root_usr + '创建ssh客户端失败,停止检查')
        dg_status_ret['comment'] = '为' + root_usr + '创建ssh客户端失败,停止检查'
        dg_status_ret['endTime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        return dg_status_ret
    server_check_items = [
        {'desc': '检查服务器终端是否能够正确返回执行结果', 'key': 'CONSOLE', 'command': 'echo 1234567890', 'result_regex_map': {'CONSOLE_RIGHT': '^1234567890$'}, 'accept_result': '^CONSOLE_RIGHT$', 'timeout': False, 'depend_cond': {}, 'command_type': 'bash/shell', 'not_succ_to_break': True},
        {'desc': '检查服务器主机名是否配置正确', 'key': 'HOST_NAME', 'command': 'hostname', 'result_regex_map': {'HOST_NAME_RIGHT': '^' + ora_cfg['host_name'] + '$'}, 'accept_result': '^HOST_NAME_RIGHT$', 'timeout': False, 'depend_cond': {}, 'command_type': 'bash/shell', 'not_succ_to_break': False},
        {'desc': '检查服务器python版本', 'key': 'PYTHON_VERSION', 'command': 'python -V| grep -oP "(?<=^Python )\S+$"', 'result_regex_map': {'V24': script_24_support_version, 'V26': script_26_support_version}, 'accept_result' : '^(V24|V26)$', 'timeout': False, 'depend_cond': {}, 'command_type': 'bash/shell', 'not_succ_to_break': True},
        {'desc': '确认hosts文件存在', 'key': 'HOSTS_FILE', 'command': 'ls /etc/hosts', 'result_regex_map': {'HOSTS_EXIST': '^/etc/hosts$'}, 'accept_result': '^HOSTS_EXIST$', 'timeout': False, 'depend_cond': {}, 'command_type': 'bash/shell', 'not_succ_to_break': False},
        {'desc': 'hosts没有配置备库ip', 'key': 'HOSTS_CFG', 'command': 'grep "' + rltd_ora_cfg['host_ip'] + '" /etc/hosts | grep -v "^\s*#"', 'result_regex_map': {'NOT_CONTENT_STANDBY_IP': '^\s*$'}, 'accept_result': '^NOT_CONTENT_STANDBY_IP$', 'command_type': 'bash/shell', 'timeout': False, 'depend_cond': {}, 'not_succ_to_break': False},
        {'desc': '确认网卡是bond0模式', 'key': 'BOND0', 'command': 'ls /etc/sysconfig/network-scripts/ifcfg-bond0', 'result_regex_map': {'BOND0_EXIST': '^/etc/sysconfig/network-scripts/ifcfg-bond0$'}, 'accept_result': '^BOND0_EXIST$', 'timeout': False, 'depend_cond': {}, 'command_type': 'bash/shell', 'not_succ_to_break': False},
        {'desc': '确认NetworkManager服务未被启动', 'key': 'NETWORKMANAGER_SERVICE', 'command': 'service NetworkManager status|grep -oP "(?<=pid ).*(?=\))" | grep -oP "\d+"', 'result_regex_map': {'SERVICE_NOT_START': '^$', 'SERVICE_START': '^\d+$'}, 'accept_result': '^SERVICE_NOT_START$', 'timeout': False, 'depend_cond': {}, 'command_type': 'bash/shell', 'not_succ_to_break': False},
    ]
    check_k_v = dict()
    err_msg = ''
    for check_item in server_check_items:
        can_exec_check = True
        for k, v in check_item['depend_cond'].iteritems():
            if not check_k_v.has_key(k) or check_k_v[k] != v:
                logger.info(check_item['desc'] + '依赖的的条件:' + k + '=' + v + '不满足,该步骤将不执行')
                can_exec_check = False
                break
        if can_exec_check:
            item_result = __exec_check(conn, check_item)
            item_list.append(item_result)
            check_k_v[check_item['key']] = item_result[check_item['key']]
            if not item_result['exec_success']:
                err_msg = err_msg + check_item['desc'] + '检查失败;'
                if check_item['not_succ_to_break']:
                    logger.error(check_item['desc'] + '执行失败且not_succ_to_break=True,退出检查流程,当前流程执行结果:' + err_msg)
                    dg_status_ret['comment'] = err_msg
                    conn.close()
                    return dg_status_ret
    base_path = ora_cfg['base_path']
    bin_path = (base_path + "/bin/lsnrctl").replace("//", "/")
    tnsnames_path = (base_path + '/network/admin/tnsnames.ora').replace("//", "/")
    listener_path = (base_path + '/network/admin/listener.ora').replace("//", "/")
    ora_check_items = [
        {'desc': '检查base_path配置是否配置正确', 'key': 'BASE_PATH', 'command': 'ls ' + bin_path, 'result_regex_map': {'BASE_PATH_RIGHT': '^' + bin_path + '$'}, 'accept_result': '^BASE_PATH_RIGHT$', 'timeout': False, 'depend_cond': {}, 'command_type': 'bash/shell', 'not_succ_to_break': True},
        {'desc': '检查tnsnames.ora文件存在', 'key': 'TNSNAMES_FILE', 'command': 'ls ' + tnsnames_path, 'result_regex_map': {'TNSNAMES_EXIST': '^' + tnsnames_path + '$'}, 'accept_result': '^TNSNAMES_EXIST$', 'timeout': False, 'depend_cond': {}, 'command_type': 'bash/shell', 'not_succ_to_break': False},
        {'desc': '确认tnsnames.ora中的HOST只能是ip地址', 'key': 'TNSNAMES_CFG', 'command': 'grep -v "\s*#" ' + tnsnames_path + '|grep -oP "(?<=HOST)\s*=\s*\S+\s*(?=\))"|grep -oP "(?<==).*"|grep -vP "^\s*\d+\.\d+\.\d+\.\d+\s*"', 'result_regex_map': {'TNSNAMES_CFG_HOST_USE_IP': '^$'}, 'accept_result' : '^TNSNAMES_CFG_HOST_USE_IP$', 'timeout': False, 'depend_cond': {}, 'command_type': 'bash/shell', 'not_succ_to_break': True},
        {'desc': '确认listener.ora文件存在', 'key': 'LISTENER_FILE', 'command': 'ls ' + listener_path, 'result_regex_map': {'LISTENER_EXIST': '^' + listener_path + '$'}, 'accept_result': '^LISTENER_EXIST$', 'timeout': False, 'depend_cond': {}, 'command_type': 'bash/shell', 'not_succ_to_break': False},
        {'desc': '确认listener.ora的HOST没有用ip表示', 'key': 'LISTENER_CFG', 'command': 'grep -v "^\s*#" ' + listener_path + '|grep -oP "(?<=HOST)\s*=\s*\S+\s*(?=\))"|grep -oP "(?<==).*"|grep -E "^\s*(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\s*$"', 'result_regex_map': {'LISTENER_CFG_HOST_NOT_USE_IP': '^$'}, 'accept_result': '^LISTENER_CFG_HOST_NOT_USE_IP$', 'command_type': 'bash/shell', 'timeout': False, 'depend_cond': {'LISTENER_EXIST' : 'LISTENER_EXIST'}, 'not_succ_to_break': False},
        {'desc': '检查tns服务状态', 'key': 'TNS_SERVICE', 'command': 'lsnrctl status', 'result_regex_map': {'TNS_START': '.*The command completed successfully.*', 'TNS_NOT_START':'.*TNS-12541.*'}, 'accept_result': '^TNS_START$', 'timeout': False, 'depend_cond': {}, 'command_type': 'bash/shell', 'not_succ_to_break': False},
        {'desc': '检查数据库启动状态', 'key': 'DATABASE_STATUS', 'command': 'sqlplus -s / as sysdba <<EOF\nselect status,database_status from v\\$instance;\nEOF', 'result_regex_map': {'MOUNTED': '.*MOUNTED.*ACTIVE.*', 'OPEN': '.*OPEN.*ACTIVE.*', 'SHUTDOWN' : '.*ORA-01034.*'}, 'accept_result': '^OPEN$', 'timeout': False, 'depend_cond': {}, 'command_type': 'oracle/sql', 'not_succ_to_break': False},
        {'desc': '检查oracle的实例名', 'key': 'INSTANCE', 'command': 'sqlplus -s / as sysdba <<EOF\nselect value from v\\$parameter where name=\'instance_name\';\nEOF',
         'result_regex_map': {'INSTANCE_RIGHT': '.*' + ora_cfg['app_name'] + '$'}, 'accept_result': '^INSTANCE_RIGHT$',
         'timeout': False, 'depend_cond': {}, 'command_type': 'bash/shell', 'not_succ_to_break': True},
        {'desc': '检查oracle的unique name(别名)', 'key': 'UNIQUE_NAME', 'command': 'sqlplus -s / as sysdba <<EOF\nselect value from v\\$parameter where name=\'db_unique_name\';\nEOF',
         'result_regex_map': {'UNIQUE_NAME_RIGHT': '.*' + ora_cfg['app_alias'] + '.*'}, 'accept_result': '^UNIQUE_NAME_RIGHT$',
         'timeout': False, 'depend_cond': {}, 'command_type': 'bash/shell', 'not_succ_to_break': False},
        {'desc': '检查主库配置的备库的DB_UNIQUE_NAME是否和备库的unique name一致', 'key': 'DB_UNIQUE_NAME',
         'command': 'sqlplus -s / as sysdba <<EOF\nselect value from v\\$parameter where name=\'log_archive_dest_2\';\nEOF',
         'result_regex_map': {'DB_UNIQUE_NAME_RIGHT': '.*(DB_UNIQUE_NAME|db_unique_name)=' + rltd_ora_cfg['app_alias'] + '(\s|$)'}, 'accept_result': '^DB_UNIQUE_NAME_RIGHT$',
         'timeout': False, 'depend_cond': {}, 'command_type': 'oracle/sql', 'not_succ_to_break': True},
        {'desc': '检查主库配置的备库service是否和备库定义的service_name一致', 'key': 'ORA_DG_SERVICE', 'command': 'sqlplus -s / as sysdba <<EOF\nselect value from v\\$parameter where name=\'log_archive_dest_2\';\nEOF',
         'result_regex_map': {'ORA_DG_SERVICE': '.*(SERVICE|service)='+ rltd_ora_cfg['service_name'] + '(\s|$)'}, 'accept_result': '^ORA_DG_SERVICE_RIGHT$',
         'timeout': False, 'depend_cond': {}, 'command_type': 'oracle/sql', 'not_succ_to_break': False},
        {'desc': '确认listener.ora的HOST没有用ip表示', 'key': 'LISTENER_CFG',
         'command': 'grep -v "^\s*#" ' + listener_path + '|grep -oP "(?<=HOST)\s*=\s*\S+\s*(?=\))"|grep -oP "(?<==).*"|grep -E "^\s*(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\s*$"',
         'result_regex_map': {'LISTENER_CFG_HOST_NOT_USE_IP': '^$'}, 'accept_result': '^LISTENER_CFG_HOST_NOT_USE_IP$',
         'command_type': 'bash/shell', 'timeout': False, 'depend_cond': {'LISTENER_EXIST': 'LISTENER_EXIST'},
         'not_succ_to_break': False},
        {'desc': '检查tns服务状态', 'key': 'TNS_SERVICE', 'command': 'lsnrctl status',
         'result_regex_map': {'TNS_START': '.*The command completed successfully.*', 'TNS_NOT_START': '.*TNS-12541.*'},
         'accept_result': '^TNS_START$', 'timeout': False, 'depend_cond': {}, 'command_type': 'bash/shell',
         'not_succ_to_break': False},
        {'desc': '检查数据库实例运行状态', 'key': 'DATABASE_INSTANCE_STATUS',
         'command': 'sqlplus -s / as sysdba <<EOF\nselect instance_name,status,database_status from v\\$instance;\nEOF',
         'result_regex_map': {'MOUNTED': '.*' + ora_cfg['app_name'] + '.*MOUNTED.*ACTIVE.*', 'OPEN': '.*OPEN.*ACTIVE.*', 'SHUTDOWN': '.*ORA-01034.*'},
         'accept_result': '^OPEN$', 'timeout': False, 'depend_cond': {}, 'command_type': 'oracle/sql',
         'not_succ_to_break': True},
        {'desc': '检查oracle的database role', 'key': 'DATABASE_ROLE',
         'command': 'sqlplus -s / as sysdba <<EOF\nselect database_role from v\\$database;\nEOF',
         'result_regex_map': {'PRIMARY': '.*PRIMARY.*', 'STANDBY': '.*PHYSICAL STANDBY.*'},
         'accept_result': '^PRIMARY$',
         'timeout': False, 'depend_cond': {}, 'command_type': 'oracle/sql', 'not_succ_to_break': False},
        {'desc': '检查oracle的switchover status', 'key': 'SWITCHOVER_STATUS',
         'command': 'sqlplus -s / as sysdba <<EOF\nselect switchover_status from v\\$database;\nEOF',
         'result_regex_map': {'TO_PRIMARY': '.*TO PRIMART.*', 'TO_STANDBY': '.*TO STANDBY.*', 'SESSIONS_ACTIVE': '.*SESSIONS ACTIVE.*', 'ORA_ERROR': '.*ORA-\\d{5,5}(\\D|$)'},
         'accept_result': '^(TO_PRIMARY|SESSIONS_ACTIVE)$',
         'timeout': False, 'depend_cond': {}, 'command_type': 'oracle/sql', 'not_succ_to_break': False},
        {'desc': '检查oracle的archive_gap', 'key': 'ARCHIVE_GAP',
         'command': 'sqlplus -s / as sysdba <<EOF\nselect * from v\\$archive_gap;\nEOF',
         'result_regex_map': {'ARCHIVE_GAP_EMPTY': '.*no rows selected.*', 'ARCHIVE_GAP_NOT_EMPTY': '^((?!no rows selected).)*$'},
         'accept_result': '^ARCHIVE_GAP_EMPTY$',
         'timeout': False, 'depend_cond': {}, 'command_type': 'oracle/sql', 'not_succ_to_break': False},
        {'desc': '检查oracle的archive log', 'key': 'ARCHIVE_LOG',
         'command': 'sqlplus -s / as sysdba <<EOF\nselect (select max(SEQUENCE#) from V\\$archived_log where applied=\'NO\')-(select max(SEQUENCE#) from V\\$archived_log where applied=\'YES\')  as archived_log from dual;\nEOF',
         'result_regex_map': {'ARCHIVE_LOG_OK': '\D(0|1)$'}, 'accept_result': '^ARCHIVE_LOG_OK$',
         'command_type': 'oracle/sql', 'timeout': False, 'depend_cond': {},
         'not_succ_to_break': False},
        {'desc': '检查oracle的表空间', 'key': 'TABLE_SPACE', 'command': 'sqlplus -s / as sysdba <<EOF\nselect TABLESPACE_NAME,FILE_NAME,STATUS from dba_temp_files;\nEOF',
         'result_regex_map': {'TABLE_SPACE_OK': '.*AVAILABLE.*', 'TABLE_SPACE_ERROR': '.*ORA-01110: data file 201.*'},
         'accept_result': '^TABLE_SPACE_OK$', 'timeout': False, 'depend_cond': {}, 'command_type': 'oracle/sql',
         'not_succ_to_break': False}
    ]
    check_result, conn = __create_ssh_connect(host_ip, ssh_port, ora_cfg['app_user'], ora_cfg['app_user_password'])
    item_list.append(check_result)
    if not check_result['exec_success'] :
        logger.error('为' + ora_cfg['app_user'] + '创建ssh客户端失败,停止检查')
        dg_status_ret['comment'] = '为' + ora_cfg['app_user'] + '创建ssh客户端失败,停止检查'
        dg_status_ret['endTime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        return dg_status_ret
    for check_item in ora_check_items:
        can_exec_check = True
        for k, v in check_item['depend_cond'].iteritems():
            if not check_k_v.has_key(k) or check_k_v[k] != v:
                logger.info(check_item['desc'] + '依赖的的条件:' + k + '=' + v + '不满足,该步骤将不执行')
                can_exec_check = False
                break
        if can_exec_check:
            item_result = __exec_check(conn, check_item)
            item_list.append(item_result)
            if not item_result['exec_success']:
                err_msg = err_msg + check_item['desc'] + '检查失败;'
                if check_item['not_succ_to_break']:
                    logger.error(check_item['desc'] + '执行失败且not_succ_to_break=True,退出检查流程,当前流程执行结果:' + err_msg)
                    dg_status_ret['comment'] = err_msg
                    conn.close()
                    return dg_status_ret
    if err_msg == '':
        dg_status_ret['status'] = 'SUCCESS'
        dg_status_ret['comment'] = '主oracle状态检查通过'
    else:
        dg_status_ret['comment'] = err_msg
    logger.info('主oracle状态检查结果' + dg_status_ret['status'] + ':' + dg_status_ret['comment'])


def check_dg_oracle_status(pri_ora_cfg, stby_ora_cfg):
    dg_status_ret = dict()
    dg_status_ret['status'] = 'SUCCESS'
    dg_status_ret['key'] = 'DG_STANDBY_ORACLE_STATUS_CHECK'
    dg_status_ret['startTime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    dg_status_ret['desc'] = '检查dg oracle运行装态以及配置信息'
    dg_status_ret['comment'] = ''
    pri_status = check_dg_primary_oracle_status(pri_ora_cfg, stby_ora_cfg)
    stby_status = check_dg_stby_oracle_status(pri_ora_cfg, stby_ora_cfg)
    dg_status_ret['endTime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    dg_status_ret['pri_ora_dg_status'] = pri_status
    dg_status_ret['stby_ora_dg_status'] = stby_status
    return dg_status_ret



def start_pri_stby_switch(pri_ora_cfg, stby_ora_cfg, switch_method, avaible_ip):
    return None


"""
ora_cfg = AppCfg.objects.get(id=1)
cfg = dict()
cfg['app_template_id'] = ora_cfg.app_template.id
cfg['app_type'] = ora_cfg.app_type
cfg['app_name'] = ora_cfg.app_name
cfg['app_alias'] = ora_cfg.app_alias
cfg['base_path'] = ora_cfg.base_path
cfg['host_ip'] = ora_cfg.server.host_ip
cfg['host_name'] = ora_cfg.server.host_name
cfg['root_user'] = ora_cfg.root_user.login_name
cfg['root_password'] = ora_cfg.root_user.pass_word
cfg['app_user'] = ora_cfg.app_user.login_name
cfg['app_user_password'] = ora_cfg.app_user.pass_word
cfg['app_cfg_id'] = ora_cfg.id
cfg['server_id'] = ora_cfg.server.id
cfg['root_user_id'] = ora_cfg.root_user.id
cfg['app_user_id'] = ora_cfg.app_user.id
cfg['service_name'] = ora_cfg.server_name
{'app_user_password': u'123456', 'app_type': u'oracle', 'app_name': u'ccod', 'service_name': u'db_wending', 'server_id': 1, 'host_ip': u'10.130.41.159', 'base_path
': u'/home/oracle/oracle10g/product/10.2.0/db_1', 'app_template_id': 1, 'app_alias': u'WENDING', 'root_user_id': 1, 'app_user_id': 2, 'host_name': u'ccod-oracle5',
 'app_cfg_id': 1, 'app_user': u'oracle', 'root_password': u'123456', 'root_user': u'root'}
 [{'timeout': True, 'depend_cond': {'TERMINAL_CONSOLE': 'SUCC'}, 'result_regex_map': {'SUCC': '.*The command completed successfully.*', 'TNS_NOT_START': '.*TNS-12541.*'}, 'command': 'lsnrctl status', 'key': 'TNS_START', 'command_type': 'bash/shell', 'not_succ_to_break': True, 'desc': '检查oracle的tns服务是否启动'}]
"""

test_ret = check_dg_primary_oracle_status(pri_cfg, stby_cfg)
print(test_ret)
