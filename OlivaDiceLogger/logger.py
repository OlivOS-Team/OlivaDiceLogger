# -*- encoding: utf-8 -*-
r"""
_______________________    _________________________________________
__  __ \__  /____  _/_ |  / /__    |__  __ \___  _/_  ____/__  ____/
_  / / /_  /  __  / __ | / /__  /| |_  / / /__  / _  /    __  __/
/ /_/ /_  /____/ /  __ |/ / _  ___ |  /_/ /__/ /  / /___  _  /___
\____/ /_____/___/  _____/  /_/  |_/_____/ /___/  \____/  /_____/

@File      :   logger.py
@Author    :   lunzhiPenxil仑质
@Contact   :   lunzhipenxil@gmail.com
@License   :   AGPL
@Copyright :   (C) 2020-2026, OlivOS-Team
@Desc      :   None
"""

import OlivaDiceCore
import OlivaDiceLogger

import time
import uuid
import re
import json
import os
import glob
import traceback
import threading
import requests as req
from functools import wraps

gLoggerIOLockMap = {}


def safe_text(value):
    """只转义孤立 Unicode 代理字符，保持正常文本原样写入。"""
    if not isinstance(value, str):
        return value
    try:
        return value.encode('utf-8', errors='backslashreplace').decode('utf-8')
    except Exception:
        return repr(value)


def check_and_process_compatibility():
    # 兼容改为创建文件，只做一次，之后不做
    dataPath = OlivaDiceLogger.data.dataPath
    dataLogPath = OlivaDiceLogger.data.dataLogPath
    compatibility_dir = f'{dataPath}{dataLogPath}{OlivaDiceLogger.data.dataCompatibilityPath}'
    compatibility_flag = f'{compatibility_dir}/{OlivaDiceLogger.data.dataCompatibilityFlagFile}'
    if os.path.exists(compatibility_flag):
        return
    if not os.path.exists(compatibility_dir):
        os.makedirs(compatibility_dir)
    # 执行兼容性处理
    migrate_database_config()
    log_dir = f'{dataPath}{dataLogPath}'
    if os.path.exists(log_dir):
        for ext in ['.olivadicelog', '.trpglog', '_temp.trpglog']:
            pattern = os.path.join(log_dir, f'*{ext}')
            for filepath in glob.glob(pattern):
                filename = os.path.basename(filepath)
                if '_' not in filename.replace('log_', '', 1):
                    base_name = filename[: -len(ext)]
                    clean_name = base_name.replace('log_', '', 1)
                    new_name = f'log_{clean_name}_default{ext}'
                    new_path = os.path.join(log_dir, new_name)
                    if not os.path.exists(new_path):
                        os.rename(filepath, new_path)
    with open(compatibility_flag, 'w', encoding='utf-8') as f:
        f.write(f'已成功于[{time.strftime("%Y-%m-%d %H:%M:%S")}]执行日志文件兼容性处理')


def migrate_database_config():
    for userHash in OlivaDiceCore.userConfig.dictUserConfigData:
        for botHash in OlivaDiceCore.userConfig.dictUserConfigData[userHash]:
            config = OlivaDiceCore.userConfig.dictUserConfigData[userHash][botHash]
            if config.get('userType', '') != 'group':
                continue
            config_note = config.get('configNote')
            if not isinstance(config_note, dict):
                config_note = {}
                config['configNote'] = config_note
            logNowName = config_note.get('logNowName')
            logNameList = config_note.get('logNameList', [])
            logNameTimeDict = config_note.get('logNameTimeDict', {})
            if not isinstance(logNameList, list):
                logNameList = []
            if not isinstance(logNameTimeDict, dict):
                logNameTimeDict = {}
            config_note['logNameList'] = logNameList
            config_note['logNameTimeDict'] = logNameTimeDict
            if logNowName and not logNameList:
                # 从logNowName提取UUID（去掉"log_"前缀）
                log_uuid = logNowName.replace('log_', '', 1)
                # 设置default
                config_note['logActiveName'] = 'default'
                config_note['logNameList'] = ['default']
                config_note['logNameDict'] = {'default': log_uuid}
                config_note['logNameTimeDict']['default'] = {'start_time': 0, 'end_time': 0, 'total_time': 0}
                config_note['logNowName'] = None
                OlivaDiceCore.userConfig.listUserConfigDataUpdate.append(userHash)
            if logNameList:
                # 时间兼容
                for name in logNameList:
                    if name not in logNameTimeDict:
                        logNameTimeDict[name] = {'start_time': 0, 'end_time': 0, 'total_time': 0}
                config_note['logNameTimeDict'] = logNameTimeDict
                OlivaDiceCore.userConfig.listUserConfigDataUpdate.append(userHash)

    for userHash in set(OlivaDiceCore.userConfig.listUserConfigDataUpdate):
        OlivaDiceCore.userConfig.writeUserConfigByUserHash(userHash)
    OlivaDiceCore.userConfig.listUserConfigDataUpdate = []


def init_logger(plugin_event, Proc):
    releaseDir('%s%s' % (OlivaDiceLogger.data.dataPath, OlivaDiceLogger.data.dataLogPath))
    check_and_process_compatibility()
    OlivaDiceCore.crossHook.dictHookFunc['msgHook'] = add_logger_func(OlivaDiceCore.crossHook.dictHookFunc['msgHook'])
    try:
        import OlivOSOnebotV11

        OlivOSOnebotV11.eventRouter.txEvent.doRouter = add_logger_lazy_reply_func(
            OlivOSOnebotV11.eventRouter.txEvent.doRouter
        )
    except Exception:
        traceback.print_exc()


# 时间函数
def format_duration(seconds):
    if seconds <= 0:
        return '0s'

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    res = ''

    if hours > 0:
        res += f'{hours}h'
    if minutes > 0:
        res += f'{minutes}m'
    if seconds > 0:
        res += f'{seconds}s'

    return res


def add_logger_lazy_reply_func(target_func):
    @wraps(target_func)
    def logger_func(self_arg):
        res = target_func(self_arg)
        try:
            loggerEntryLazyReply(self_arg)
        except Exception:
            traceback.print_exc()
        return res

    return logger_func


def loggerEntryLazyReply(self_arg):
    try:
        import OlivOSOnebotV11

        tmp_event = None
        tmp_funcType = None
        tmp_sender = None
        tmp_dectData = None
        tmp_message = None
        if self_arg.funcType in ['send_msg']:
            if self_arg.params['message_type'] == 'private':
                pass
            elif self_arg.params['message_type'] == 'group':
                tmp_funcType = 'send_group'
        elif self_arg.funcType in ['send_private_msg']:
            pass
        elif self_arg.funcType in ['send_group_msg']:
            tmp_funcType = 'send_group'
        if tmp_funcType == 'send_group':
            tmp_botHash = self_arg.plugin_event.bot_info.hash
            tmp_sender = {'id': str(self_arg.plugin_event.bot_info.id), 'name': 'Bot'}
            tmp_groupId = str(self_arg.params['group_id'])
            tmp_event = self_arg.plugin_event
            tmp_event_new = OlivOSOnebotV11.eventRouter.getEventRegDict(
                botHash=tmp_botHash, key=f'group_message/{tmp_groupId}'
            )
            if tmp_event_new is not None:
                tmp_event = tmp_event_new
            tmp_hostId = OlivOSOnebotV11.eventRouter.getHostIdDict(botHash=tmp_botHash, groupId=tmp_groupId)
            tmp_groupId = OlivOSOnebotV11.eventRouter.getMappingIdDict(tmp_botHash, tmp_groupId)
            tmp_hostId = OlivOSOnebotV11.eventRouter.getMappingIdDict(tmp_botHash, tmp_hostId)
            if tmp_hostId == 'None':
                tmp_hostId = None
            tmp_dectData = [tmp_hostId, tmp_groupId, None]
            tmp_message = OlivOSOnebotV11.eventRouter.paraRvMapper(self_arg.params['message']).get('old_string')
        if (
            tmp_event is not None
            and tmp_funcType is not None
            and tmp_sender is not None
            and tmp_dectData is not None
            and tmp_message is not None
        ):
            loggerEntry(tmp_event, tmp_funcType, tmp_sender, tmp_dectData, tmp_message)
    except Exception:
        traceback.print_exc()


# 记录日志时撤回添加撤回标记
def handle_message_recall(event):
    try:
        message_id = event.data.message_id
        group_id = event.data.group_id
        botHash = event.bot_info.hash
        try:
            import OlivOSOnebotV11

            host_id = OlivOSOnebotV11.eventRouter.getHostIdDict(botHash=botHash, groupId=group_id)
        except Exception:
            host_id = None
        tmp_hagID = f'{host_id}|{group_id}' if host_id else str(group_id)

        if not OlivaDiceCore.userConfig.getUserConfigByKey(
            userId=tmp_hagID,
            userType='group',
            platform=event.platform['platform'],
            userConfigKey='logEnable',
            botHash=event.bot_info.hash,
        ):
            return

        log_name = OlivaDiceCore.userConfig.getUserConfigByKey(
            userId=tmp_hagID,
            userType='group',
            platform=event.platform['platform'],
            userConfigKey='logActiveName',
            botHash=event.bot_info.hash,
        )
        if not log_name:
            return

        log_name_dict = (
            OlivaDiceCore.userConfig.getUserConfigByKey(
                userId=tmp_hagID,
                userType='group',
                platform=event.platform['platform'],
                userConfigKey='logNameDict',
                botHash=event.bot_info.hash,
            )
            or {}
        )
        log_uuid = log_name_dict.get(log_name, str(uuid.uuid4()))
        tmp_logName = f'log_{log_uuid}_{log_name}'
        log_file = f'{OlivaDiceLogger.data.dataPath}{OlivaDiceLogger.data.dataLogPath}/{tmp_logName}.olivadicelog'

        if not os.path.exists(log_file):
            return

        if log_file not in gLoggerIOLockMap:
            gLoggerIOLockMap[log_file] = threading.Lock()

        with gLoggerIOLockMap[log_file]:
            updated_lines = []
            modified = False
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        log_entry = json.loads(line.strip())
                        if str(log_entry.get('message_id')) == str(message_id):
                            log_entry['deleted'] = True
                            modified = True
                        updated_lines.append(json.dumps(log_entry, ensure_ascii=False) + '\n')
                    except json.JSONDecodeError:
                        continue

            if modified:
                with open(log_file, 'w', encoding='utf-8') as f:
                    f.writelines(updated_lines)

    except Exception:
        traceback.print_exc()


def add_logger_func(target_func):
    @wraps(target_func)
    def logger_func(*arg, **kwargs):
        res = target_func(*arg, **kwargs)
        loggerEntry(*arg, **kwargs)
        return res

    return logger_func


def is_valid_log_name(name):
    if re.search(r'(?:[\\/:*?"<>|\[\]\x00-\x1F]|&#(?:91|93)|&amp)', name):
        return False

    if name.endswith('.'):
        return False

    return True


def get_log_lines(log_name):
    dataPath = OlivaDiceLogger.data.dataPath
    dataLogPath = OlivaDiceLogger.data.dataLogPath
    dataLogFile = '%s%s/%s.olivadicelog' % (dataPath, dataLogPath, log_name)

    if not os.path.exists(dataLogFile):
        return 0

    try:
        with open(dataLogFile, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            return len(lines)
    except Exception:
        return 0


def check_log_file_exists(log_name):
    dataPath = OlivaDiceLogger.data.dataPath
    dataLogPath = OlivaDiceLogger.data.dataLogPath
    olivadicelog_file = f'{dataPath}{dataLogPath}/{log_name}.olivadicelog'
    trpglog_file = f'{dataPath}{dataLogPath}/{log_name}.trpglog'
    return os.path.exists(olivadicelog_file) and os.path.exists(trpglog_file)


def extract_forward_id_list(tmp_message):
    """从old_string消息文本中提取合并转发消息ID列表"""
    if not isinstance(tmp_message, str):
        return []
    return re.findall(r'\[CQ:forward,id=([^\[\]\s]+)\]', tmp_message)


def remove_forward_code(tmp_message):
    """移除消息中的合并转发CQ码, 返回剩余文本"""
    if not isinstance(tmp_message, str):
        return str(tmp_message)
    return re.sub(r'\[CQ:forward,id=[^\[\]\s]+\]', '', tmp_message)


def format_forward_segment(tmp_seg):
    """把单个消息段(dict或str)转为old_string(CQ码)文本"""
    if isinstance(tmp_seg, str):
        return tmp_seg
    if not isinstance(tmp_seg, dict):
        return str(tmp_seg)
    tmp_type = tmp_seg.get('type')
    tmp_data = tmp_seg.get('data')
    if not isinstance(tmp_data, dict):
        tmp_data = tmp_seg
    if tmp_type == 'text' or (tmp_type is None and 'text' in tmp_data):
        return str(tmp_data.get('text', ''))
    if tmp_type == 'at':
        return '[CQ:at,qq=%s]' % tmp_data.get('qq', tmp_data.get('id', 'all'))
    if tmp_type == 'face':
        return '[CQ:face,id=%s]' % tmp_data.get('id', '0')
    if tmp_type in ['image']:
        return '[CQ:image,file=%s]' % tmp_data.get('file', tmp_data.get('file_id', tmp_data.get('uri', '')))
    if tmp_type in ['record', 'voice', 'audio']:
        return '[CQ:record,file=%s]' % tmp_data.get('file', tmp_data.get('file_id', tmp_data.get('uri', '')))
    if tmp_type == 'video':
        return '[CQ:video,file=%s]' % tmp_data.get('file', tmp_data.get('file_id', tmp_data.get('uri', '')))
    if tmp_type == 'reply':
        return '[CQ:reply,id=%s]' % tmp_data.get('id', '')
    if tmp_type == 'forward':
        return '[CQ:forward,id=%s]' % tmp_data.get('id', tmp_data.get('forward_id', ''))
    if tmp_type == 'json':
        return '[CQ:json,data=%s]' % tmp_data.get('data', '')
    if tmp_type == 'xml':
        return '[CQ:xml,data=%s]' % tmp_data.get('data', '')
    if tmp_type is None:
        return str(tmp_data)
    return '[CQ:%s]' % tmp_type


def format_forward_content(tmp_content):
    """把合并转发节点的content(str/list/其他)统一转为old_string文本"""
    if isinstance(tmp_content, str):
        return tmp_content
    if isinstance(tmp_content, list):
        return ''.join([format_forward_segment(x) for x in tmp_content if x is not None])
    return str(tmp_content)


def get_forward_node_list(plugin_event, forward_id):
    """通过平台接口拉取合并转发节点列表，失败时返回None"""
    tmp_res = None
    try:
        tmp_res = plugin_event.get_forward_msg(forward_id)
    except Exception:
        return None
    if not isinstance(tmp_res, dict):
        return None
    if not tmp_res.get('active', False):
        return None
    tmp_messages = tmp_res.get('data', {}).get('messages', None)
    if isinstance(tmp_messages, list) and len(tmp_messages) > 0:
        return tmp_messages
    return None


def get_forward_node_field(tmp_data, key_list):
    """按优先级从节点数据中取第一个非空字段"""
    for key_this in key_list:
        if key_this in tmp_data and tmp_data[key_this] is not None:
            return tmp_data[key_this]
    return None


def decode_forward_nodes(tmp_node_list):
    """把各协议端形态不一的合并转发节点列表统一解析为
    [{'user_id':..., 'name':..., 'message':..., 'time':...}]，无法解析的节点跳过"""
    tmp_res = []
    if not isinstance(tmp_node_list, list):
        return tmp_res
    for tmp_node in tmp_node_list:
        try:
            if not isinstance(tmp_node, dict):
                continue
            tmp_node_data = tmp_node.get('data')
            if not isinstance(tmp_node_data, dict):
                tmp_node_data = tmp_node
            tmp_user_id = get_forward_node_field(tmp_node_data, ['user_id', 'uin', 'uid', 'id'])
            tmp_name = get_forward_node_field(tmp_node_data, ['nickname', 'name', 'sender_name', 'user_name'])
            tmp_content = get_forward_node_field(tmp_node_data, ['content', 'message', 'text', 'segments', 'msg'])
            tmp_time = get_forward_node_field(tmp_node_data, ['time'])
            if tmp_content is None:
                continue
            tmp_message = format_forward_content(tmp_content)
            if str(tmp_message).strip() == '':
                continue
            if tmp_user_id is None:
                tmp_user_id = -1
            if tmp_name is None:
                tmp_name = 'N/A'
            if not isinstance(tmp_time, int):
                tmp_time = None
            tmp_res.append(
                {
                    'user_id': tmp_user_id,
                    'name': safe_text(str(tmp_name)),
                    'message': safe_text(str(tmp_message)),
                    'time': tmp_time,
                }
            )
        except Exception:
            continue
    return tmp_res


def count_forward_nodes(tmp_node_list):
    """统计合并转发节点列表中可解析的节点总数, 用于判断是否存在解码失败的节点"""
    if not isinstance(tmp_node_list, list):
        return 0
    tmp_count = 0
    for tmp_node in tmp_node_list:
        if isinstance(tmp_node, dict):
            tmp_count += 1
    return tmp_count


def write_log_entry(data_log_file, log_dict):
    """线程安全地追加一条日志记录"""
    if data_log_file not in gLoggerIOLockMap:
        gLoggerIOLockMap[data_log_file] = threading.Lock()
    loggerIOLock = gLoggerIOLockMap[data_log_file]
    loggerIOLock.acquire()
    try:
        with open(data_log_file, 'a+', encoding='utf-8') as dataLogFile_f:
            dataLogFile_f.write('%s\n' % json.dumps(log_dict, ensure_ascii=False))
    finally:
        loggerIOLock.release()


def loggerEntry(event, funcType, sender, dectData, message):
    [host_id, group_id, user_id] = dectData
    tmp_hagID = None
    if host_id is not None and group_id is not None:
        tmp_hagID = '%s|%s' % (str(host_id), str(group_id))
    elif group_id is not None:
        tmp_hagID = str(group_id)
    tmp_name = 'N/A'
    tmp_id = -1
    if 'name' in sender:
        tmp_name = sender['name']
    if 'id' in sender:
        tmp_id = sender['id']
    if funcType in ['recv', 'reply_private', 'reply', 'send_group']:
        active_log_name = OlivaDiceCore.userConfig.getUserConfigByKey(
            userId=tmp_hagID,
            userType='group',
            platform=event.platform['platform'],
            userConfigKey='logActiveName',
            botHash=event.bot_info.hash,
        )
        if active_log_name and OlivaDiceCore.userConfig.getUserConfigByKey(
            userId=tmp_hagID,
            userType='group',
            platform=event.platform['platform'],
            userConfigKey='logEnable',
            botHash=event.bot_info.hash,
        ):
            # 检查事件是否有 message_id，如果没有则跳过
            if not hasattr(event, 'data') or not hasattr(event.data, 'message_id'):
                return
            message_id = event.data.message_id
            message_ref_idx = None
            if event.platform['sdk'] == 'qqGuildv2_link':
                extend_data = getattr(event.data, 'extend', None)
                if isinstance(extend_data, dict):
                    qq_msg_idx = extend_data.get('qq_msg_idx', None)
                    if qq_msg_idx is not None and str(qq_msg_idx).startswith('REFIDX_'):
                        message_ref_idx = str(qq_msg_idx)

            # 检查是否启用使用角色卡名字功能
            log_use_pc_name = OlivaDiceCore.userConfig.getUserConfigByKey(
                userId=tmp_hagID,
                userType='group',
                platform=event.platform['platform'],
                userConfigKey='logUsePcName',
                botHash=event.bot_info.hash,
            )
            if log_use_pc_name and funcType == 'recv':
                try:
                    tmp_pcHash = OlivaDiceCore.pcCard.getPcHash(tmp_id, event.platform['platform'])
                    tmp_pc_name = OlivaDiceCore.pcCard.pcCardDataGetSelectionKey(tmp_pcHash, hagId=tmp_hagID)
                    if tmp_pc_name:
                        tmp_name = tmp_pc_name
                except Exception:
                    pass

            log_dict = {
                'time': int(time.mktime(time.localtime())),
                'type': funcType,
                'message_id': message_id,
                'message_ref_idx': message_ref_idx,
                'deleted': False,
                'dect': {
                    'host_id': host_id,
                    'group_id': group_id,
                    'user_id': user_id,
                },
                'sender': {'id': tmp_id, 'name': safe_text(tmp_name)},
                'message': safe_text(message),
            }
            log_name_dict = (
                OlivaDiceCore.userConfig.getUserConfigByKey(
                    userId=tmp_hagID,
                    userType='group',
                    platform=event.platform['platform'],
                    userConfigKey='logNameDict',
                    botHash=event.bot_info.hash,
                )
                or {}
            )
            tmp_log_uuid = log_name_dict.get(active_log_name, str(uuid.uuid4()))
            tmp_logName = f'log_{tmp_log_uuid}_{active_log_name}'
            dataPath = OlivaDiceLogger.data.dataPath
            dataLogPath = OlivaDiceLogger.data.dataLogPath
            dataLogFile = '%s%s/%s.olivadicelog' % (dataPath, dataLogPath, tmp_logName)

            # 合并转发转写: 群开启logForward开关时, 把合并转发记录转成正常的人物和消息写入
            tmp_log_dict_list = [log_dict]
            if funcType == 'recv' and len(extract_forward_id_list(message)) > 0:
                log_forward = OlivaDiceCore.userConfig.getUserConfigByKey(
                    userId=tmp_hagID,
                    userType='group',
                    platform=event.platform['platform'],
                    userConfigKey='logForward',
                    botHash=event.bot_info.hash,
                )
                if log_forward:
                    tmp_entry_list = []
                    tmp_node_total = 0
                    for tmp_forward_id in extract_forward_id_list(message):
                        tmp_node_list = get_forward_node_list(event, tmp_forward_id)
                        tmp_node_total += count_forward_nodes(tmp_node_list)
                        tmp_entry_list.extend(decode_forward_nodes(tmp_node_list))
                    if len(tmp_entry_list) > 0:
                        tmp_log_dict_list = []
                        # 存在解码失败的节点时保留原始记录兜底, 否则只保留非转发的剩余文本
                        if len(tmp_entry_list) < tmp_node_total:
                            tmp_fallback_message = message
                        else:
                            tmp_fallback_message = remove_forward_code(message)
                        tmp_fallback_message = tmp_fallback_message.strip()
                        if tmp_fallback_message != '':
                            tmp_log_dict_list.append(
                                {
                                    'time': log_dict['time'],
                                    'type': funcType,
                                    'message_id': message_id,
                                    'message_ref_idx': message_ref_idx,
                                    'deleted': False,
                                    'dect': log_dict['dect'],
                                    'sender': log_dict['sender'],
                                    'message': safe_text(tmp_fallback_message),
                                }
                            )
                        for tmp_entry in tmp_entry_list:
                            tmp_entry_time = tmp_entry['time']
                            if tmp_entry_time is None:
                                tmp_entry_time = int(time.mktime(time.localtime()))
                            tmp_log_dict_list.append(
                                {
                                    'time': tmp_entry_time,
                                    'type': 'recv',
                                    # 继承原消息标识, 保证引用功能可用且撤回可覆盖转写内容
                                    'message_id': message_id,
                                    'message_ref_idx': message_ref_idx,
                                    'deleted': False,
                                    'dect': {
                                        'host_id': host_id,
                                        'group_id': group_id,
                                        'user_id': tmp_entry['user_id'],
                                    },
                                    'sender': {
                                        'id': tmp_entry['user_id'],
                                        'name': tmp_entry['name'],
                                    },
                                    'message': tmp_entry['message'],
                                }
                            )
            for tmp_log_dict_this in tmp_log_dict_list:
                write_log_entry(dataLogFile, tmp_log_dict_this)
    pass


def init_log_file(logName):
    dataPath = OlivaDiceLogger.data.dataPath
    dataLogPath = OlivaDiceLogger.data.dataLogPath
    dataLogFile = '%s%s/%s.olivadicelog' % (dataPath, dataLogPath, logName)
    try:
        # 如果文件不存在,创建并添加初始的duration记录
        if not os.path.exists(dataLogFile):
            if dataLogFile not in gLoggerIOLockMap:
                gLoggerIOLockMap[dataLogFile] = threading.Lock()

            with gLoggerIOLockMap[dataLogFile]:
                total_record = {'type': 'log_total_duration', 'total_time': 0}
                with open(dataLogFile, 'w', encoding='utf-8') as f:
                    f.write(json.dumps(total_record, ensure_ascii=False) + '\n')
        else:
            # 文件已存在,检查是否有duration记录
            has_duration = False
            with open(dataLogFile, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        log_entry = json.loads(line.strip())
                        if log_entry.get('type') == 'log_total_duration':
                            has_duration = True
                            break
                    except Exception:
                        continue
            # 如果没有duration记录,在开头添加
            if not has_duration:
                if dataLogFile not in gLoggerIOLockMap:
                    gLoggerIOLockMap[dataLogFile] = threading.Lock()
                with gLoggerIOLockMap[dataLogFile]:
                    with open(dataLogFile, 'r', encoding='utf-8') as f:
                        existing_content = f.read()
                    total_record = {'type': 'log_total_duration', 'total_time': 0}
                    with open(dataLogFile, 'w', encoding='utf-8') as f:
                        f.write(json.dumps(total_record, ensure_ascii=False) + '\n')
                        f.write(existing_content)
    except Exception:
        traceback.print_exc()


def update_log_total_duration(dataLogFile, total_duration):
    """更新olivadicelog文件中的log_total_duration条目"""
    try:
        if dataLogFile not in gLoggerIOLockMap:
            gLoggerIOLockMap[dataLogFile] = threading.Lock()

        with gLoggerIOLockMap[dataLogFile]:
            updated_lines = []
            duration_updated = False

            with open(dataLogFile, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        log_entry = json.loads(line.strip())
                        if log_entry.get('type') == 'log_total_duration':
                            log_entry['total_time'] = total_duration
                            duration_updated = True
                        updated_lines.append(json.dumps(log_entry, ensure_ascii=False) + '\n')
                    except json.JSONDecodeError:
                        updated_lines.append(line)
            # 如果没有找到duration记录,添加一个(理论上不应该发生)
            if not duration_updated:
                total_record = {'type': 'log_total_duration', 'total_time': total_duration}
                updated_lines.insert(0, json.dumps(total_record, ensure_ascii=False) + '\n')
            with open(dataLogFile, 'w', encoding='utf-8') as f:
                f.writelines(updated_lines)
    except Exception:
        traceback.print_exc()


def read_log_total_time_from_file(log_uuid):
    """
    从 .olivadicelog 文件读取累计时长。
    优先读文件头 log_total_duration 记录的 total_time；
    若 total_time 为 0（从未成功 off），则 fallback 到首条与末条消息的时间差。
    返回 float（秒），文件不存在返回 None。
    """
    dataPath = OlivaDiceLogger.data.dataPath
    dataLogPath = OlivaDiceLogger.data.dataLogPath
    log_dir = dataPath + dataLogPath
    log_files = glob.glob(f'{log_dir}/log_{log_uuid}_*.olivadicelog')
    if not log_files:
        return None
    try:
        total_time = 0
        first_msg_time = None
        last_msg_time = None
        with open(log_files[0], 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except (json.JSONDecodeError, ValueError):
                    continue
                if record.get('type') == 'log_total_duration':
                    total_time = record.get('total_time', 0)
                elif 'time' in record:
                    if first_msg_time is None:
                        first_msg_time = record['time']
                    last_msg_time = record['time']
        # total_time > 0 说明有成功 off 过，累计值可信
        if total_time > 0:
            return total_time
        # total_time == 0：从未成功 off，用首尾时间差近似
        if first_msg_time is not None and last_msg_time is not None:
            return last_msg_time - first_msg_time
        return 0
    except Exception:
        return 0


def releaseLogFile(logName, total_duration=0, temp=False):
    dataPath = OlivaDiceLogger.data.dataPath
    dataLogPath = OlivaDiceLogger.data.dataLogPath
    if temp:
        dataLogFile_1 = '%s%s/%s_temp.trpglog' % (dataPath, dataLogPath, logName)
    else:
        dataLogFile_1 = '%s%s/%s.trpglog' % (dataPath, dataLogPath, logName)
    dataLogFile = '%s%s/%s.olivadicelog' % (dataPath, dataLogPath, logName)
    if not os.path.exists(dataLogFile):
        return False
    tmp_dataLogFile = None
    try:
        # 更新olivadicelog中的总时长记录
        update_log_total_duration(dataLogFile, total_duration)
        with open(dataLogFile, 'r+', encoding='utf-8', errors='ignore') as dataLogFile_f:
            tmp_dataLogFile = dataLogFile_f.read()
        if tmp_dataLogFile:
            tmp_dataLogFile = tmp_dataLogFile.strip('\n')
            tmp_dataLogFile_list = tmp_dataLogFile.split('\n')
            res_logFile_str = ''
            for tmp_dataLogFile_list_this in tmp_dataLogFile_list:
                tmp_dataLog_json = None
                try:
                    tmp_dataLog_json = json.loads(tmp_dataLogFile_list_this)
                except Exception:
                    tmp_dataLog_json = None
                if tmp_dataLog_json:
                    # 跳过已删除消息和总时长记录
                    if tmp_dataLog_json.get('deleted', False):
                        continue
                    if tmp_dataLog_json.get('type') == 'log_total_duration':
                        continue
                    res_logFile_str += '%s(%s) %s\n%s\n' % (
                        str(tmp_dataLog_json['sender']['name']),
                        str(tmp_dataLog_json['sender']['id']),
                        str(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(tmp_dataLog_json['time']))),
                        str(tmp_dataLog_json['message']),
                    )
            with open(dataLogFile_1, 'w+', encoding='utf-8') as dataLogFile_f:
                dataLogFile_f.write(res_logFile_str)
            return True
    except Exception:
        traceback.print_exc()
        return False
    return False


def uploadLogFile(logName, timeout=60):
    dataPath = OlivaDiceLogger.data.dataPath
    dataLogPath = OlivaDiceLogger.data.dataLogPath
    dataLogFile = '%s%s/%s.olivadicelog' % (dataPath, dataLogPath, logName)  # NOQA: F841
    dataLogFile_1 = '%s%s/%s.trpglog' % (dataPath, dataLogPath, logName)
    tmp_dataLogFile = None
    with open(dataLogFile_1, 'rb') as dataLogFile_f:
        tmp_dataLogFile = dataLogFile_f.read()
        url = OlivaDiceLogger.data.dataLogUpload
        files = {'file': tmp_dataLogFile}
        data = {'name': logName}
        response = req.request(  # NOQA: F841
            'POST', url, files=files, data=data, proxies=OlivaDiceCore.webTool.get_system_proxy(), timeout=timeout
        )


def releaseDir(dir_path):
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)


def get_last_message_id(log_file_path):
    """获取日志文件中最后一个有效的message_id"""
    last_message_id = None
    if os.path.exists(log_file_path):
        try:
            with open(log_file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        log_entry = json.loads(line.strip())
                        if not log_entry.get('deleted', False) and 'message_id' in log_entry:
                            # 跳过无消息标识的合成条目(如历史版本写入的合并转发转写记录)
                            if log_entry['message_id'] is not None:
                                last_message_id = log_entry['message_id']
                    except Exception:
                        continue
        except Exception:
            pass
    return last_message_id


def get_last_message_ref_idx(log_file_path):
    """获取最后一条有效日志的 QQ Guild v2 引用索引。"""
    last_message_ref_idx = None
    if os.path.exists(log_file_path):
        try:
            with open(log_file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        log_entry = json.loads(line.strip())
                        if (
                            not log_entry.get('deleted', False)
                            and 'message_id' in log_entry
                            and log_entry['message_id'] is not None
                        ):
                            last_message_ref_idx = log_entry.get('message_ref_idx', None)
                    except Exception:
                        continue
        except Exception:
            pass
    return last_message_ref_idx


def write_status_to_file(log_uuid, status_data):
    """将统计数据写入status_uuid.json文件"""
    dataPath = OlivaDiceLogger.data.dataPath
    dataLogPath = OlivaDiceLogger.data.dataLogPath
    status_file = f'{dataPath}{dataLogPath}/status_{log_uuid}.json'
    try:
        with open(status_file, 'w', encoding='utf-8') as f:
            json.dump(status_data, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        traceback.print_exc()
        return False


def read_status_from_file(log_uuid):
    """从status_uuid.json文件读取统计数据"""
    dataPath = OlivaDiceLogger.data.dataPath
    dataLogPath = OlivaDiceLogger.data.dataLogPath
    status_file = f'{dataPath}{dataLogPath}/status_{log_uuid}.json'
    try:
        if os.path.exists(status_file):
            with open(status_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    except Exception:
        traceback.print_exc()
        return None


def normalize_log_status_config(raw_value):
    """将群组配置中的 logStatus 规范化为 dict。"""
    if isinstance(raw_value, dict):
        return raw_value
    return {}


def init_log_status(log_uuid, plugin_event, tmp_hagID):
    """初始化日志状态数据"""
    # 获取当前群组配置中的logStatus
    raw_log_status = OlivaDiceCore.userConfig.getUserConfigByKey(
        userId=tmp_hagID,
        userType='group',
        platform=plugin_event.platform['platform'],
        userConfigKey='logStatus',
        botHash=plugin_event.bot_info.hash,
    )

    log_status = normalize_log_status_config(raw_log_status)
    if log_status != raw_log_status:
        OlivaDiceCore.userConfig.setUserConfigByKey(
            userId=tmp_hagID,
            userType='group',
            platform=plugin_event.platform['platform'],
            userConfigKey='logStatus',
            userConfigValue=log_status,
            botHash=plugin_event.bot_info.hash,
        )

    # 如果该UUID不存在，则创建
    if log_uuid not in log_status:
        log_status[log_uuid] = {}
        OlivaDiceCore.userConfig.setUserConfigByKey(
            userId=tmp_hagID,
            userType='group',
            platform=plugin_event.platform['platform'],
            userConfigKey='logStatus',
            userConfigValue=log_status,
            botHash=plugin_event.bot_info.hash,
        )


def persist_log_status(log_uuid, plugin_event, tmp_hagID):
    """持久化日志状态数据到status_uuid.json"""
    raw_log_status = OlivaDiceCore.userConfig.getUserConfigByKey(
        userId=tmp_hagID,
        userType='group',
        platform=plugin_event.platform['platform'],
        userConfigKey='logStatus',
        botHash=plugin_event.bot_info.hash,
    )
    log_status = normalize_log_status_config(raw_log_status)
    if log_uuid in log_status:
        write_status_to_file(log_uuid, log_status[log_uuid])


def clear_log_status(log_uuid, plugin_event, tmp_hagID):
    """清除内存中的日志状态数据"""
    raw_log_status = OlivaDiceCore.userConfig.getUserConfigByKey(
        userId=tmp_hagID,
        userType='group',
        platform=plugin_event.platform['platform'],
        userConfigKey='logStatus',
        botHash=plugin_event.bot_info.hash,
    )
    log_status = normalize_log_status_config(raw_log_status)
    if log_uuid in log_status:
        del log_status[log_uuid]
        OlivaDiceCore.userConfig.setUserConfigByKey(
            userId=tmp_hagID,
            userType='group',
            platform=plugin_event.platform['platform'],
            userConfigKey='logStatus',
            userConfigValue=log_status,
            botHash=plugin_event.bot_info.hash,
        )


def get_log_status(log_uuid, plugin_event, tmp_hagID):
    """获取日志状态数据"""
    raw_log_status = OlivaDiceCore.userConfig.getUserConfigByKey(
        userId=tmp_hagID,
        userType='group',
        platform=plugin_event.platform['platform'],
        userConfigKey='logStatus',
        botHash=plugin_event.bot_info.hash,
    )
    log_status = normalize_log_status_config(raw_log_status)
    if log_uuid in log_status:
        return log_status[log_uuid]

    # 从文件中读取
    return read_status_from_file(log_uuid)


def format_user_stat_data(user_data, bot_hash, dictStrCustom):
    """格式化单个用户的统计数据"""
    if not user_data or '人物卡' not in user_data:
        return None, 0, 0, []

    success_format = dictStrCustom['strLoggerStatSuccessFormat']
    fail_format = dictStrCustom['strLoggerStatFailFormat']
    pc_card_format = dictStrCustom['strLoggerStatPcCardFormat']
    success_label = dictStrCustom['strLoggerStatSuccessLabel']
    fail_label = dictStrCustom['strLoggerStatFailLabel']
    pc_card_separator = dictStrCustom['strLoggerStatPcCardSeparator']

    pc_cards_data = []
    total_success = 0
    total_fail = 0

    for pc_name, pc_data in user_data['人物卡'].items():
        pc_success = sum(pc_data.get('成功', {}).values())
        pc_fail = sum(pc_data.get('失败', {}).values())
        total_success += pc_success
        total_fail += pc_fail

        # 格式化成功列表
        success_str = ''
        success_list = []
        # 不论是否有成功数据，都获取成功列表
        if pc_data.get('成功'):
            for skill, count in pc_data['成功'].items():
                formatted = success_format.replace('{tSkillName}', skill).replace('{tCount}', str(count))
                success_list.append(formatted)
        # 使用分号分隔，最后一个换行
        if len(success_list) > 1:
            success_items = '; '.join(success_list)
        else:
            success_items = success_list[0] if success_list else dictStrCustom['strLoggerStatEmptyText']
        success_str = success_label.replace('{tSuccessItems}', success_items)

        # 格式化失败列表
        fail_str = ''
        fail_list = []
        # 不论是否有失败数据，都获取失败列表
        if pc_data.get('失败'):
            for skill, count in pc_data['失败'].items():
                formatted = fail_format.replace('{tSkillName}', skill).replace('{tCount}', str(count))
                fail_list.append(formatted)
        # 使用分号分隔，最后一个换行
        if len(fail_list) > 1:
            fail_items = '; '.join(fail_list)
        else:
            fail_items = fail_list[0] if fail_list else dictStrCustom['strLoggerStatEmptyText']
        fail_str = fail_label.replace('{tFailItems}', fail_items)

        # 存储人物卡数据
        pc_card_text = (
            pc_card_format
            .replace('{tPcName}', pc_name)
            .replace('{tSuccessList}', success_str)
            .replace('{tFailList}', fail_str)
        )
        pc_cards_data.append({
            'name': pc_name,
            'success_count': pc_success,
            'fail_count': pc_fail,
            'success_text': success_str,
            'fail_text': fail_str,
            'card_text': pc_card_text,
        })

    # 生成默认的格式化文本（向后兼容）
    lines = [card['card_text'] for card in pc_cards_data]
    return pc_card_separator.join(lines), total_success, total_fail, pc_cards_data


def format_all_stat_data(plugin_event, status_data, dictStrCustom):
    """格式化所有用户的统计数据"""
    if not status_data:
        return None, 0, 0, []

    # 获取自定义格式
    user_format = dictStrCustom['strLoggerStatUserFormat']
    user_separator = dictStrCustom['strLoggerStatUserSeparator']

    users_data = []
    total_success = 0
    total_fail = 0

    for user_hash, user_data in status_data.items():
        user_id = user_data['id']
        user_name = OlivaDiceCore.msgReplyModel.get_user_name(plugin_event, user_id)
        user_stat, user_success, user_fail, pc_cards_data = format_user_stat_data(
            user_data, plugin_event.bot_info.hash, dictStrCustom
        )

        if user_stat:
            user_text = user_format.replace('{tUserName}', user_name).replace('{tUserStatData}', user_stat)
            users_data.append({
                'name': user_name,
                'user_id': user_id,
                'success_count': user_success,
                'fail_count': user_fail,
                'stat_text': user_stat,
                'user_text': user_text,
                'pc_cards_data': pc_cards_data,
            })
            total_success += user_success
            total_fail += user_fail

    # 生成默认的格式化文本
    lines = [user['user_text'] for user in users_data]
    return user_separator.join(lines), total_success, total_fail, users_data
