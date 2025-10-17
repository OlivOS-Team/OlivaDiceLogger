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
    tmp_id_str = str(plugin_event.base_info['self_id'])
    tmp_at_str_sub = None
    tmp_id_str_sub = None
    if 'sub_self_id' in plugin_event.data.extend:
        if plugin_event.data.extend['sub_self_id'] != None:
            tmp_at_str_sub = OlivOS.messageAPI.PARA.at(plugin_event.data.extend['sub_self_id']).CQ()
            tmp_id_str_sub = str(plugin_event.data.extend['sub_self_id'])
    tmp_command_str_1 = '.'
    tmp_command_str_2 = '。'
    tmp_command_str_3 = '/'
    tmp_reast_str = plugin_event.data.message
    flag_force_reply = False
    flag_is_command = False
    flag_is_from_host = False
    flag_is_from_group = False
    flag_is_from_group_admin = False
    flag_is_from_group_sub_admin = False
    flag_is_from_group_have_admin = False
    flag_is_from_master = False
    if isMatchWordStart(tmp_reast_str, '[CQ:reply,id='):
        tmp_reast_str = skipToRight(tmp_reast_str, ']')
        tmp_reast_str = tmp_reast_str[1:]
    if flag_force_reply is False:
        tmp_reast_str_old = tmp_reast_str
        tmp_reast_obj = OlivOS.messageAPI.Message_templet(
            'old_string',
            tmp_reast_str
        )
        tmp_at_list = []
        for tmp_reast_obj_this in tmp_reast_obj.data:
            tmp_para_str_this = tmp_reast_obj_this.CQ()
            if type(tmp_reast_obj_this) is OlivOS.messageAPI.PARA.at:
                tmp_at_list.append(str(tmp_reast_obj_this.data['id']))
                tmp_reast_str = tmp_reast_str.lstrip(tmp_para_str_this)
            elif type(tmp_reast_obj_this) is OlivOS.messageAPI.PARA.text:
                if tmp_para_str_this.strip(' ') == '':
                    tmp_reast_str = tmp_reast_str.lstrip(tmp_para_str_this)
                else:
                    break
            else:
                break
        if tmp_id_str in tmp_at_list:
            flag_force_reply = True
        if tmp_id_str_sub in tmp_at_list:
            flag_force_reply = True
        if 'all' in tmp_at_list:
            flag_force_reply = True
        if flag_force_reply is True:
            tmp_reast_str = skipSpaceStart(tmp_reast_str)
        else:
            tmp_reast_str = tmp_reast_str_old
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

            # 检查是否有日志正在进行end操作(锁定状态)
            log_ending_lock = OlivaDiceCore.userConfig.getUserConfigByKey(
                userId = tmp_hagID,
                userType = 'group',
                platform = plugin_event.platform['platform'],
                userConfigKey = 'logEndingLock',
                botHash = plugin_event.bot_info.hash
            )
            
            if log_ending_lock:
                # 如果正在进行end操作，阻止所有其他log命令
                tmp_reply_str = OlivaDiceCore.msgCustomManager.formatReplySTR(
                    dictStrCustom['strLoggerLogEndingInProgress'], 
                    dictTValue
                )
                replyMsg(plugin_event, tmp_reply_str)
                return

            if isMatchWordStart(tmp_reast_str, ['on','new']):
                tmp_reast_str = getMatchWordStartRight(tmp_reast_str, ['on','new'])
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

                log_name_time_dict = OlivaDiceCore.userConfig.getUserConfigByKey(
                    userId = tmp_hagID,
                    userType = 'group',
                    platform = plugin_event.platform['platform'],
                    userConfigKey = 'logNameTimeDict',
                    botHash = plugin_event.bot_info.hash
                ) or {}

                is_continue = log_name in log_name_list
                last_message_id = None

                if is_continue:
                    # 获取最后一个message_id
                    tmp_log_uuid = log_name_dict.get(log_name, str(uuid.uuid4()))
                    tmp_logName = f'log_{tmp_log_uuid}_{log_name}'
                    dataPath = OlivaDiceLogger.data.dataPath
                    dataLogPath = OlivaDiceLogger.data.dataLogPath
                    dataLogFile = f'{dataPath}{dataLogPath}/{tmp_logName}.olivadicelog'
                    last_message_id = OlivaDiceLogger.logger.get_last_message_id(dataLogFile)

                if log_name not in log_name_list:
                    log_name_list.append(log_name)
                    log_name_dict[log_name] = str(uuid.uuid4())
                    log_name_time_dict[log_name] = {
                        'start_time': time.time(),
                        'end_time': 0,
                        'total_time': 0
                    }
                    dictTValue['tLogName'] = log_name
                    tmp_reply_str = OlivaDiceCore.msgCustomManager.formatReplySTR(dictStrCustom['strLoggerLogOn'], dictTValue)
                else:
                    # 继续记录，更新开始时间
                    log_name_time_dict[log_name]['start_time'] = time.time()
                    # 更新结束时间为0，便于后面temp判断是不是正在进行的日志（如果off了end_time就不会是0）
                    log_name_time_dict[log_name]['end_time'] = 0
                    tmp_log_uuid = log_name_dict.get(log_name, str(uuid.uuid4()))
                    tmp_logName = f'log_{tmp_log_uuid}_{log_name}'
                    log_lines = OlivaDiceLogger.logger.get_log_lines(tmp_logName)
                    total_duration = log_name_time_dict[log_name]['total_time']
                    formatted_duration = OlivaDiceLogger.logger.format_duration(int(total_duration))
                    dictTValue['tLogLines'] = str(log_lines)
                    dictTValue['tLogName'] = log_name
                    dictTValue['tLogTime'] = formatted_duration
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

                OlivaDiceCore.userConfig.setUserConfigByKey(
                    userConfigKey = 'logNameTimeDict',
                    userConfigValue = log_name_time_dict,
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
                
                log_quote = OlivaDiceCore.userConfig.getUserConfigByKey(
                    userId = tmp_hagID,
                    userType = 'group',
                    platform = plugin_event.platform['platform'],
                    userConfigKey = 'logQuote',
                    botHash = plugin_event.bot_info.hash,
                    default = False
                )
                # 如果是继续日志且有最后一个 message_id 并且开启了 log quote，尝试引用回复
                if is_continue and last_message_id and log_quote:
                    if plugin_event.platform['platform'] == 'qq':
                        try:
                            # 尝试构造引用回复消息
                            dictTValue['tLogName'] = log_name
                            tmp_reply_str_2 = OlivaDiceCore.msgCustomManager.formatReplySTR(dictStrCustom['strLoggerLogQuote'], dictTValue)
                            reply_with_quote = f'[CQ:reply,id={last_message_id}]{tmp_reply_str_2}'
                            replyMsg(plugin_event, reply_with_quote)
                        except:
                            # 如果引用回复失败，抛出异常回复
                            dictTValue['tLogName'] = log_name
                            tmp_reply_str = OlivaDiceCore.msgCustomManager.formatReplySTR(
                                dictStrCustom['strLoggerLogQuoteError'], 
                                dictTValue
                            )
                            replyMsg(plugin_event, tmp_reply_str)
                    else:
                        # 其他平台不支持引用回复
                        dictTValue['tLogName'] = log_name
                        tmp_reply_str = OlivaDiceCore.msgCustomManager.formatReplySTR(
                            dictStrCustom['strLoggerLogQuoteError'], 
                            dictTValue
                        )
                        replyMsg(plugin_event, tmp_reply_str)
                # 正常回复
                replyMsg(plugin_event, tmp_reply_str)
                return
            elif isMatchWordStart(tmp_reast_str, 'off'):
                tmp_reast_str = getMatchWordStartRight(tmp_reast_str, 'off')
                tmp_reast_str = skipSpaceStart(tmp_reast_str)

                is_logging = OlivaDiceCore.userConfig.getUserConfigByKey(
                    userId = tmp_hagID,
                    userType = 'group',
                    platform = plugin_event.platform['platform'],
                    userConfigKey = 'logEnable',
                    botHash = plugin_event.bot_info.hash
                )

                if not is_logging:
                    tmp_reply_str = OlivaDiceCore.msgCustomManager.formatReplySTR(
                        dictStrCustom['strLoggerLogAlreadyOff'], 
                        dictTValue
                    )
                    replyMsg(plugin_event, tmp_reply_str)
                    return

                log_name = OlivaDiceCore.userConfig.getUserConfigByKey(
                    userId = tmp_hagID,
                    userType = 'group',
                    platform = plugin_event.platform['platform'],
                    userConfigKey = 'logActiveName',
                    botHash = plugin_event.bot_info.hash
                )

                if tmp_reast_str.strip() != '':
                    log_name = tmp_reast_str.strip()

                log_name_dict = OlivaDiceCore.userConfig.getUserConfigByKey(
                    userId = tmp_hagID,
                    userType = 'group',
                    platform = plugin_event.platform['platform'],
                    userConfigKey = 'logNameDict',
                    botHash = plugin_event.bot_info.hash
                ) or {}
                
                log_name_time_dict = OlivaDiceCore.userConfig.getUserConfigByKey(
                    userId = tmp_hagID,
                    userType = 'group',
                    platform = plugin_event.platform['platform'],
                    userConfigKey = 'logNameTimeDict',
                    botHash = plugin_event.bot_info.hash
                ) or {}
                
                tmp_log_uuid = log_name_dict.get(log_name, str(uuid.uuid4()))
                tmp_logName = f'log_{tmp_log_uuid}_{log_name}'
                log_lines = OlivaDiceLogger.logger.get_log_lines(tmp_logName)

                # 更新时间记录
                if log_name in log_name_time_dict:
                    time_record = log_name_time_dict[log_name]
                    current_time = time.time()
                    if time_record['start_time'] > 0:
                        duration = current_time - time_record['start_time']
                        time_record['total_time'] += duration
                        time_record['end_time'] = current_time
                    total_duration = time_record['total_time']
                    formatted_duration = OlivaDiceLogger.logger.format_duration(int(total_duration))
                    dictTValue['tLogTime'] = formatted_duration
                
                OlivaDiceCore.userConfig.setUserConfigByKey(
                    userConfigKey = 'logNameTimeDict',
                    userConfigValue = log_name_time_dict,
                    botHash = plugin_event.bot_info.hash,
                    userId = tmp_hagID,
                    userType = 'group',
                    platform = plugin_event.platform['platform']
                )

                OlivaDiceCore.userConfig.setUserConfigByKey(
                    userConfigKey = 'logEnable',
                    userConfigValue=False,
                    botHash = plugin_event.bot_info.hash,
                    userId = tmp_hagID,
                    userType = 'group',
                    platform = plugin_event.platform['platform']
                )

                dictTValue['tLogLines'] = str(log_lines)
                dictTValue['tLogName'] = log_name
                tmp_reply_str = OlivaDiceCore.msgCustomManager.formatReplySTR(
                    dictStrCustom['strLoggerLogOff'], 
                    dictTValue
                )

                OlivaDiceCore.userConfig.writeUserConfigByUserHash(
                    userHash=OlivaDiceCore.userConfig.getUserHash(
                        userId = tmp_hagID,
                        userType = 'group',
                        platform = plugin_event.platform['platform']
                    )
                )
                replyMsg(plugin_event, tmp_reply_str)
                return

            elif isMatchWordStart(tmp_reast_str, 'end'):
                tmp_reast_str = getMatchWordStartRight(tmp_reast_str, 'end')
                tmp_reast_str = skipSpaceStart(tmp_reast_str)

                # 在第一次回复时立即设置锁定状态，防止多次触发
                OlivaDiceCore.userConfig.setUserConfigByKey(
                    userConfigKey = 'logEndingLock',
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
                    # 解除锁定
                    OlivaDiceCore.userConfig.setUserConfigByKey(
                        userConfigKey = 'logEndingLock',
                        userConfigValue = False,
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
                    # 解除锁定
                    OlivaDiceCore.userConfig.setUserConfigByKey(
                        userConfigKey = 'logEndingLock',
                        userConfigValue = False,
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
                
                log_name_time_dict = OlivaDiceCore.userConfig.getUserConfigByKey(
                    userId = tmp_hagID,
                    userType = 'group',
                    platform = plugin_event.platform['platform'],
                    userConfigKey = 'logNameTimeDict',
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

                # 显示时间
                total_duration = 0
                if log_name in log_name_time_dict:
                    time_record = log_name_time_dict[log_name]
                    current_time = time.time()
                    # 如果正在记录中，加上当前时长
                    if time_record['start_time'] > 0 and time_record['end_time'] == 0:
                        duration = current_time - time_record['start_time']
                        time_record['total_time'] += duration
                    total_duration = time_record['total_time']
                    formatted_duration = OlivaDiceLogger.logger.format_duration(int(total_duration))
                    dictTValue['tLogTime'] = formatted_duration
                    
                dictTValue['tLogName'] = log_name
                tmp_reply_str = OlivaDiceCore.msgCustomManager.formatReplySTR(dictStrCustom['strLoggerLogEnd'], dictTValue)
                replyMsg(plugin_event, tmp_reply_str)

                upload_success = False
                try:
                    if OlivaDiceLogger.logger.releaseLogFile(tmp_logName, total_duration):
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
                        upload_success = True

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
                                
                            if log_name in log_name_time_dict:
                                del log_name_time_dict[log_name]
                                OlivaDiceCore.userConfig.setUserConfigByKey(
                                    userConfigKey = 'logNameTimeDict',
                                    userConfigValue = log_name_time_dict,
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
                except Exception as e:
                    # 上传失败也要解除锁定
                    traceback.print_exc()
                finally:
                    # 无论成功失败，都解除锁定
                    OlivaDiceCore.userConfig.setUserConfigByKey(
                        userConfigKey = 'logEndingLock',
                        userConfigValue = False,
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

            elif isMatchWordStart(tmp_reast_str, 'list'):
                log_name_list = OlivaDiceCore.userConfig.getUserConfigByKey(
                    userId = tmp_hagID,
                    userType = 'group',
                    platform = plugin_event.platform['platform'],
                    userConfigKey = 'logNameList',
                    botHash = plugin_event.bot_info.hash
                ) or []

                log_name_time_dict = OlivaDiceCore.userConfig.getUserConfigByKey(
                    userId = tmp_hagID,
                    userType = 'group',
                    platform = plugin_event.platform['platform'],
                    userConfigKey = 'logNameTimeDict',
                    botHash = plugin_event.bot_info.hash
                ) or {}

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
                        # time_info = ""
                        # if name in log_name_time_dict:
                        #     total_duration = log_name_time_dict[name]['total_time']
                        #     # 如果正在记录中，加上日志时长
                        #     if log_name_time_dict[name]['start_time'] > 0 and log_name_time_dict[name]['end_time'] == 0:
                        #         current_duration = time.time() - log_name_time_dict[name]['start_time']
                        #         total_duration += current_duration
                        #     time_info = f" (总时长: {OlivaDiceLogger.logger.format_duration(int(total_duration))})"
                        
                        # if name == active_log_name:
                        #     log_list_str.append(f"- {name} (当前日志){time_info}")
                        # else:
                        #     log_list_str.append(f"- {name}{time_info}")

                        if name == active_log_name:
                            log_list_str.append(f"- {name} (当前日志)")
                        else:
                            log_list_str.append(f"- {name}")

                    dictTValue['tLogList'] = '\n'.join(log_list_str)
                    tmp_reply_str = OlivaDiceCore.msgCustomManager.formatReplySTR(dictStrCustom['strLoggerLogList'], dictTValue)

                replyMsg(plugin_event, tmp_reply_str)
                return
            
            elif isMatchWordStart(tmp_reast_str, ['stop','halt']):
                tmp_reast_str = getMatchWordStartRight(tmp_reast_str, ['stop','halt'])
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

                log_name_time_dict = OlivaDiceCore.userConfig.getUserConfigByKey(
                    userId = tmp_hagID,
                    userType = 'group',
                    platform = plugin_event.platform['platform'],
                    userConfigKey = 'logNameTimeDict',
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

                # 显示时间
                total_duration = 0
                if log_name in log_name_time_dict:
                    time_record = log_name_time_dict[log_name]
                    current_time = time.time()
                    # 如果正在记录中，加上当前时长
                    if time_record['start_time'] > 0 and time_record['end_time'] == 0:
                        duration = current_time - time_record['start_time']
                        time_record['total_time'] += duration
                    total_duration = time_record['total_time']
                    formatted_duration = OlivaDiceLogger.logger.format_duration(int(total_duration))
                    dictTValue['tLogTime'] = formatted_duration
                # 强制生成.trpglog文件
                success = OlivaDiceLogger.logger.releaseLogFile(tmp_logName, total_duration)
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

                    if log_name in log_name_time_dict:
                        del log_name_time_dict[log_name]
                        OlivaDiceCore.userConfig.setUserConfigByKey(
                            userConfigKey = 'logNameTimeDict',
                            userConfigValue = log_name_time_dict,
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

                # 从olivadicelog文件中读取时长
                total_duration = 0
                olivadicelog_file = f'{dataPath}{dataLogPath}/{tmp_logName}.olivadicelog'
                if os.path.exists(olivadicelog_file):
                    with open(olivadicelog_file, 'r', encoding='utf-8') as f:
                        for line in f:
                            try:
                                record = json.loads(line.strip())
                                if record.get('type') == 'log_total_duration':
                                    total_duration = record.get('total_time', 0)
                                    break
                            except:
                                continue
                            
                formatted_duration = OlivaDiceLogger.logger.format_duration(int(total_duration))
                dictTValue['tLogTime'] = formatted_duration

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
            elif isMatchWordStart(tmp_reast_str, ['temp','get','tmp']):
                tmp_reast_str = getMatchWordStartRight(tmp_reast_str, ['temp','get','tmp'])
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

                log_name_time_dict = OlivaDiceCore.userConfig.getUserConfigByKey(
                    userId = tmp_hagID,
                    userType = 'group',
                    platform = plugin_event.platform['platform'],
                    userConfigKey = 'logNameTimeDict',
                    botHash = plugin_event.bot_info.hash
                ) or {}

                tmp_log_uuid = log_name_dict.get(log_name, str(uuid.uuid4()))
                tmp_logName = f'log_{tmp_log_uuid}_{log_name}'
                total_duration = 0
                if log_name in log_name_time_dict:
                    time_record = log_name_time_dict[log_name]
                    current_time = time.time()
                    # 如果正在记录中，加上当前时长
                    if time_record['start_time'] > 0 and time_record['end_time'] == 0:
                        duration = current_time - time_record['start_time']
                        time_record['total_time'] += duration
                    total_duration = time_record['total_time']
                    formatted_duration = OlivaDiceLogger.logger.format_duration(int(total_duration))
                    dictTValue['tLogTime'] = formatted_duration
                
                # 生成临时日志文件（添加 _temp 后缀）
                if OlivaDiceLogger.logger.releaseLogFile(tmp_logName, total_duration, temp=True):
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
                        userId = tmp_hagID,
                        userType = 'group',
                        platform = plugin_event.platform['platform'],
                        userConfigKey = 'logActiveName',
                        botHash = plugin_event.bot_info.hash
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

                log_name_time_dict = OlivaDiceCore.userConfig.getUserConfigByKey(
                    userId = tmp_hagID,
                    userType = 'group',
                    platform = plugin_event.platform['platform'],
                    userConfigKey = 'logNameTimeDict',
                    botHash = plugin_event.bot_info.hash
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

                # 更新时间记录字典
                if old_name in log_name_time_dict:
                    log_name_time_dict[new_name] = log_name_time_dict[old_name]
                    del log_name_time_dict[old_name]

                active_log_name = OlivaDiceCore.userConfig.getUserConfigByKey(
                    userId = tmp_hagID,
                    userType = 'group',
                    platform = plugin_event.platform['platform'],
                    userConfigKey = 'logActiveName',
                    botHash = plugin_event.bot_info.hash
                )

                if active_log_name == old_name:
                    OlivaDiceCore.userConfig.setUserConfigByKey(
                        userConfigKey = 'logActiveName',
                        userConfigValue = new_name,
                        botHash = plugin_event.bot_info.hash,
                        userId = tmp_hagID,
                        userType = 'group',
                        platform = plugin_event.platform['platform']
                    )

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

                OlivaDiceCore.userConfig.setUserConfigByKey(
                    userConfigKey = 'logNameTimeDict',
                    userConfigValue = log_name_time_dict,
                    botHash = plugin_event.bot_info.hash,
                    userId = tmp_hagID,
                    userType = 'group',
                    platform = plugin_event.platform['platform']
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
            elif isMatchWordStart(tmp_reast_str, 'set'):
                tmp_reast_str = getMatchWordStartRight(tmp_reast_str, 'set')
                tmp_reast_str = skipSpaceStart(tmp_reast_str)
                
                # 检查是否正在记录
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
                    
                log_name = tmp_reast_str.strip()
                if not log_name:
                    replyMsgLazyHelpByEvent(plugin_event, 'log')
                    return
                    
                log_name_list = OlivaDiceCore.userConfig.getUserConfigByKey(
                    userId = tmp_hagID,
                    userType = 'group',
                    platform = plugin_event.platform['platform'],
                    userConfigKey = 'logNameList',
                    botHash = plugin_event.bot_info.hash
                ) or []
                # 首先尝试直接切换（精确匹配）
                if log_name in log_name_list:
                    # 设置活跃日志
                    OlivaDiceCore.userConfig.setUserConfigByKey(
                        userConfigKey = 'logActiveName',
                        userConfigValue = log_name,
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
                    dictTValue['tLogSelection'] = log_name
                    dictTValue['tLogName'] = log_name
                    tmp_reply_str = OlivaDiceCore.msgCustomManager.formatReplySTR(
                        dictStrCustom['strLoggerLogActiveSwitch'], 
                        dictTValue
                    )
                    replyMsg(plugin_event, tmp_reply_str)
                else:
                    # 如果直接切换失败，尝试模糊搜索
                    if len(log_name_list) > 0:
                        dictTValue['tLogName'] = log_name
                        dictTValue['tLogSelection'] = log_name
                        selected_log_name = OlivaDiceCore.helpDoc.fuzzySearchAndSelect(
                            key_str = log_name,
                            item_list = log_name_list,
                            bot_hash = plugin_event.bot_info.hash,
                            plugin_event = plugin_event,
                            strRecommendKey = 'strLoggerLogSetRecommend',
                            strErrorKey = 'strLoggerLogNotFound',
                            dictStrCustom = dictStrCustom,
                            dictTValue = dictTValue
                        )
                        # 如果用户选择了某个日志，切换到该日志
                        if selected_log_name is not None:
                            OlivaDiceCore.userConfig.setUserConfigByKey(
                                userConfigKey = 'logActiveName',
                                userConfigValue = selected_log_name,
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
                            dictTValue['tLogName'] = selected_log_name
                            tmp_reply_str = OlivaDiceCore.msgCustomManager.formatReplySTR(
                                dictStrCustom['strLoggerLogActiveSwitch'], 
                                dictTValue
                            )
                            replyMsg(plugin_event, tmp_reply_str)
                    else:
                        # 如果没有任何日志，显示错误
                        dictTValue['tLogName'] = log_name
                        tmp_reply_str = OlivaDiceCore.msgCustomManager.formatReplySTR(
                            dictStrCustom['strLoggerLogNotFound'], 
                            dictTValue
                        )
                        replyMsg(plugin_event, tmp_reply_str)
                return
            elif isMatchWordStart(tmp_reast_str, ['quote','reply']):
                tmp_reast_str = getMatchWordStartRight(tmp_reast_str, ['quote','reply'])
                tmp_reast_str = skipSpaceStart(tmp_reast_str)
                tmp_pc_platform = plugin_event.platform['platform']
                # 处理 log quote on/off 命令
                log_quote_enabled = OlivaDiceCore.userConfig.getUserConfigByKey(
                    userId = tmp_hagID,
                    userType = 'group',
                    platform = tmp_pc_platform,
                    userConfigKey = 'logQuote',
                    botHash = plugin_event.bot_info.hash,
                    default = False
                )
                if isMatchWordStart(tmp_reast_str, 'on', fullMatch = True):
                    # log quote on 命令
                    if log_quote_enabled:
                        tmp_reply_str = OlivaDiceCore.msgCustomManager.formatReplySTR(dictStrCustom['strLoggerLogQuoteAlreadyOn'], dictTValue)
                    else:
                        OlivaDiceCore.userConfig.setUserConfigByKey(
                            userConfigKey = 'logQuote',
                            userConfigValue = True,
                            botHash = plugin_event.bot_info.hash,
                            userId = tmp_hagID,
                            userType = 'group',
                            platform = tmp_pc_platform
                        )
                        OlivaDiceCore.userConfig.writeUserConfigByUserHash(
                            userHash = OlivaDiceCore.userConfig.getUserHash(
                                userId = tmp_hagID,
                                userType = 'group',
                                platform = tmp_pc_platform
                            )
                        )
                        tmp_reply_str = OlivaDiceCore.msgCustomManager.formatReplySTR(dictStrCustom['strLoggerLogQuoteOn'], dictTValue)
                    replyMsg(plugin_event, tmp_reply_str)
                    return
                elif isMatchWordStart(tmp_reast_str, 'off', fullMatch = True):
                    # log quote off 命令
                    if not log_quote_enabled:
                        tmp_reply_str = OlivaDiceCore.msgCustomManager.formatReplySTR(dictStrCustom['strLoggerLogQuoteAlreadyOff'], dictTValue)
                    else:
                        OlivaDiceCore.userConfig.setUserConfigByKey(
                            userConfigKey = 'logQuote',
                            userConfigValue = False,
                            botHash = plugin_event.bot_info.hash,
                            userId = tmp_hagID,
                            userType = 'group',
                            platform = tmp_pc_platform
                        )
                        OlivaDiceCore.userConfig.writeUserConfigByUserHash(
                            userHash = OlivaDiceCore.userConfig.getUserHash(
                                userId = tmp_hagID,
                                userType = 'group',
                                platform = tmp_pc_platform
                            )
                        )
                        tmp_reply_str = OlivaDiceCore.msgCustomManager.formatReplySTR(dictStrCustom['strLoggerLogQuoteOff'], dictTValue)
                    replyMsg(plugin_event, tmp_reply_str)
                    return
                else:
                    # 如果没有其他参数，尝试引用活跃日志
                    if not tmp_reast_str.strip():
                        # 获取当前活跃日志
                        log_name = OlivaDiceCore.userConfig.getUserConfigByKey(
                            userId = tmp_hagID,
                            userType = 'group',
                            platform = plugin_event.platform['platform'],
                            userConfigKey = 'logActiveName',
                            botHash = plugin_event.bot_info.hash
                        )
                        if not log_name:
                            tmp_reply_str = OlivaDiceCore.msgCustomManager.formatReplySTR(
                                dictStrCustom['strLoggerLogStatusNoLog'], 
                                dictTValue
                            )
                            replyMsg(plugin_event, tmp_reply_str)
                            return
                    else:
                        log_name = tmp_reast_str.strip()

                    # 检查日志是否存在
                    log_name_list = OlivaDiceCore.userConfig.getUserConfigByKey(
                        userId = tmp_hagID,
                        userType = 'group',
                        platform = plugin_event.platform['platform'],
                        userConfigKey = 'logNameList',
                        botHash = plugin_event.bot_info.hash
                    ) or []

                    if log_name not in log_name_list:
                        dictTValue['tLogName'] = log_name
                        tmp_reply_str = OlivaDiceCore.msgCustomManager.formatReplySTR(
                            dictStrCustom['strLoggerLogNotFound'], 
                            dictTValue
                        )
                        replyMsg(plugin_event, tmp_reply_str)
                        return

                    # 获取最后一个message_id
                    log_name_dict = OlivaDiceCore.userConfig.getUserConfigByKey(
                        userId = tmp_hagID,
                        userType = 'group',
                        platform = plugin_event.platform['platform'],
                        userConfigKey = 'logNameDict',
                        botHash = plugin_event.bot_info.hash
                    ) or {}

                    tmp_log_uuid = log_name_dict.get(log_name, str(uuid.uuid4()))
                    tmp_logName = f'log_{tmp_log_uuid}_{log_name}'
                    dataPath = OlivaDiceLogger.data.dataPath
                    dataLogPath = OlivaDiceLogger.data.dataLogPath
                    dataLogFile = f'{dataPath}{dataLogPath}/{tmp_logName}.olivadicelog'
                    last_message_id = OlivaDiceLogger.logger.get_last_message_id(dataLogFile)
                    dictTValue['tLogName'] = log_name
                    if last_message_id and plugin_event.platform['platform'] == 'qq':
                        try:
                            # 尝试构造引用回复消息
                            tmp_reply_str = OlivaDiceCore.msgCustomManager.formatReplySTR(
                                dictStrCustom['strLoggerLogQuote'], 
                                dictTValue
                            )
                            reply_with_quote = f'[CQ:reply,id={last_message_id}]{tmp_reply_str}'
                            replyMsg(plugin_event, reply_with_quote)
                            return
                        except:
                            # 如果引用回复失败，则抛出引用失败回复
                            pass

                    tmp_reply_str = OlivaDiceCore.msgCustomManager.formatReplySTR(
                        dictStrCustom['strLoggerLogQuoteError'], 
                        dictTValue
                    )
                    replyMsg(plugin_event, tmp_reply_str)
            elif isMatchWordStart(tmp_reast_str, 'status'):
                tmp_reast_str = getMatchWordStartRight(tmp_reast_str, 'status')
                tmp_reast_str = skipSpaceStart(tmp_reast_str)
                # 获取指定的日志名称，如果没有指定则使用当前活跃日志
                log_name = tmp_reast_str.strip() if tmp_reast_str.strip() else None
                tmp_reply_str = get_log_status(tmp_hagID, plugin_event, dictTValue, dictStrCustom, log_name)
                replyMsg(plugin_event, tmp_reply_str)
            else:
                log_name = tmp_reast_str.strip() if tmp_reast_str.strip() else None
                # 如果是通过.log查看日志状态，没有名称的话，就返回helper
                if log_name:
                    replyMsgLazyHelpByEvent(plugin_event, 'log')
                    return
                tmp_reply_str = get_log_status(tmp_hagID, plugin_event, dictTValue, dictStrCustom, log_name)
                replyMsg(plugin_event, tmp_reply_str)
            return

def get_log_status(tmp_hagID, plugin_event, dictTValue, dictStrCustom, log_name = None):
    # 虽然前面判断过了，但是为了保险起见这里还是判断一下
    # 如果没有指定日志名称，使用活跃日志
    if log_name is None:
        log_name = OlivaDiceCore.userConfig.getUserConfigByKey(
            userId = tmp_hagID,
            userType = 'group',
            platform = plugin_event.platform['platform'],
            userConfigKey = 'logActiveName',
            botHash = plugin_event.bot_info.hash
        )
        if not log_name:
            return OlivaDiceCore.msgCustomManager.formatReplySTR(
                dictStrCustom['strLoggerLogStatusNoLog'], 
                dictTValue
            )
    # 检查日志是否存在
    log_name_list = OlivaDiceCore.userConfig.getUserConfigByKey(
        userId = tmp_hagID,
        userType = 'group',
        platform = plugin_event.platform['platform'],
        userConfigKey = 'logNameList',
        botHash = plugin_event.bot_info.hash
    ) or []
    
    if log_name not in log_name_list:
        dictTValue['tLogName'] = log_name
        return OlivaDiceCore.msgCustomManager.formatReplySTR(
            dictStrCustom['strLoggerLogNameNotFound'], 
            dictTValue
        )
    # 检查日志是否正在记录
    is_logging = False
    active_log_name = OlivaDiceCore.userConfig.getUserConfigByKey(
        userId = tmp_hagID,
        userType = 'group',
        platform = plugin_event.platform['platform'],
        userConfigKey = 'logActiveName',
        botHash = plugin_event.bot_info.hash
    )
    if log_name == active_log_name:
        is_logging = OlivaDiceCore.userConfig.getUserConfigByKey(
            userId = tmp_hagID,
            userType = 'group',
            platform = plugin_event.platform['platform'],
            userConfigKey = 'logEnable',
            botHash = plugin_event.bot_info.hash
        )
    log_name_dict = OlivaDiceCore.userConfig.getUserConfigByKey(
        userId = tmp_hagID,
        userType = 'group',
        platform = plugin_event.platform['platform'],
        userConfigKey = 'logNameDict',
        botHash = plugin_event.bot_info.hash
    ) or {}
    log_name_time_dict = OlivaDiceCore.userConfig.getUserConfigByKey(
        userId = tmp_hagID,
        userType = 'group',
        platform = plugin_event.platform['platform'],
        userConfigKey = 'logNameTimeDict',
        botHash = plugin_event.bot_info.hash
    ) or {}
    tmp_log_uuid = log_name_dict.get(log_name, str(uuid.uuid4()))
    tmp_logName = f'log_{tmp_log_uuid}_{log_name}'
    log_lines = OlivaDiceLogger.logger.get_log_lines(tmp_logName)
    # 计算总时长
    total_duration = 0
    if log_name in log_name_time_dict:
        time_record = log_name_time_dict[log_name]
        current_time = time.time()
        total_duration = time_record['total_time']
        # 如果正在记录中，加上当前时长
        if log_name == active_log_name and is_logging:
            duration = current_time - time_record['start_time']
            total_duration += duration
    formatted_duration = OlivaDiceLogger.logger.format_duration(int(total_duration))
    dictTValue['tLogName'] = log_name
    dictTValue['tLogUUID'] = tmp_log_uuid
    dictTValue['tLogStatus'] = '开启' if (log_name == active_log_name and is_logging) else '关闭'
    dictTValue['tLogLines'] = str(log_lines)
    dictTValue['tLogTime'] = formatted_duration
    return OlivaDiceCore.msgCustomManager.formatReplySTR(
        dictStrCustom['strLoggerLogStatus'], 
        dictTValue
    )