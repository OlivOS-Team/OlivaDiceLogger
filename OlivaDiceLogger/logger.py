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
import json
import os
import traceback
import threading
import requests as req
from functools import wraps

gLoggerIOLockMap = {}

def init_logger(plugin_event, Proc):
    releaseDir('%s%s' % (OlivaDiceLogger.data.dataPath, OlivaDiceLogger.data.dataLogPath))
    OlivaDiceCore.crossHook.dictHookFunc['msgHook'] = add_logger_func(OlivaDiceCore.crossHook.dictHookFunc['msgHook'])
    try:
        import OlivOSOnebotV11
        OlivOSOnebotV11.eventRouter.txEvent.doRouter = add_logger_lazy_reply_func(
            OlivOSOnebotV11.eventRouter.txEvent.doRouter
        )
    except Exception as e:
        traceback.print_exc()

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


def add_logger_func(target_func):
    @wraps(target_func)
    def logger_func(*arg, **kwargs):
        res = target_func(*arg, **kwargs)
        loggerEntry(*arg, **kwargs)
        return res
    return logger_func


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
        if OlivaDiceCore.userConfig.getUserConfigByKey(
            userId = tmp_hagID,
            userType = 'group',
            platform = event.platform['platform'],
            userConfigKey = 'logEnable',
            botHash = event.bot_info.hash
        ):
            log_dict = {
                'time': int(time.mktime(time.localtime())),
                'type': funcType,
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
            tmp_logName = OlivaDiceCore.userConfig.getUserConfigByKey(
                userId = tmp_hagID,
                userType = 'group',
                platform = event.platform['platform'],
                userConfigKey = 'logNowName',
                botHash = event.bot_info.hash
            )
            if tmp_logName != None:
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

def releaseLogFile(logName):
    dataPath = OlivaDiceLogger.data.dataPath
    dataLogPath = OlivaDiceLogger.data.dataLogPath
    dataLogFile = '%s%s/%s.olivadicelog' % (dataPath, dataLogPath, logName)
    dataLogFile_1 = '%s%s/%s.trpglog' % (dataPath, dataLogPath, logName)
    tmp_dataLogFile = None
    with open(dataLogFile, 'r+', encoding = 'utf-8' , errors='ignore' ) as dataLogFile_f:
        tmp_dataLogFile = dataLogFile_f.read()
    if tmp_dataLogFile != None:
        tmp_dataLogFile = tmp_dataLogFile.strip('\n')
        tmp_dataLogFile_list = tmp_dataLogFile.split('\n')
        res_logFile_str = ''
        for tmp_dataLogFile_list_this in tmp_dataLogFile_list:
            tmp_dataLog_json = None
            try:
                tmp_dataLog_json = json.loads(tmp_dataLogFile_list_this)
            except:
                tmp_dataLog_json = None
            if tmp_dataLog_json != None:
                res_logFile_str += '%s(%s) %s\n%s\n' % (
                    str(tmp_dataLog_json['sender']['name']),
                    str(tmp_dataLog_json['sender']['id']),
                    str(time.strftime('%H:%M:%S', time.localtime(tmp_dataLog_json['time']))),
                    str(tmp_dataLog_json['message'])
                )
        with open(dataLogFile_1, 'w+', encoding = 'utf-8') as dataLogFile_f:
            dataLogFile_f.write(res_logFile_str)

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
