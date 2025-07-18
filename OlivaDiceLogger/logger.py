# -*- encoding: utf-8 -*-
'''
_______________________    _________________________________________
__  __ \__  /____  _/_ |  / /__    |__  __ \___  _/_  ____/__  ____/
_  / / /_  /  __  / __ | / /__  /| |_  / / /__  / _  /    __  __/   
/ /_/ /_  /____/ /  __ |/ / _  ___ |  /_/ /__/ /  / /___  _  /___   
\____/ /_____/___/  _____/  /_/  |_/_____/ /___/  \____/  /_____/   

@File      :   logger.py
@Author    :   lunzhiPenxil仑质
@Contact   :   lunzhipenxil@gmail.com
@License   :   AGPL
@Copyright :   (C) 2020-2021, OlivOS-Team
@Desc      :   None
'''

import OlivOS
import OlivaDiceCore
import OlivaDiceLogger

import time
import uuid
import re
import json
import os
import traceback
import threading
import requests as req
from functools import wraps

gLoggerIOLockMap = {}

# 兼容性处理只做一次
_compatibility_processed = False

def check_and_process_compatibility():
    global _compatibility_processed
    if not _compatibility_processed:
        migrate_database_config()
        dataPath = OlivaDiceLogger.data.dataPath
        dataLogPath = OlivaDiceLogger.data.dataLogPath
        log_dir = f'{dataPath}{dataLogPath}'
        
        if os.path.exists(log_dir):
            extensions = ['.olivadicelog', '.trpglog', '_temp.trpglog']
            for ext in extensions:
                for filename in os.listdir(log_dir):
                    if filename.endswith(ext) and '_' not in filename.replace('log_', '', 1):
                        base_name = filename[:-len(ext)]
                        clean_name = base_name.replace('log_', '', 1)
                        new_name = f'log_{clean_name}_default{ext}'
                        if not os.path.exists(f'{log_dir}/{new_name}'):
                            os.rename(
                                f'{log_dir}/{filename}',
                                f'{log_dir}/{new_name}'
                            )
        _compatibility_processed = True

def migrate_database_config():
    for userHash in OlivaDiceCore.userConfig.dictUserConfigData:
        for botHash in OlivaDiceCore.userConfig.dictUserConfigData[userHash]:
            config = OlivaDiceCore.userConfig.dictUserConfigData[userHash][botHash]
            if config.get('userType',"") != 'group':
                continue
            logNowName = config.get('configNote', {}).get('logNowName')
            logNameList = config.get('configNote', {}).get('logNameList', [])
            logNameTimeDict = config.get('configNote', {}).get('logNameTimeDict', {})
            if logNowName and not logNameList:
                # 从logNowName提取UUID（去掉"log_"前缀）
                log_uuid = logNowName.replace('log_', '', 1)
                # 设置default
                config['configNote']['logActiveName'] = 'default'
                config['configNote']['logNameList'] = ['default']
                config['configNote']['logNameDict'] = {'default': log_uuid}
                config['configNote']['logNameTimeDict']['default'] = {
                    'start_time': 0,
                    'end_time': 0,
                    'total_time': 0                    
                }
                config['configNote']['logNowName'] = None
                OlivaDiceCore.userConfig.listUserConfigDataUpdate.append(userHash)
            if logNameList:
                # 时间兼容
                for name in logNameList:
                    if name not in logNameTimeDict:
                        logNameTimeDict[name] = {
                            'start_time': 0,
                            'end_time': 0,
                            'total_time': 0
                        }
                config['configNote']['logNameTimeDict'] = logNameTimeDict
                OlivaDiceCore.userConfig.listUserConfigDataUpdate.append(userHash)

    for userHash in set(OlivaDiceCore.userConfig.listUserConfigDataUpdate):
        OlivaDiceCore.userConfig.writeUserConfigByUserHash(userHash)
    OlivaDiceCore.userConfig.listUserConfigDataUpdate = []

def init_logger(plugin_event, Proc):
    check_and_process_compatibility()
    releaseDir('%s%s' % (OlivaDiceLogger.data.dataPath, OlivaDiceLogger.data.dataLogPath))
    OlivaDiceCore.crossHook.dictHookFunc['msgHook'] = add_logger_func(OlivaDiceCore.crossHook.dictHookFunc['msgHook'])
    try:
        import OlivOSOnebotV11
        OlivOSOnebotV11.eventRouter.txEvent.doRouter = add_logger_lazy_reply_func(
            OlivOSOnebotV11.eventRouter.txEvent.doRouter
        )
    except Exception as e:
        traceback.print_exc()

# 时间函数
def format_duration(seconds):
    if seconds <= 0:
        return "0s"
    
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    res = ''
    
    if hours > 0:
        res += f"{hours}h"
    if minutes > 0:
        res += f"{minutes}m"
    if seconds > 0:
        res += f"{seconds}s"
        
    return res

def add_logger_lazy_reply_func(target_func):
    @wraps(target_func)
    def logger_func(self_arg):
        res = target_func(self_arg)
        try:
            loggerEntryLazyReply(self_arg)
        except Exception as e:
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
        if self_arg.funcType in [
            'send_msg'
        ]:
            if self_arg.params['message_type'] == 'private':
                pass
            elif self_arg.params['message_type'] == 'group':
                tmp_funcType = 'send_group'
        elif self_arg.funcType in [
            'send_private_msg'
        ]:
            pass
        elif self_arg.funcType in [
            'send_group_msg'
        ]:
            tmp_funcType = 'send_group'
        if tmp_funcType == 'send_group':
            tmp_botHash = self_arg.plugin_event.bot_info.hash
            tmp_sender = {
                'id': str(self_arg.plugin_event.bot_info.id),
                'name': 'Bot'
            }
            tmp_groupId = str(self_arg.params['group_id'])
            tmp_event = self_arg.plugin_event
            tmp_event_new = OlivOSOnebotV11.eventRouter.getEventRegDict(
                botHash = tmp_botHash,
                key = f'group_message/{tmp_groupId}'
            )
            if tmp_event_new is not None:
                tmp_event = tmp_event_new
            tmp_hostId = OlivOSOnebotV11.eventRouter.getHostIdDict(
                botHash = tmp_botHash,
                groupId = tmp_groupId
            )
            tmp_groupId = OlivOSOnebotV11.eventRouter.getMappingIdDict(tmp_botHash, tmp_groupId)
            tmp_hostId = OlivOSOnebotV11.eventRouter.getMappingIdDict(tmp_botHash, tmp_hostId)
            if tmp_hostId == 'None':
                tmp_hostId = None
            tmp_dectData = [tmp_hostId, tmp_groupId, None]
            tmp_message = OlivOSOnebotV11.eventRouter.paraRvMapper(
                self_arg.params['message']
            ).get('old_string')
        if tmp_event is not None \
        and tmp_funcType is not None \
        and tmp_sender is not None \
        and tmp_dectData is not None \
        and tmp_message is not None:
            loggerEntry(tmp_event, tmp_funcType, tmp_sender, tmp_dectData, tmp_message)
    except Exception as e:
        traceback.print_exc()

# 记录日志时撤回添加撤回标记
def handle_message_recall(event):
    try:
        message_id = event.data.message_id
        group_id = event.data.group_id
        botHash = event.bot_info.hash
        try:
            import OlivOSOnebotV11
            host_id = OlivOSOnebotV11.eventRouter.getHostIdDict(
                    botHash=botHash,
                    groupId=group_id
                )
        except Exception as e:
            host_id = None
        tmp_hagID = f"{host_id}|{group_id}" if host_id else str(group_id)
        
        if not OlivaDiceCore.userConfig.getUserConfigByKey(
            userId = tmp_hagID,
            userType = 'group',
            platform = event.platform['platform'],
            userConfigKey = 'logEnable',
            botHash = event.bot_info.hash
        ):
            return

        log_name = OlivaDiceCore.userConfig.getUserConfigByKey(
            userId = tmp_hagID,
            userType = 'group',
            platform = event.platform['platform'],
            userConfigKey = 'logActiveName',
            botHash = event.bot_info.hash
        )
        if not log_name:
            return

        log_name_dict = OlivaDiceCore.userConfig.getUserConfigByKey(
            userId = tmp_hagID,
            userType = 'group',
            platform = event.platform['platform'],
            userConfigKey = 'logNameDict',
            botHash = event.bot_info.hash
        ) or {}
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

    except Exception as e:
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
    except:
        return 0

def check_log_file_exists(log_name):
    dataPath = OlivaDiceLogger.data.dataPath
    dataLogPath = OlivaDiceLogger.data.dataLogPath
    olivadicelog_file = f'{dataPath}{dataLogPath}/{log_name}.olivadicelog'
    trpglog_file = f'{dataPath}{dataLogPath}/{log_name}.trpglog'
    return os.path.exists(olivadicelog_file) and os.path.exists(trpglog_file)

def loggerEntry(event, funcType, sender, dectData, message):
    [host_id, group_id, user_id] = dectData
    tmp_hagID = None
    if host_id != None and group_id != None:
        tmp_hagID = '%s|%s' % (str(host_id), str(group_id))
    elif group_id != None:
        tmp_hagID = str(group_id)
    tmp_name = 'N/A'
    tmp_id = -1
    if 'name' in sender:
        tmp_name = sender['name']
    if 'id' in sender:
        tmp_id = sender['id']
    if funcType in [
        'recv',
        'reply_private',
        'reply',
        'send_group'
    ]:
        active_log_name = OlivaDiceCore.userConfig.getUserConfigByKey(
            userId = tmp_hagID,
            userType = 'group',
            platform = event.platform['platform'],
            userConfigKey = 'logActiveName',
            botHash = event.bot_info.hash
        )
        if active_log_name and OlivaDiceCore.userConfig.getUserConfigByKey(
            userId = tmp_hagID,
            userType = 'group',
            platform = event.platform['platform'],
            userConfigKey = 'logEnable',
            botHash = event.bot_info.hash
        ):
            message_id = event.data.message_id
                
            log_dict = {
                'time': int(time.mktime(time.localtime())),
                'type': funcType,
                'message_id': message_id,
                'deleted': False,
                'dect': {
                    'host_id': host_id,
                    'group_id': group_id,
                    'user_id': user_id,
                },
                'sender': {
                    'id': tmp_id,
                    'name': tmp_name
                },
                'message': message
            }
            log_str = json.dumps(log_dict, ensure_ascii = False)
            log_name_dict = OlivaDiceCore.userConfig.getUserConfigByKey(
                userId = tmp_hagID,
                userType = 'group',
                platform = event.platform['platform'],
                userConfigKey = 'logNameDict',
                botHash = event.bot_info.hash
            ) or {}
            tmp_log_uuid = log_name_dict.get(active_log_name, str(uuid.uuid4()))
            tmp_logName = f'log_{tmp_log_uuid}_{active_log_name}'
            dataPath = OlivaDiceLogger.data.dataPath
            dataLogPath = OlivaDiceLogger.data.dataLogPath
            dataLogFile = '%s%s/%s.olivadicelog' % (dataPath, dataLogPath, tmp_logName)
            if dataLogFile not in gLoggerIOLockMap:
                gLoggerIOLockMap[dataLogFile] = threading.Lock()
            loggerIOLock = gLoggerIOLockMap[dataLogFile]
            loggerIOLock.acquire()
            with open(dataLogFile, 'a+', encoding = 'utf-8') as dataLogFile_f:
                dataLogFile_f.write('%s\n' % log_str)
            loggerIOLock.release()
    pass

def releaseLogFile(logName, total_duration = 0, temp = False):
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
        # 尝试从日志文件名解析日志名称和UUID
        log_name_parts = logName.split('_')
        if len(log_name_parts) >= 3:
            log_uuid = log_name_parts[1]
            log_name = "_".join(log_name_parts[2:])
            # 如果不是临时日志，在olivadicelog末尾添加总时长记录
            if not temp:
                total_record = {
                    'type': 'log_total_duration',
                    'total_time': total_duration
                }
                with open(dataLogFile, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(total_record, ensure_ascii=False) + '\n')
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
                except:
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
                        str(tmp_dataLog_json['message'])
                    )
            with open(dataLogFile_1, 'w+', encoding = 'utf-8') as dataLogFile_f:
                dataLogFile_f.write(res_logFile_str)
            return True
    except Exception as e:
        traceback.print_exc()
        return False
    return False

def uploadLogFile(logName):
    dataPath = OlivaDiceLogger.data.dataPath
    dataLogPath = OlivaDiceLogger.data.dataLogPath
    dataLogFile = '%s%s/%s.olivadicelog' % (dataPath, dataLogPath, logName)
    dataLogFile_1 = '%s%s/%s.trpglog' % (dataPath, dataLogPath, logName)
    tmp_dataLogFile = None
    with open(dataLogFile_1, 'rb') as dataLogFile_f:
        tmp_dataLogFile = dataLogFile_f.read()
        url = OlivaDiceLogger.data.dataLogUpload
        files = {
            'file': tmp_dataLogFile
        }
        data = {
            'name': logName
        }
        response = req.request("POST", url, files = files, data = data, proxies = OlivaDiceCore.webTool.get_system_proxy())

def releaseDir(dir_path):
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
