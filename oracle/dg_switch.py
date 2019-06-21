from common.log import logger
from datetime import datetime
import  re
import subprocess
import signal, functools
class TimeoutError(Exception): pass
import paramiko
from paramiko.ssh_exception import AuthenticationException


hosts = ['10.130.41.159', '10.130.41.159', '10.130.41.161', '10.130.41.161']
pri_cfg = {'app_user_password': u'123456', 'app_type': u'oracle', 'app_name': u'ccod', 'service_name': u'db_wending', 'server_id': 1, 'host_ip': u'10.130.41.159', 'base_path': u'/home/oracle/oracle10g/product/10.2.0/db_1', 'app_template_id': 1, 'app_alias': u'WENDING', 'root_user_id': 1, 'app_user_id': 2, 'host_name': u'ccod-oracle5', 'app_cfg_id': 1, 'app_user': u'oracle', 'root_password': u'123456', 'root_user': u'root'}
stby_cfg = {'app_user_password': u'123456', 'app_type': u'oracle', 'app_name': u'ccod', 'service_name': u'db_phystdby', 'server_id': 2, 'host_ip': u'10.130.41.161', 'base_path': u'/home/oracle/oracle10g/product/10.2.0/db_1', 'app_template_id': 1, 'app_alias': u'PHYSTDBY', 'root_user_id': 3, 'app_user_id': 4, 'host_name': u'localhost','app_cfg_id': 2, 'app_user': u'oracle', 'root_password': u'123456', 'root_user': u'root'}


default_exec_command_timeout = 10
ssh_connect_timeout = 20
script_24_support_version = '^2\.4\.3$'
script_26_support_version = '^2\.6\.6$'
script_3_support_version = '||'
ip_regex = '.*(2(5[0-5]{1}|[0-4]\\d{1})|[0-1]?\\d{1,2})\\.(2(5[0-5]{1}|[0-4]\\d{1})|[0-1]?\\d{1,2})\\.(2(5[0-5]{1}|[0-4]\\d{1})|[0-1]?\\d{1,2})\\.(2(5[0-5]{1}|[0-4]\\d{1})|[0-1]?\\d{1,2}).*'


def __do_check(check_type, conn, ora_cfg, rlt_ora_cfg, command_type, command, desc, result_regex_map)

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
    key = 'PING'
    ret['startTime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    ret['command'] = command
    ret['desc'] = '服务器是否在线'
    ret['key'] = key
    process = subprocess.Popen(command,shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,close_fds=True)
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
    result = out.decode()
    str_info = re.compile("(\n)*$")
    result = str_info.sub('', result)
    ret['endTime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    ret['output'] = result
    if re.match(".*ttl=.*", result) and re.match(".*time=.*", result):
        ret[key] = 'SUCC'
    else:
        result[key] = 'FAIL'
    logger.info("ping " + host_ip + "result : " + ret[key])
	return ret


@timeout(ssh_connect_timeout, "Timeout Error:fail to create connection in " + ssh_connect_timeout + " seconds")
def __create_ssh_connect(host_ip, ssh_port, user, password):
    logger.info("创建ssh连接host_ip=%s, ssh_port=%d, user=%s, password=%s" % (host_ip, ssh_port, user, password))
    ret = {}
    command = 'create ssh connect for ' + user + '@' + host_ip
    key = 'CREATE_SSH_CONNECT'
    ret['startTime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    ret['command'] = command
    ret['desc'] = '为' + user + '创建ssh连接'
    ret['key'] = key
    ssh_client = None
    try:
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(host_ip, ssh_port, user, password)
        ret['output'] = "create ssh connect for " + user + ":SUCC"
        ret[key] = 'SUCC'
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


def script_result_regex_match(script_result, regex, script_type='bash/shell'):
	str_info = re.compile("\n")
	input_str = str_info.sub('@#@#@', script_result)
	if re.match(regex, input_str):
		return True
	else:
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
    stdin,stdout,stderr = conn.exec_command(command)
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
    for k,v in result_regex_map.iteritems():
		if script_result_regex_match(exec_result, v, script_type):
			logger.info("命令输出结果满足正则表达式:" + v + "," + key + "将返回" + k)
			ret[key] = k
			ret['endTime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            return ret
    logger.error("正则表达式匹配失败," + key + "将返回FALSE")
    ret[key] = 'FALSE'
    ret['endTime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    return ret


def __exec_command(conn, command, key, result_regex_map, desc, script_type):
    """
    通过ssh在linux服务器上执行一条命令，命令执行结果会匹配result_regex_map中的正则，
    如果能够匹配某个正则那么返回的key等于正则表达式对应的关键字否则返回失败
    :param conn: ssh连接会话
    :param command: 需要执行的命令
    :param key: 执行结果对应的key
    :param result_regex_map: 配置命令执行结果的正则表达式
    :param desc: 命令描述
    :param script_type: 脚本类型目前只支持bash/shell和oracle/sql两类
    :return: {'output', 'command', 'key', key, 'desc', 'output', 'startTime', 'endTime'}
    """
    ret = dict()
    ret['output'] = result
    ret['command'] = command
    ret['key'] = key
    ret['desc'] = desc
    ret['startTime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    stdin, stdout, stderr = conn.exec_command(command)
    exec_result = stdout.read()
    err = stderr.read()
    if err:
        exec_result = err
    ret['output'] = exec_result
    logger.info(command + ' exec result:' + ret['out'])
	for k,v in result_regex_map.iteritems():
		if script_result_regex_match(exec_result, v, script_type=):
			logger.info("命令输出结果满足正则表达式:" + v + "," + key + "将返回" + k)
			ret[key] = k
			ret['endTime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
			return ret
	logger.error("正则表达式匹配失败," + key + "将返回FALSE")
	ret[key] = 'FALSE'
	ret['endTime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
	return ret


def __exec_check(conn, command, key, result_regex_map, desc, script_type='bash/shell'):
    """
    执行某项检查,由于不用考虑超时，仅仅调用__exec_command命令即可
    :param conn: ssh连接会话
    :param command: 执行某项检查需要执行的命令
    :param key: 该项检查对应的key
    :param result_regex_map: 用来匹配检查结果的正则表达式
    :param desc: 检查项描述
    :param script_type: 脚本类型目前只支持bash/shell和oracle/sql两类
    :return: {'output', 'command', 'key', key, 'desc', 'output', 'startTime', 'endTime'}
    """
    ret = dict()
    logger.info("开始%s检查,command=%s, key=%s, result_regex_map=%s" % (desc, command, key, str(result_regex_map)))
    ret['command'] = command
    ret['key'] = key
    ret['desc'] = desc
    ret['startTime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    try:
        ret = __exec_check(conn, command, key, result_regex_map, desc)
    except Exception, err:
        logger.error(desc + " 检查发生异常", err);
        ret[key] = 'FALSE'
        ret['output'] = str(err)
	ret['endTime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
	return ret


def __timeout_exec_check(conn, command, key, result_regex_map, desc, script_type='bash/shell'):
    """
     执行某项检查,需要捕获检查超时异常,例如oracle的listener.ora配置错误有可能造成执行lsnrctl status时返回超时
     :param conn: ssh连接会话
     :param command: 执行某项检查需要执行的命令
     :param key: 该项检查对应的key
     :param result_regex_map: 用来匹配检查结果的正则表达式
     :param desc: 检查项描述
     :param script_type: 命令类型，目前支持bash/shell和oracle/sql
     :return: {'output', 'command', 'key', key, 'desc', 'output', 'startTime', 'endTime'}
     """
    ret = dict()
    logger.info("开始%s检查,command=%s, key=%s, result_regex_map=%s" % (desc, command, key, str(result_regex_map)))
    ret['startTime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    ret['command'] = command
    ret['key'] = key
    ret['desc'] = desc
    try:
        ret = __timeout_exec_command(conn, command, key, result_regex_map, desc, script_type)
    except TimeoutError, detail:
        logger.error(desc + "检查超时", detail)
        ret['output'] = str(detail)
        ret[key] = 'TIMEOUT'
    except Exception, err:
        logger.error(desc + "检查异常", err)
        ret['output'] = str(err)
        ret[key] = 'FALSE'
    ret['endTime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    logger.info(desc + " check result:" + key + "=" + ret[key])
    return ret


def check_dg_primary_oracle_status(pri_ora_cfg, stby_ora_cfg):
    ret = dict()
    ret['status'] = 'FALSE'
    ret['key'] = 'DG_PRIMARY_ORACLE_STATUS_CHECK'
    ret['startTime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    ret['desc'] = '检查dg oracle中primary oracle的运行状态以及相关配置是否同standby oracle配置匹配'
    ret['comment'] = ''
    item_list = list()
    ret['item_list'] = item_list
    ora_cfg = pri_ora_cfg
    rltd_ora_cfg = stby_ora_cfg
    host_ip = ora_cfg.server.host_ip
    check_result = __ping_test(host_ip)
    item_list.append(check_result)
    if check_result[check_result['key']] != 'SUCC':
        logger.error(host_ip + '服务器不在线，停止检查')
        ret['comment'] = '服务器不在线，停止检查'
        ret['endTime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        return ret
    root_usr = ora_cfg.root_user.user_name
    root_pwd = ora_cfg.root_user.pass_word
    ssh_port = ora_cfg.server.ssh_port
    check_result, conn = __create_ssh_connect(host_ip, ssh_port, root_usr, root_pwd)
    item_list.append(check_result)
    if check_result[check_result['key']] != 'SUCC':
        logger.error('为' + root_usr + '创建ssh客户端失败,停止检查')
        ret['comment'] = '为' + root_usr + '创建ssh客户端失败,停止检查'
        ret['endTime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        return ret
    server_check_items = [{'timeout': False, 'depend_cond': {}, 'result_regex_map': {'V24': script_24_support_version, 'V26': script_26_support_version}, 'command': 'python -V| grep -oP "(?<=^Python )\S+$"', 'key': 'PYTHON_VERSION', 'command_type': 'bash/shell', 'not_succ_to_break': True, 'desc': '检查服务器python版本', 'accept_result' : '^(V24|V26)$'},
                          {'timeout': False, 'depend_cond': {}, 'result_regex_map': {'CONSOLE_RIGHT': '^1234567890$'}, 'command': 'echo 1234567890', 'key': 'CONSOLE_CHECK', 'command_type': 'bash/shell', 'not_succ_to_break': True, 'desc': '检查服务器终端是否能够正确返回执行结果', 'accept_result' : '^CONSOLE_RIGHT$'},
                          {'timeout': False, 'depend_cond': {}, 'result_regex_map': {'HOSTS_EXIST': '^/etc/hosts$'},'command': 'ls /etc/hosts', 'key': 'HOSTS_EXIST_CHECK', 'command_type': 'bash/shell', 'not_succ_to_break': False, 'desc': '确认hosts文件存在', 'accept_result': '^HOSTS_EXIST'},
                          {'timeout': False, 'depend_cond': {}, 'result_regex_map': {'NOT_CONTENT_STANDBY_IP': '^\s*$'}, 'command': 'grep "' + stby_cfg.host_ip + '" /etc/hosts | grep -v "^\s*#"', 'key': 'HOSTS_CFG_RIGHT', 'command_type': 'bash/shell', 'not_succ_to_break': False, 'desc': 'hosts没有配置备库ip', 'accept_result': '^NOT_CONTENT_STANDBY_IP'},
                          {'timeout': False, 'depend_cond': {}, 'result_regex_map': {'BOND0_EXIST': '^/etc/sysconfig/network-scripts/ifcfg-bond0$'}, 'command': 'ls /etc/sysconfig/network-scripts/ifcfg-bond0', 'key': 'BOND0_EXIST_CHECK', 'command_type': 'bash/shell', 'not_succ_to_break': False, 'desc': '确认bond0文件存在', 'accept_result': '^BOND0_EXIST'},
                          {'timeout': True, 'depend_cond': {'TERMINAL_CONSOLE': 'SUCC'}, 'result_regex_map': {'SUCC': '.*The command completed successfully.*', 'TNS_NOT_START': '.*TNS-12541.*'}, 'command': 'lsnrctl status', 'key': 'TNS_START', 'command_type': 'bash/shell', 'not_succ_to_break': True, 'desc': '检查oracle的tns服务是否启动'}]


def check_dg_primary_oracle_status_old(pri_ora_cfg, stby_ora_cfg):
    """
    检查oracle的dg状态
    :param is_primary:被检查的oracle的database role是primay还是standby
    :param pri_app_cfg: primary oracle的配置
    :param stby_app_cfg: standby oracle的配置
    :return: oracle的dg状态检查结果,'OK'检查通过，'CONNECT_FAIL'连接服务器失败,'AUTH_FAIL'用户登录失败,以及oracle dg状态错误信息
    """
    ret = dict()
    ret['status'] = 'FALSE'
    ret['key'] = 'DG_PRIMARY_ORACLE_STATUS_CHECK'
    ret['startTime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    ret['desc'] = '检查dg oracle中primary oracle的运行状态以及相关配置是否同standby oracle配置匹配'
    ret['comment'] = ''
    item_list = list()
    ret['item_list'] = item_list
    ora_cfg = pri_ora_cfg
    rltd_ora_cfg = stby_ora_cfg
    host_ip = ora_cfg.server.host_ip
    check_result = __ping_test(host_ip)
    item_list.append(check_result)
    if check_result[check_result['key']] != 'SUCC':
        logger.error(host_ip + '服务器不在线，停止检查')
        ret['comment'] = '服务器不在线，停止检查'
        ret['endTime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        return ret
    root_usr = ora_cfg.root_user.user_name
    root_pwd = ora_cfg.root_user.pass_word
    ssh_port = ora_cfg.server.ssh_port
    check_result, conn = __create_ssh_connect(host_ip, ssh_port, root_usr, root_pwd)
    item_list.append(check_result)
    if check_result[check_result['key']] != 'SUCC':
        logger.error('为' + root_usr + '创建ssh客户端失败,停止检查')
        ret['comment'] = '为' + root_usr + '创建ssh客户端失败,停止检查'
        ret['endTime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        return ret
    check_result = __exec_check(conn, 'echo 1234567890', 'TERMINAL_CONSOLE', {'SUCC':'^1234567890$'}, "终端输出结果验证")
    item_list.append(check_result)
    if check_result[check_result['key']] != 'SUCC':
        logger.error('终端输出结果验证失败,停止检查')
        ret['comment'] = '终端输出结果验证失败,停止检查'
        ret['endTime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        return ret
    check_result = __exec_check(conn, 'python -V', 'TERMINAL_CONSOLE', {'SUCC':'^^Python \d.*\d$'}, "终端输出结果验证")
    item_list.append(check_result)
    if check_result[check_result['key']] != 'SUCC':
        logger.error('服务器python版本验证失败')
        ret['comment'] = '服务器python版本验证失败'
        ret['endTime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        return ret
    py_version = check_result['output'].replace('Python ', '')
    if script_24_support_version.find('|' + py_version + '|') < 0 and script_26_support_version.find('|' + py_version + '|') < 0 and script_3_support_version.find('|' + py_version + '|') < 0:
        logger.error('目前应用不支持' + py_version + '版本python')
        check_result[check_result['key']] = 'FAIL'
        ret['comment'] = '目前应用不支持' + py_version + '版本python'
        ret['endTime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        return ret
    check_result = __exec_check(conn, 'service NetworkManager status', 'NETWOKRMANAGER_NOT_START', {'SUCC':'^^(?\!.*(pid\s+\d+))'}, "验证NetworkManager服务未被启动")
    item_list.append(check_result)
    check_result = __exec_check(conn, 'hostname', 'HOST_NAME', {'SUCC':'^' + ora_cfg.server.host_name + '$'}, '服务器名是否配置正确')
    item_list.append(check_result)
    check_result = __exec_check(conn, 'ls /etc/hosts', 'HOSTS_EXIST', {'SUCC':'^/etc/hosts$'}, 'hosts文件是否存在')
    item_list.append(check_result)
    check_result = __exec_check(conn, 'grep "' + stby_cfg.host_ip + '" /etc/hosts | grep -v "^\s*#"', 'HOSTS_NOT_CONTENT_STBY_IP', {'SUCC':'^$'}, '确认hosts文件不能配置备机ip')
    item_list.append(check_result)
    check_result = __exec_check(conn, 'ls /etc/sysconfig/network-scripts/ifcfg-bond0', 'BOND0_EXIST', {'SUCC':'^/etc/sysconfig/network-scripts/ifcfg-bond0$'}, 'bond0文件是否存在')
    item_list.append(check_result)
    logger.info('root用户相关检查完成')
    conn.close()
    ora_usr = ora_cfg.app_user.user_name
    ora_usr_pwd = ora_cfg.app_user.pass_word
    check_result, conn = __create_ssh_connect(host_ip, ssh_port, ora_usr, ora_usr_pwd)
    item_list.append(check_result)
    if check_result[check_result['key']] != 'SUCC':
        logger.error('为' + ora_usr + '创建ssh客户端失败,停止检查')
        ret['comment'] = '为' + ora_usr + '创建ssh客户端失败,停止检查'
        ret['endTime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        return ret
    base_path = ora_cfg.base_path
    bin_path = base_path + '/bin/lsnrctl'
    bin_path = bin_path.replaceAll('//', '/')
    check_result = __exec_check(conn, 'ls ' + bin_path, 'BASE_PATH_RIGHT', {'SUCC':'^' + bin_path + '$'}, '验证base_path配置正确')
    item_list.append(check_result)
    tnsnames_path = base_path + '/network/admin/tnsnames.ora'
    tnsnames_path = tnsnames_path.replace('//', '/')
    check_result = __exec_check(conn, 'ls ' + tnsnames_path, 'TNSNAMES_EXIST', {'SUCC':'^' + tnsnames_path + '$'}, '检查tnsnames.ora是否存在')
    item_list.append(check_result)
    if check_result[check_result['key']] == 'SUCC':
        check_result = __exec_check(conn, 'grep -v "\s*#" ' + tnsnames_path + '|grep -oP "(?<=HOST)\s*=\s*\S+\s*(?=\))"|grep -oP "(?<==).*"|grep -vP "^\s*\d+\.\d+\.\d+\.\d+\s*"' ,
                                    'TNSNAMES_NOT_CONTENT_HOSTNAME', {'SUCC': '^\s*$'}, '确认tnsnames.ora配置中的HOST不能是主机名')
        item_list.append(check_result)
    listener_path = base_path + '/network/admin/listener.ora'
    listener_path = tnsnames_path.replace('//', '/')
    check_result = __exec_check(conn, 'ls ' + listener_path, 'LISTENER_EXIST', {'SUCC':'^' + listener_path + '$','NOT_EXIST':'^ls.+'}, '检查tnsnames.ora是否存在')
    item_list.append(check_result)
    if check_result[check_result['key']] == 'SUCC':
        check_result = __exec_check(conn, 'grep -v "^\s*#" ' + listener_path + '|grep -oP "(?<=HOST)\s*=\s*\S+\s*(?=\))"|grep -oP "(?<==).*"|grep -E "^\s*(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\s*$"' ,
                                    'LISTENER_NOT_CONTENT_IP', {'SUCC': '^\s*$'}, '确认listener.ora配置中的HOST不能是ip')
        item_list.append(check_result)
    check_result = __timeout_exec_check(conn, 'lsnrctl status', 'TNS_START', {'TNS_NOT_START':'.*TNS-12541.*', 'SUCC':'The command completed successfully'}, '检查oracle的tns服务是否启动')
    item_list.append(check_result)
    if check_result[check_result['key']] != 'SUCC':
        logger.error('oracle的tns服务检查失败:' + check_result[check_result['key'] + ',结束当前检查')
        conn.close()
        ret['comment'] = 'oracle的tns服务检查失败:' + check_result[check_result['key'] + ',结束当前检查'
        ret['endTime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        return ret
    check_result = __timeout_exec_check(conn, 'sqlplus -s / as sysdba <<EOF\nselect instance_name,host_name,startup_time,status,database_status from v\\$instance;\nEOF', 'ORACLE_STARTUP', {'SUCC':'.*OPEN.*ACTIVE.*', 'SHUTDOWN':'.*ORA-01034.*'}, '检查oracle数据库是否启动', script_type='oracle/sql')
    item_list.append(check_result)
    if check_result[check_result['key']] != 'SUCC':
        logger.error('oracle数据库启动检查失败:' + check_result[check_result['key'] + ',结束当前检查')
        conn.close()
        ret['comment'] = 'oracle数据库启动检查失败:' + check_result[check_result['key']
        ret['endTime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        return ret
    check_result = __exec_check(conn, 'sqlplus -s / as sysdba <<EOF\nselect database_role from v\\$database;\nEOF', 'DATABASE_ROLE_CHECK', {'SUCC':'.*OPEN.*ACTIVE.*', 'SHUTDOWN':'.*ORA-01034.*'}, '检查oracle数据库是否启动', script_type='oracle/sql')
    item_list.append(check_result)


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

