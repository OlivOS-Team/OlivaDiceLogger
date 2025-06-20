# -*- encoding: utf-8 -*-
'''
_______________________    _________________________________________
__  __ \__  /____  _/_ |  / /__    |__  __ \___  _/_  ____/__  ____/
_  / / /_  /  __  / __ | / /__  /| |_  / / /__  / _  /    __  __/   
/ /_/ /_  /____/ /  __ |/ / _  ___ |  /_/ /__/ /  / /___  _  /___   
\____/ /_____/___/  _____/  /_/  |_/_____/ /___/  \____/  /_____/   

@File      :   msgReply.py
@Author    :   lunzhiPenxil仑质
@Contact   :   lunzhipenxil@gmail.com
@License   :   AGPL
@Copyright :   (C) 2020-2021, OlivOS-Team
@Desc      :   None
'''

import OlivOS
import OlivaDiceLogger
import OlivaDiceCore
import urllib.parse

import hashlib
import time
import os
from datetime import datetime, timezone, timedelta
import uuid
import json
import traceback

def unity_init(plugin_event, Proc):
    pass

def data_init(plugin_event, Proc):
    OlivaDiceLogger.msgCustomManager.initMsgCustom(Proc.Proc_data['bot_info_dict'])
    OlivaDiceLogger.userConfig.initUserConfigNoteDefault(Proc.Proc_data['bot_info_dict'])

def unity_reply(plugin_event, Proc):
    OlivaDiceCore.userConfig.setMsgCount()
    dictTValue = OlivaDiceCore.msgCustom.dictTValue.copy()
    dictTValue['tName'] = plugin_event.data.sender['name']
    dictStrCustom = OlivaDiceCore.msgCustom.dictStrCustomDict[plugin_event.bot_info.hash]
    dictGValue = OlivaDiceCore.msgCustom.dictGValue
    dictTValue.update(dictGValue)
    dictTValue = OlivaDiceCore.msgCustomManager.dictTValueInit(plugin_event, dictTValue)

    replyMsg = OlivaDiceCore.msgReply.replyMsg
    replyMsgLazyHelpByEvent = OlivaDiceCore.msgReply.replyMsgLazyHelpByEvent
    isMatchWordStart = OlivaDiceCore.msgReply.isMatchWordStart
    getMatchWordStartRight = OlivaDiceCore.msgReply.getMatchWordStartRight
    skipSpaceStart = OlivaDiceCore.msgReply.skipSpaceStart
    skipToRight = OlivaDiceCore.msgReply.skipToRight
    msgIsCommand = OlivaDiceCore.msgReply.msgIsCommand

    tmp_at_str = OlivOS.messageAPI.PARA.at(plugin_event.base_info['self_id']).CQ()
    tmp_at_str_sub = None
    if 'sub_self_id' in plugin_event.data.extend:
        if plugin_event.data.extend['sub_self_id'] != None:
            tmp_at_str_sub = OlivOS.messageAPI.PARA.at(plugin_event.data.extend['sub_self_id']).CQ()
    tmp_command_str_1 = '.'
    tmp_command_str_2 = '。'
    tmp_command_str_3 = '/'
    tmp_reast_str = plugin_event.data.message
    flag_force_reply = False
    flag_is_command = False
    flag_is_from_host = False
    flag_is_from_group = False
    flag_is_from_group_admin = False
    flag_is_from_group_have_admin = False
    flag_is_from_master = False
    if isMatchWordStart(tmp_reast_str, '[CQ:reply,id='):
        tmp_reast_str = skipToRight(tmp_reast_str, ']')
        tmp_reast_str = tmp_reast_str[1:]
        if isMatchWordStart(tmp_reast_str, tmp_at_str):
            tmp_reast_str = getMatchWordStartRight(tmp_reast_str, tmp_at_str)
            tmp_reast_str = skipSpaceStart(tmp_reast_str)
            flag_force_reply = True
    if isMatchWordStart(tmp_reast_str, tmp_at_str):
        tmp_reast_str = getMatchWordStartRight(tmp_reast_str, tmp_at_str)
        tmp_reast_str = skipSpaceStart(tmp_reast_str)
        flag_force_reply = True
    if tmp_at_str_sub != None:
        if isMatchWordStart(tmp_reast_str, tmp_at_str_sub):
            tmp_reast_str = getMatchWordStartRight(tmp_reast_str, tmp_at_str_sub)
            tmp_reast_str = skipSpaceStart(tmp_reast_str)
            flag_force_reply = True
    [tmp_reast_str, flag_is_command] = msgIsCommand(
        tmp_reast_str,
        OlivaDiceCore.crossHook.dictHookList['prefix']
    )
    if flag_is_command:
        tmp_hagID = None
        if plugin_event.plugin_info['func_type'] == 'group_message':
            if plugin_event.data.host_id != None:
                flag_is_from_host = True
            flag_is_from_group = True
        elif plugin_event.plugin_info['func_type'] == 'private_message':
            flag_is_from_group = False
        if flag_is_from_host and flag_is_from_group:
            tmp_hagID = '%s|%s' % (str(plugin_event.data.host_id), str(plugin_event.data.group_id))
        elif flag_is_from_group:
            tmp_hagID = str(plugin_event.data.group_id)
        if flag_is_from_group:
            if 'role' in plugin_event.data.sender:
                flag_is_from_group_have_admin = True
                if plugin_event.data.sender['role'] in ['owner', 'admin']:
                    flag_is_from_group_admin = True
                elif plugin_event.data.sender['role'] in ['sub_admin']:
                    flag_is_from_group_admin = True
                    flag_is_from_group_sub_admin = True
        flag_hostEnable = True
        if flag_is_from_host:
            flag_hostEnable = OlivaDiceCore.userConfig.getUserConfigByKey(
                userId = plugin_event.data.host_id,
                userType = 'host',
                platform = plugin_event.platform['platform'],
                userConfigKey = 'hostEnable',
                botHash = plugin_event.bot_info.hash
            )
        flag_hostLocalEnable = True
        if flag_is_from_host:
            flag_hostLocalEnable = OlivaDiceCore.userConfig.getUserConfigByKey(
                userId = plugin_event.data.host_id,
                userType = 'host',
                platform = plugin_event.platform['platform'],
                userConfigKey = 'hostLocalEnable',
                botHash = plugin_event.bot_info.hash
            )
        flag_groupEnable = True
        if flag_is_from_group:
            if flag_is_from_host:
                if flag_hostEnable:
                    flag_groupEnable = OlivaDiceCore.userConfig.getUserConfigByKey(
                        userId = tmp_hagID,
                        userType = 'group',
                        platform = plugin_event.platform['platform'],
                        userConfigKey = 'groupEnable',
                        botHash = plugin_event.bot_info.hash
                    )
                else:
                    flag_groupEnable = OlivaDiceCore.userConfig.getUserConfigByKey(
                        userId = tmp_hagID,
                        userType = 'group',
                        platform = plugin_event.platform['platform'],
                        userConfigKey = 'groupWithHostEnable',
                        botHash = plugin_event.bot_info.hash
                    )
            else:
                flag_groupEnable = OlivaDiceCore.userConfig.getUserConfigByKey(
                    userId = tmp_hagID,
                    userType = 'group',
                    platform = plugin_event.platform['platform'],
                    userConfigKey = 'groupEnable',
                    botHash = plugin_event.bot_info.hash
                )
        #此频道关闭时中断处理
        if not flag_hostLocalEnable and not flag_force_reply:
            return
        #此群关闭时中断处理
        if not flag_groupEnable and not flag_force_reply:
            return
        if isMatchWordStart(tmp_reast_str, 'log', isCommand = True) and flag_is_from_group:
            tmp_reast_str = getMatchWordStartRight(tmp_reast_str, 'log')
            tmp_reast_str = skipSpaceStart(tmp_reast_str)
            tmp_reply_str = None

            if isMatchWordStart(tmp_reast_str, 'on'):
                tmp_reast_str = getMatchWordStartRight(tmp_reast_str, 'on')
                tmp_reast_str = skipSpaceStart(tmp_reast_str)

                is_logging = OlivaDiceCore.userConfig.getUserConfigByKey(
                    userId = tmp_hagID,
                    userType = 'group',
                    platform = plugin_event.platform['platform'],
                    userConfigKey = 'logEnable',
                    botHash = plugin_event.bot_info.hash
                )

                if is_logging:
                    active_log_name = OlivaDiceCore.userConfig.getUserConfigByKey(
                        userId = tmp_hagID,
                        userType = 'group',
                        platform = plugin_event.platform['platform'],
                        userConfigKey = 'logActiveName',
                        botHash = plugin_event.bot_info.hash
                    )
                    dictTValue['tLogName'] = active_log_name
                    tmp_reply_str = OlivaDiceCore.msgCustomManager.formatReplySTR(dictStrCustom['strLoggerLogAlreadyOn'], dictTValue)
                    replyMsg(plugin_event, tmp_reply_str)
                    return

                log_name = OlivaDiceCore.userConfig.getUserConfigByKey(
                    userId = tmp_hagID,
                    userType = 'group',
                    platform = plugin_event.platform['platform'],
                    userConfigKey = 'logActiveName',
                    botHash = plugin_event.bot_info.hash
                ) or 'default'

                if tmp_reast_str.strip() != '':
                    log_name = tmp_reast_str.strip()
                    if not OlivaDiceLogger.logger.is_valid_log_name(log_name):
                        dictTValue['tLogName'] = log_name
                        tmp_reply_str = OlivaDiceCore.msgCustomManager.formatReplySTR(dictStrCustom['strLoggerLogInvalidName'], dictTValue)
                        replyMsg(plugin_event, tmp_reply_str)
                        return

                log_name_list = OlivaDiceCore.userConfig.getUserConfigByKey(
                    userId = tmp_hagID,
                    userType = 'group',
                    platform = plugin_event.platform['platform'],
                    userConfigKey = 'logNameList',
                    botHash = plugin_event.bot_info.hash
                ) or []

                log_name_dict = OlivaDiceCore.userConfig.getUserConfigByKey(
                    userId = tmp_hagID,
                    userType = 'group',
                    platform = plugin_event.platform['platform'],
                    userConfigKey = 'logNameDict',
                    botHash = plugin_event.bot_info.hash
                ) or {}
                        
                if log_name not in log_name_list:
                    log_name_list.append(log_name)
                    log_name_dict[log_name] = str(uuid.uuid4())
                    OlivaDiceCore.userConfig.setUserConfigByKey(
                        userConfigKey = 'logNameList',
                        userConfigValue = log_name_list,
                        botHash = plugin_event.bot_info.hash,
                        userId = tmp_hagID,
                        userType = 'group',
                        platform = plugin_event.platform['platform']
                    )
                    OlivaDiceCore.userConfig.setUserConfigByKey(
                        userConfigKey = 'logNameDict',
                        userConfigValue = log_name_dict,
                        botHash = plugin_event.bot_info.hash,
                        userId = tmp_hagID,
                        userType = 'group',
                        platform = plugin_event.platform['platform']
                    )
                    dictTValue['tLogName'] = log_name
                    tmp_reply_str = OlivaDiceCore.msgCustomManager.formatReplySTR(dictStrCustom['strLoggerLogOn'], dictTValue)
                else:
                    tmp_log_uuid = log_name_dict.get(log_name, str(uuid.uuid4()))
                    tmp_logName = f'log_{tmp_log_uuid}_{log_name}'
                    log_lines = OlivaDiceLogger.logger.get_log_lines(tmp_logName)
                    dictTValue['tLogLines'] = str(log_lines)
                    dictTValue['tLogName'] = log_name
                    tmp_reply_str = OlivaDiceCore.msgCustomManager.formatReplySTR(dictStrCustom['strLoggerLogContinue'], dictTValue)

                OlivaDiceCore.userConfig.setUserConfigByKey(
                    userConfigKey = 'logActiveName',
                    userConfigValue = log_name,
                    botHash = plugin_event.bot_info.hash,
                    userId = tmp_hagID,
                    userType = 'group',
                    platform = plugin_event.platform['platform']
                )

                OlivaDiceCore.userConfig.setUserConfigByKey(
                    userConfigKey = 'logEnable',
                    userConfigValue = True,
                    botHash = plugin_event.bot_info.hash,
                    userId = tmp_hagID,
                    userType = 'group',
                    platform = plugin_event.platform['platform']
                )

                OlivaDiceCore.userConfig.writeUserConfigByUserHash(
                    userHash = OlivaDiceCore.userConfig.getUserHash(
                        userId = tmp_hagID,
                        userType = 'group',
                        platform = plugin_event.platform['platform']
                    )
                )
                replyMsg(plugin_event, tmp_reply_str)
                return

            elif isMatchWordStart(tmp_reast_str, 'off'):
                tmp_reast_str = getMatchWordStartRight(tmp_reast_str, 'off')
                tmp_reast_str = skipSpaceStart(tmp_reast_str)

                is_logging = OlivaDiceCore.userConfig.getUserConfigByKey(
                    userId=tmp_hagID,
                    userType='group',
                    platform=plugin_event.platform['platform'],
                    userConfigKey='logEnable',
                    botHash=plugin_event.bot_info.hash
                )

                if not is_logging:
                    tmp_reply_str = OlivaDiceCore.msgCustomManager.formatReplySTR(
                        dictStrCustom['strLoggerLogAlreadyOff'], 
                        dictTValue
                    )
                    replyMsg(plugin_event, tmp_reply_str)
                    return

                log_name = OlivaDiceCore.userConfig.getUserConfigByKey(
                    userId=tmp_hagID,
                    userType='group',
                    platform=plugin_event.platform['platform'],
                    userConfigKey='logActiveName',
                    botHash=plugin_event.bot_info.hash
                )

                if tmp_reast_str.strip() != '':
                    log_name = tmp_reast_str.strip()

                log_name_dict = OlivaDiceCore.userConfig.getUserConfigByKey(
                    userId=tmp_hagID,
                    userType='group',
                    platform=plugin_event.platform['platform'],
                    userConfigKey='logNameDict',
                    botHash=plugin_event.bot_info.hash
                ) or {}
                tmp_log_uuid = log_name_dict.get(log_name, str(uuid.uuid4()))
                tmp_logName = f'log_{tmp_log_uuid}_{log_name}'
                log_lines = OlivaDiceLogger.logger.get_log_lines(tmp_logName)

                OlivaDiceCore.userConfig.setUserConfigByKey(
                    userConfigKey='logEnable',
                    userConfigValue=False,
                    botHash=plugin_event.bot_info.hash,
                    userId=tmp_hagID,
                    userType='group',
                    platform=plugin_event.platform['platform']
                )

                dictTValue['tLogLines'] = str(log_lines)
                dictTValue['tLogName'] = log_name
                tmp_reply_str = OlivaDiceCore.msgCustomManager.formatReplySTR(
                    dictStrCustom['strLoggerLogOff'], 
                    dictTValue
                )

                OlivaDiceCore.userConfig.writeUserConfigByUserHash(
                    userHash=OlivaDiceCore.userConfig.getUserHash(
                        userId=tmp_hagID,
                        userType='group',
                        platform=plugin_event.platform['platform']
                    )
                )
                replyMsg(plugin_event, tmp_reply_str)
                return

            elif isMatchWordStart(tmp_reast_str, 'end'):
                tmp_reast_str = getMatchWordStartRight(tmp_reast_str, 'end')
                tmp_reast_str = skipSpaceStart(tmp_reast_str)

                log_name = OlivaDiceCore.userConfig.getUserConfigByKey(
                    userId = tmp_hagID,
                    userType = 'group',
                    platform = plugin_event.platform['platform'],
                    userConfigKey = 'logActiveName',
                    botHash = plugin_event.bot_info.hash
                )

                if tmp_reast_str.strip() != '':
                    log_name = tmp_reast_str.strip()

                if log_name is None:
                    tmp_reply_str = OlivaDiceCore.msgCustomManager.formatReplySTR(dictStrCustom['strLoggerLogAlreadyEnd'], dictTValue)
                    replyMsg(plugin_event, tmp_reply_str)
                    return

                log_name_list = OlivaDiceCore.userConfig.getUserConfigByKey(
                    userId = tmp_hagID,
                    userType = 'group',
                    platform = plugin_event.platform['platform'],
                    userConfigKey = 'logNameList',
                    botHash = plugin_event.bot_info.hash
                ) or []

                if log_name not in log_name_list:
                    dictTValue['tLogName'] = log_name
                    tmp_reply_str = OlivaDiceCore.msgCustomManager.formatReplySTR(dictStrCustom['strLoggerLogNotFound'], dictTValue)
                    replyMsg(plugin_event, tmp_reply_str)
                    return

                log_name_dict = OlivaDiceCore.userConfig.getUserConfigByKey(
                    userId = tmp_hagID,
                    userType = 'group',
                    platform = plugin_event.platform['platform'],
                    userConfigKey = 'logNameDict',
                    botHash = plugin_event.bot_info.hash
                ) or {}

                tmp_log_uuid = log_name_dict.get(log_name, str(uuid.uuid4()))
                tmp_logName = f'log_{tmp_log_uuid}_{log_name}'
                log_lines = OlivaDiceLogger.logger.get_log_lines(tmp_logName)
                dictTValue['tLogLines'] = str(log_lines)

                active_log_name = OlivaDiceCore.userConfig.getUserConfigByKey(
                    userId = tmp_hagID,
                    userType = 'group',
                    platform = plugin_event.platform['platform'],
                    userConfigKey = 'logActiveName',
                    botHash = plugin_event.bot_info.hash
                )

                if active_log_name == log_name:
                    OlivaDiceCore.userConfig.setUserConfigByKey(
                        userConfigKey = 'logEnable',
                        userConfigValue = False,
                        botHash = plugin_event.bot_info.hash,
                        userId = tmp_hagID,
                        userType = 'group',
                        platform = plugin_event.platform['platform']
                    )
                    OlivaDiceCore.userConfig.setUserConfigByKey(
                        userConfigKey = 'logActiveName',
                        userConfigValue = None,
                        botHash = plugin_event.bot_info.hash,
                        userId = tmp_hagID,
                        userType = 'group',
                        platform = plugin_event.platform['platform']
                    )

                dictTValue['tLogName'] = log_name
                tmp_reply_str = OlivaDiceCore.msgCustomManager.formatReplySTR(dictStrCustom['strLoggerLogEnd'], dictTValue)
                replyMsg(plugin_event, tmp_reply_str)

                if OlivaDiceLogger.logger.releaseLogFile(tmp_logName):
                    dictTValue['tLogName'] = log_name
                    dictTValue['tLogUUID'] = tmp_log_uuid
                    tmp_reply_str = OlivaDiceCore.msgCustomManager.formatReplySTR(dictStrCustom['strLoggerLogSave'], dictTValue)
                    replyMsg(plugin_event, tmp_reply_str)
                    OlivaDiceLogger.logger.uploadLogFile(tmp_logName)
                    encoded_logName = urllib.parse.quote(tmp_logName)
                    dictTValue['tLogUrl'] = '%s%s' % (
                        OlivaDiceLogger.data.dataLogPainterUrl,
                        encoded_logName
                    )
                    tmp_reply_str = OlivaDiceCore.msgCustomManager.formatReplySTR(dictStrCustom['strLoggerLogUrl'], dictTValue)
                    replyMsg(plugin_event, tmp_reply_str)

                    if log_name in log_name_list:
                        log_name_list.remove(log_name)
                        OlivaDiceCore.userConfig.setUserConfigByKey(
                            userConfigKey = 'logNameList',
                            userConfigValue = log_name_list,
                            botHash = plugin_event.bot_info.hash,
                            userId = tmp_hagID,
                            userType = 'group',
                            platform = plugin_event.platform['platform']
                        )
                        
                        if log_name in log_name_dict:
                            del log_name_dict[log_name]
                            OlivaDiceCore.userConfig.setUserConfigByKey(
                                userConfigKey = 'logNameDict',
                                userConfigValue = log_name_dict,
                                botHash = plugin_event.bot_info.hash,
                                userId = tmp_hagID,
                                userType = 'group',
                                platform = plugin_event.platform['platform']
                            )

                    try:
                        if plugin_event.platform['platform'] == 'kaiheila'\
                        and plugin_event.indeAPI.hasAPI('create_message'):
                            plugin_event.indeAPI.create_message(
                                chat_type = 'group',
                                chat_id = plugin_event.data.group_id,
                                content_type = 10,
                                content = json.dumps(
                                    [
                                        {
                                            "type": "card",
                                            "theme": "primary",
                                            "color": "#009FE9",
                                            "size": "lg",
                                            "modules": [
                                                {
                                                    "type": "header",
                                                    "text": {
                                                        "type": "plain-text",
                                                        "content": "您的日志将在如下时间后过期，请尽快点击按钮提取"
                                                    }
                                                },
                                                {
                                                    "type": "countdown",
                                                    "mode": "day",
                                                    "endTime": int((int(datetime.now(timezone.utc).timestamp()) + 7 * 24 * 60 * 60) * 1000)
                                                },
                                                {
                                                    "type": "action-group",
                                                    "elements": [
                                                        {
                                                            "type": "button",
                                                            "theme": "info",
                                                            "value": str(dictTValue['tLogUrl']),
                                                            "click": "link",
                                                            "text": {
                                                                "type": "plain-text",
                                                                "content": "点我提取日志"
                                                            }
                                                        }
                                                    ]
                                                },
                                                {
                                                    "type": "context",
                                                    "elements": [
                                                        {
                                                          "type": "plain-text",
                                                          "content": "OlivaDice - 青果核心掷骰机器人"
                                                        }
                                                    ]
                                                }
                                            ]
                                        }
                                    ],
                                    ensure_ascii=False
                                )
                            )
                    except Exception as e:
                        traceback.print_exc()

                OlivaDiceCore.userConfig.writeUserConfigByUserHash(
                    userHash = OlivaDiceCore.userConfig.getUserHash(
                        userId = tmp_hagID,
                        userType = 'group',
                        platform = plugin_event.platform['platform']
                    )
                )
                return

            elif isMatchWordStart(tmp_reast_str, 'list'):
                log_name_list = OlivaDiceCore.userConfig.getUserConfigByKey(
                    userId = tmp_hagID,
                    userType = 'group',
                    platform = plugin_event.platform['platform'],
                    userConfigKey = 'logNameList',
                    botHash = plugin_event.bot_info.hash
                ) or []

                # 过滤掉已结束的日志
                active_logs = []
                for name in log_name_list:
                    tmp_log_uuid = OlivaDiceCore.userConfig.getUserConfigByKey(
                        userId = tmp_hagID,
                        userType = 'group',
                        platform = plugin_event.platform['platform'],
                        userConfigKey = 'logNameDict',
                        botHash = plugin_event.bot_info.hash
                    ).get(name, str(uuid.uuid4()))
                    tmp_logName = f'log_{tmp_log_uuid}_{name}'
                    if not OlivaDiceLogger.logger.check_log_file_exists(tmp_logName):
                        active_logs.append(name)

                if len(active_logs) == 0:
                    tmp_reply_str = OlivaDiceCore.msgCustomManager.formatReplySTR(dictStrCustom['strLoggerLogListEmpty'], dictTValue)
                else:
                    active_log_name = OlivaDiceCore.userConfig.getUserConfigByKey(
                        userId = tmp_hagID,
                        userType = 'group',
                        platform = plugin_event.platform['platform'],
                        userConfigKey = 'logActiveName',
                        botHash = plugin_event.bot_info.hash
                    )

                    log_list_str = []
                    for name in active_logs:
                        if name == active_log_name:
                            log_list_str.append(f"- {name} (当前记录)")
                        else:
                            log_list_str.append(f"- {name}")

                    dictTValue['tLogList'] = '\n'.join(log_list_str)
                    tmp_reply_str = OlivaDiceCore.msgCustomManager.formatReplySTR(dictStrCustom['strLoggerLogList'], dictTValue)

                replyMsg(plugin_event, tmp_reply_str)
                return
            
            elif isMatchWordStart(tmp_reast_str, 'stop'):
                tmp_reast_str = getMatchWordStartRight(tmp_reast_str, 'stop')
                tmp_reast_str = skipSpaceStart(tmp_reast_str)
                
                log_name = OlivaDiceCore.userConfig.getUserConfigByKey(
                    userId = tmp_hagID,
                    userType = 'group',
                    platform = plugin_event.platform['platform'],
                    userConfigKey = 'logActiveName',
                    botHash = plugin_event.bot_info.hash
                )
            
                if tmp_reast_str.strip() != '':
                    log_name = tmp_reast_str.strip()
            
                if log_name is None:
                    tmp_reply_str = OlivaDiceCore.msgCustomManager.formatReplySTR(dictStrCustom['strLoggerLogAlreadyEnd'], dictTValue)
                    replyMsg(plugin_event, tmp_reply_str)
                    return
            
                log_name_list = OlivaDiceCore.userConfig.getUserConfigByKey(
                    userId = tmp_hagID,
                    userType = 'group',
                    platform = plugin_event.platform['platform'],
                    userConfigKey = 'logNameList',
                    botHash = plugin_event.bot_info.hash
                ) or []
            
                if log_name not in log_name_list:
                    dictTValue['tLogName'] = log_name
                    tmp_reply_str = OlivaDiceCore.msgCustomManager.formatReplySTR(dictStrCustom['strLoggerLogNotFound'], dictTValue)
                    replyMsg(plugin_event, tmp_reply_str)
                    return
            
                log_name_dict = OlivaDiceCore.userConfig.getUserConfigByKey(
                    userId = tmp_hagID,
                    userType = 'group',
                    platform = plugin_event.platform['platform'],
                    userConfigKey = 'logNameDict',
                    botHash = plugin_event.bot_info.hash
                ) or {}
            
                tmp_log_uuid = log_name_dict.get(log_name, str(uuid.uuid4()))
                tmp_logName = f'log_{tmp_log_uuid}_{log_name}'

                # 检查日志文件是否存在，若不存在则创建空文件
                dataPath = OlivaDiceLogger.data.dataPath
                dataLogPath = OlivaDiceLogger.data.dataLogPath
                dataLogFile = f'{dataPath}{dataLogPath}/{tmp_logName}.olivadicelog'
                log_error = False

                if os.path.exists(dataLogFile):
                    try:
                        with open(dataLogFile, 'r', encoding='utf-8') as f:
                            for line in f:
                                line = line.strip()
                                if line:
                                    try:
                                        json.loads(line)
                                    except json.JSONDecodeError:
                                        log_error = True
                                        break
                                    
                        # 如果检测到错误，重命名原文件并创建新文件
                        if log_error:
                            error_log_file = f'{dataPath}{dataLogPath}/error_{tmp_logName}.txt'
                            try:
                                os.rename(dataLogFile, error_log_file)
                                with open(dataLogFile, 'w', encoding='utf-8') as f:
                                    f.write('{}')
                            except Exception as e:
                                traceback.print_exc()
                                log_error = True

                    except Exception as e:
                        traceback.print_exc()
                        log_error = True
                else:
                    try:
                        with open(dataLogFile, 'w', encoding='utf-8') as f:
                            f.write('{}')
                    except Exception as e:
                        traceback.print_exc()
                        log_error = True

                log_lines = OlivaDiceLogger.logger.get_log_lines(tmp_logName)
                dictTValue['tLogLines'] = str(log_lines)
                dictTValue['tLogUUID'] = tmp_log_uuid
            
                active_log_name = OlivaDiceCore.userConfig.getUserConfigByKey(
                    userId = tmp_hagID,
                    userType = 'group',
                    platform = plugin_event.platform['platform'],
                    userConfigKey = 'logActiveName',
                    botHash = plugin_event.bot_info.hash
                )
            
                if active_log_name == log_name:
                    OlivaDiceCore.userConfig.setUserConfigByKey(
                        userConfigKey = 'logEnable',
                        userConfigValue = False,
                        botHash = plugin_event.bot_info.hash,
                        userId = tmp_hagID,
                        userType = 'group',
                        platform = plugin_event.platform['platform']
                    )
                    OlivaDiceCore.userConfig.setUserConfigByKey(
                        userConfigKey = 'logActiveName',
                        userConfigValue = None,
                        botHash = plugin_event.bot_info.hash,
                        userId = tmp_hagID,
                        userType = 'group',
                        platform = plugin_event.platform['platform']
                    )
            
                # 强制生成.trpglog文件
                success = OlivaDiceLogger.logger.releaseLogFile(tmp_logName)
                if not success:
                    # 如果生成失败，创建一个文件显示日志已损坏
                    dataLogFile_1 = f'{dataPath}{dataLogPath}/{tmp_logName}.trpglog'
                    with open(dataLogFile_1, 'w', encoding='utf-8') as f:
                        f.write('日志已损坏')
            
                dictTValue['tLogName'] = log_name
                if not log_error:
                    tmp_reply_str = OlivaDiceCore.msgCustomManager.formatReplySTR(dictStrCustom['strLoggerLogStop'], dictTValue)
                else:
                    tmp_reply_str = OlivaDiceCore.msgCustomManager.formatReplySTR(dictStrCustom['strLoggerLogStopError'], dictTValue)

                replyMsg(plugin_event, tmp_reply_str)
            
                if log_name in log_name_list:
                    log_name_list.remove(log_name)
                    OlivaDiceCore.userConfig.setUserConfigByKey(
                        userConfigKey = 'logNameList',
                        userConfigValue = log_name_list,
                        botHash = plugin_event.bot_info.hash,
                        userId = tmp_hagID,
                        userType = 'group',
                        platform = plugin_event.platform['platform']
                    )
                    
                    if log_name in log_name_dict:
                        del log_name_dict[log_name]
                        OlivaDiceCore.userConfig.setUserConfigByKey(
                            userConfigKey = 'logNameDict',
                            userConfigValue = log_name_dict,
                            botHash = plugin_event.bot_info.hash,
                            userId = tmp_hagID,
                            userType = 'group',
                            platform = plugin_event.platform['platform']
                        )
            
                OlivaDiceCore.userConfig.writeUserConfigByUserHash(
                    userHash = OlivaDiceCore.userConfig.getUserHash(
                        userId = tmp_hagID,
                        userType = 'group',
                        platform = plugin_event.platform['platform']
                    )
                )
                return

            elif isMatchWordStart(tmp_reast_str, 'upload'):
                tmp_reast_str = getMatchWordStartRight(tmp_reast_str, 'upload')
                tmp_reast_str = skipSpaceStart(tmp_reast_str)

                if not tmp_reast_str.strip():
                    tmp_reply_str = OlivaDiceCore.msgCustomManager.formatReplySTR(dictStrCustom['strLoggerLogUploadNoName'], dictTValue)
                    replyMsg(plugin_event, tmp_reply_str)
                    return

                log_uuid = tmp_reast_str.strip()
                log_name = None
                
                dataPath = OlivaDiceLogger.data.dataPath
                dataLogPath = OlivaDiceLogger.data.dataLogPath
                log_files = [f for f in os.listdir(f'{dataPath}{dataLogPath}') 
                           if f.startswith(f'log_{log_uuid}_') and f.endswith('.trpglog')]
                
                if log_files:
                    # 从文件名中提取log_name
                    log_name = log_files[0].replace(f'log_{log_uuid}_', '').replace('.trpglog', '')
                
                if not log_name:
                    dictTValue['tLogUUID'] = log_uuid
                    tmp_reply_str = OlivaDiceCore.msgCustomManager.formatReplySTR(dictStrCustom['strLoggerLogFileNotFound'], dictTValue)
                    replyMsg(plugin_event, tmp_reply_str)
                    return

                tmp_logName = f'log_{log_uuid}_{log_name}'
                dataPath = OlivaDiceLogger.data.dataPath
                dataLogPath = OlivaDiceLogger.data.dataLogPath
                dataLogFile_1 = f'{dataPath}{dataLogPath}/{tmp_logName}.trpglog'

                try:
                    OlivaDiceLogger.logger.uploadLogFile(tmp_logName)
                    dictTValue['tLogName'] = log_name
                    dictTValue['tLogUUID'] = log_uuid
                    encoded_logName = urllib.parse.quote(tmp_logName)
                    dictTValue['tLogUrl'] = f'{OlivaDiceLogger.data.dataLogPainterUrl}{encoded_logName}'
                    tmp_reply_str = OlivaDiceCore.msgCustomManager.formatReplySTR(dictStrCustom['strLoggerLogUploadSuccess'], dictTValue)
                    replyMsg(plugin_event, tmp_reply_str)
                except Exception as e:
                    dictTValue['tLogName'] = log_name
                    dictTValue['tLogUUID'] = log_uuid
                    tmp_reply_str = OlivaDiceCore.msgCustomManager.formatReplySTR(dictStrCustom['strLoggerLogUploadFailed'], dictTValue)
                    replyMsg(plugin_event, tmp_reply_str)
                    traceback.print_exc()
                return
            elif isMatchWordStart(tmp_reast_str, 'temp'):
                tmp_reast_str = getMatchWordStartRight(tmp_reast_str, 'temp')
                tmp_reast_str = skipSpaceStart(tmp_reast_str)

                log_name = OlivaDiceCore.userConfig.getUserConfigByKey(
                    userId = tmp_hagID,
                    userType = 'group',
                    platform = plugin_event.platform['platform'],
                    userConfigKey = 'logActiveName',
                    botHash = plugin_event.bot_info.hash
                )

                if tmp_reast_str.strip() != '':
                    log_name = tmp_reast_str.strip()

                if not log_name:
                    tmp_reply_str = OlivaDiceCore.msgCustomManager.formatReplySTR(dictStrCustom['strLoggerLogAlreadyOff'], dictTValue)
                    replyMsg(plugin_event, tmp_reply_str)
                    return

                log_name_list = OlivaDiceCore.userConfig.getUserConfigByKey(
                    userId = tmp_hagID,
                    userType = 'group',
                    platform = plugin_event.platform['platform'],
                    userConfigKey = 'logNameList',
                    botHash = plugin_event.bot_info.hash
                ) or []

                if log_name not in log_name_list:
                    dictTValue['tLogName'] = log_name
                    tmp_reply_str = OlivaDiceCore.msgCustomManager.formatReplySTR(dictStrCustom['strLoggerLogNameNotFound'], dictTValue)
                    replyMsg(plugin_event, tmp_reply_str)
                    return

                log_name_dict = OlivaDiceCore.userConfig.getUserConfigByKey(
                    userId = tmp_hagID,
                    userType = 'group',
                    platform = plugin_event.platform['platform'],
                    userConfigKey = 'logNameDict',
                    botHash = plugin_event.bot_info.hash
                ) or {}

                tmp_log_uuid = log_name_dict.get(log_name, str(uuid.uuid4()))
                tmp_logName = f'log_{tmp_log_uuid}_{log_name}'
                
                # 生成临时日志文件（添加 _temp 后缀）
                if OlivaDiceLogger.logger.releaseLogFile(tmp_logName, temp=True):
                    OlivaDiceLogger.logger.uploadLogFile(tmp_logName + '_temp')
                    dictTValue['tLogName'] = log_name
                    dictTValue['tLogUUID'] = tmp_log_uuid
                    encoded_logName = urllib.parse.quote(tmp_logName)
                    dictTValue['tLogUrl'] = '%s%s_temp' % (
                        OlivaDiceLogger.data.dataLogPainterUrl,
                        encoded_logName
                    )
                    tmp_reply_str = OlivaDiceCore.msgCustomManager.formatReplySTR(dictStrCustom['strLoggerLogTempSuccess'], dictTValue)
                else:
                    dictTValue['tLogName'] = log_name
                    dictTValue['tLogUUID'] = tmp_log_uuid
                    tmp_reply_str = OlivaDiceCore.msgCustomManager.formatReplySTR(dictStrCustom['strLoggerLogTempFailed'], dictTValue)

                replyMsg(plugin_event, tmp_reply_str)
                return
            elif isMatchWordStart(tmp_reast_str, 'rename'):
                tmp_reast_str = getMatchWordStartRight(tmp_reast_str, 'rename')
                tmp_reast_str = skipSpaceStart(tmp_reast_str)
                            
                parts = tmp_reast_str.split('/', 1)
                new_name = parts[0].strip()
                old_name = parts[1].strip() if len(parts) > 1 else None

                if not OlivaDiceLogger.logger.is_valid_log_name(new_name) or new_name == '':
                    dictTValue['tLogName'] = new_name
                    tmp_reply_str = OlivaDiceCore.msgCustomManager.formatReplySTR(
                        dictStrCustom['strLoggerLogInvalidName'], 
                        dictTValue
                    )
                    replyMsg(plugin_event, tmp_reply_str)
                    return

                if not old_name:
                    old_name = OlivaDiceCore.userConfig.getUserConfigByKey(
                        userId=tmp_hagID,
                        userType='group',
                        platform=plugin_event.platform['platform'],
                        userConfigKey='logActiveName',
                        botHash=plugin_event.bot_info.hash
                    )

                    if not old_name:
                        tmp_reply_str = OlivaDiceCore.msgCustomManager.formatReplySTR(
                            dictStrCustom['strLoggerLogAlreadyOff'], 
                            dictTValue
                        )
                        replyMsg(plugin_event, tmp_reply_str)
                        return

                if old_name == new_name:
                    dictTValue['tLogName'] = new_name
                    tmp_reply_str = OlivaDiceCore.msgCustomManager.formatReplySTR(
                        dictStrCustom['strLoggerLogRenameSameName'], 
                        dictTValue
                    )
                    replyMsg(plugin_event, tmp_reply_str)
                    return

                log_name_list = OlivaDiceCore.userConfig.getUserConfigByKey(
                    userId=tmp_hagID,
                    userType='group',
                    platform=plugin_event.platform['platform'],
                    userConfigKey='logNameList',
                    botHash=plugin_event.bot_info.hash
                ) or []

                log_name_dict = OlivaDiceCore.userConfig.getUserConfigByKey(
                    userId=tmp_hagID,
                    userType='group',
                    platform=plugin_event.platform['platform'],
                    userConfigKey='logNameDict',
                    botHash=plugin_event.bot_info.hash
                ) or {}

                if old_name not in log_name_list:
                    dictTValue['tLogName'] = old_name
                    tmp_reply_str = OlivaDiceCore.msgCustomManager.formatReplySTR(
                        dictStrCustom['strLoggerLogNotFound'], 
                        dictTValue
                    )
                    replyMsg(plugin_event, tmp_reply_str)
                    return

                if new_name in log_name_list:
                    dictTValue['tLogName'] = new_name
                    tmp_reply_str = OlivaDiceCore.msgCustomManager.formatReplySTR(
                        dictStrCustom['strLoggerLogRenameNameExists'], 
                        dictTValue
                    )
                    replyMsg(plugin_event, tmp_reply_str)
                    return

                log_uuid = log_name_dict.get(old_name, str(uuid.uuid4()))

                log_name_list[log_name_list.index(old_name)] = new_name
                log_name_dict[new_name] = log_uuid
                del log_name_dict[old_name]

                active_log_name = OlivaDiceCore.userConfig.getUserConfigByKey(
                    userId=tmp_hagID,
                    userType='group',
                    platform=plugin_event.platform['platform'],
                    userConfigKey='logActiveName',
                    botHash=plugin_event.bot_info.hash
                )

                if active_log_name == old_name:
                    OlivaDiceCore.userConfig.setUserConfigByKey(
                        userConfigKey='logActiveName',
                        userConfigValue=new_name,
                        botHash=plugin_event.bot_info.hash,
                        userId=tmp_hagID,
                        userType='group',
                        platform=plugin_event.platform['platform']
                    )

                OlivaDiceCore.userConfig.setUserConfigByKey(
                    userConfigKey='logNameList',
                    userConfigValue=log_name_list,
                    botHash=plugin_event.bot_info.hash,
                    userId=tmp_hagID,
                    userType='group',
                    platform=plugin_event.platform['platform']
                )

                OlivaDiceCore.userConfig.setUserConfigByKey(
                    userConfigKey='logNameDict',
                    userConfigValue=log_name_dict,
                    botHash=plugin_event.bot_info.hash,
                    userId=tmp_hagID,
                    userType='group',
                    platform=plugin_event.platform['platform']
                )

                # 重命名日志文件
                old_log_name = f'log_{log_uuid}_{old_name}'
                new_log_name = f'log_{log_uuid}_{new_name}'

                dataPath = OlivaDiceLogger.data.dataPath
                dataLogPath = OlivaDiceLogger.data.dataLogPath

                for ext in ['.olivadicelog', '.trpglog', '_temp.trpglog']:
                    old_file = f'{dataPath}{dataLogPath}/{old_log_name}{ext}'
                    new_file = f'{dataPath}{dataLogPath}/{new_log_name}{ext}'
                    if os.path.exists(old_file):
                        try:
                            os.rename(old_file, new_file)
                        except Exception as e:
                            traceback.print_exc()

                dictTValue['tLogOldName'] = old_name
                dictTValue['tLogNewName'] = new_name

                if active_log_name == old_name:
                    tmp_reply_str = OlivaDiceCore.msgCustomManager.formatReplySTR(
                        dictStrCustom['strLoggerLogRenameActiveSuccess'], 
                        dictTValue
                    )
                else:
                    tmp_reply_str = OlivaDiceCore.msgCustomManager.formatReplySTR(
                        dictStrCustom['strLoggerLogRenameSuccess'], 
                        dictTValue
                    )

                replyMsg(plugin_event, tmp_reply_str)
                return
            else:
                replyMsgLazyHelpByEvent(plugin_event, 'log')
            return
