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
        import glob
        for ext in ['.olivadicelog', '.trpglog', '_temp.trpglog']:
            pattern = os.path.join(log_dir, f'*{ext}')
            for filepath in glob.glob(pattern):
                filename = os.path.basename(filepath)
                if '_' not in filename.replace('log_', '', 1):
                    base_name = filename[:-len(ext)]
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
    releaseDir('%s%s' % (OlivaDiceLogger.data.dataPath, OlivaDiceLogger.data.dataLogPath))
    check_and_process_compatibility()
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
                            last_message_id = log_entry['message_id']
                    except:
                        continue
        except:
            pass
    return last_message_id

def write_status_to_file(log_uuid, status_data):
    """将统计数据写入status_uuid.json文件"""
    dataPath = OlivaDiceLogger.data.dataPath
    dataLogPath = OlivaDiceLogger.data.dataLogPath
    status_file = f'{dataPath}{dataLogPath}/status_{log_uuid}.json'
    try:
        with open(status_file, 'w', encoding='utf-8') as f:
            json.dump(status_data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
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
    except Exception as e:
        traceback.print_exc()
        return None

def init_log_status(log_uuid, plugin_event, tmp_hagID):
    """初始化日志状态数据"""
    # 获取当前群组配置中的logStatus
    log_status = OlivaDiceCore.userConfig.getUserConfigByKey(
        userId=tmp_hagID,
        userType='group',
        platform=plugin_event.platform['platform'],
        userConfigKey='logStatus',
        botHash=plugin_event.bot_info.hash
    )
    if log_status is None:
        log_status = {}
    
    # 如果该UUID不存在，则创建
    if log_uuid not in log_status:
        log_status[log_uuid] = {}
        OlivaDiceCore.userConfig.setUserConfigByKey(
            userId=tmp_hagID,
            userType='group',
            platform=plugin_event.platform['platform'],
            userConfigKey='logStatus',
            userConfigValue=log_status,
            botHash=plugin_event.bot_info.hash
        )

def persist_log_status(log_uuid, plugin_event, tmp_hagID):
    """持久化日志状态数据到status_uuid.json"""
    log_status = OlivaDiceCore.userConfig.getUserConfigByKey(
        userId=tmp_hagID,
        userType='group',
        platform=plugin_event.platform['platform'],
        userConfigKey='logStatus',
        botHash=plugin_event.bot_info.hash
    )
    if log_status and log_uuid in log_status:
        write_status_to_file(log_uuid, log_status[log_uuid])

def clear_log_status(log_uuid, plugin_event, tmp_hagID):
    """清除内存中的日志状态数据"""
    log_status = OlivaDiceCore.userConfig.getUserConfigByKey(
        userId=tmp_hagID,
        userType='group',
        platform=plugin_event.platform['platform'],
        userConfigKey='logStatus',
        botHash=plugin_event.bot_info.hash
    )
    if log_status and log_uuid in log_status:
        del log_status[log_uuid]
        OlivaDiceCore.userConfig.setUserConfigByKey(
            userId=tmp_hagID,
            userType='group',
            platform=plugin_event.platform['platform'],
            userConfigKey='logStatus',
            userConfigValue=log_status,
            botHash=plugin_event.bot_info.hash
        )

def get_log_status(log_uuid, plugin_event, tmp_hagID):
    """获取日志状态数据"""
    log_status = OlivaDiceCore.userConfig.getUserConfigByKey(
        userId=tmp_hagID,
        userType='group',
        platform=plugin_event.platform['platform'],
        userConfigKey='logStatus',
        botHash=plugin_event.bot_info.hash
    )
    if log_status and log_uuid in log_status:
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
        pc_card_text = pc_card_format.replace('{tPcName}', pc_name).replace('{tSuccessList}', success_str).replace('{tFailList}', fail_str)
        pc_cards_data.append({
            'name': pc_name,
            'success_count': pc_success,
            'fail_count': pc_fail,
            'success_text': success_str,
            'fail_text': fail_str,
            'card_text': pc_card_text
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
        user_stat, user_success, user_fail, pc_cards_data = format_user_stat_data(user_data, plugin_event.bot_info.hash, dictStrCustom)
        
        if user_stat:
            user_text = user_format.replace('{tUserName}', user_name).replace('{tUserStatData}', user_stat)
            users_data.append({
                'name': user_name,
                'user_id': user_id,
                'success_count': user_success,
                'fail_count': user_fail,
                'stat_text': user_stat,
                'user_text': user_text,
                'pc_cards_data': pc_cards_data
            })
            total_success += user_success
            total_fail += user_fail
    
    # 生成默认的格式化文本
    lines = [user['user_text'] for user in users_data]
    return user_separator.join(lines), total_success, total_fail, users_data