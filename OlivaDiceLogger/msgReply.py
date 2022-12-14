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

import hashlib
import time
import uuid

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
                if not OlivaDiceCore.userConfig.getUserConfigByKey(
                    userId = tmp_hagID,
                    userType = 'group',
                    platform = plugin_event.platform['platform'],
                    userConfigKey = 'logEnable',
                    botHash = plugin_event.bot_info.hash
                ):
                    OlivaDiceCore.userConfig.setUserConfigByKey(
                        userConfigKey = 'logEnable',
                        userConfigValue = True,
                        botHash = plugin_event.bot_info.hash,
                        userId = tmp_hagID,
                        userType = 'group',
                        platform = plugin_event.platform['platform']
                    )
                    if OlivaDiceCore.userConfig.getUserConfigByKey(
                        userId = tmp_hagID,
                        userType = 'group',
                        platform = plugin_event.platform['platform'],
                        userConfigKey = 'logNowName',
                        botHash = plugin_event.bot_info.hash
                    ) == None:
                        tmp_new_logName = 'log_%s' % str(uuid.uuid4())
                        OlivaDiceCore.userConfig.setUserConfigByKey(
                            userConfigKey = 'logNowName',
                            userConfigValue = tmp_new_logName,
                            botHash = plugin_event.bot_info.hash,
                            userId = tmp_hagID,
                            userType = 'group',
                            platform = plugin_event.platform['platform']
                        )
                        tmp_reply_str = OlivaDiceCore.msgCustomManager.formatReplySTR(dictStrCustom['strLoggerLogOn'], dictTValue)
                    else:
                        tmp_reply_str = OlivaDiceCore.msgCustomManager.formatReplySTR(dictStrCustom['strLoggerLogContinue'], dictTValue)
                else:
                    tmp_reply_str = OlivaDiceCore.msgCustomManager.formatReplySTR(dictStrCustom['strLoggerLogAlreadyOn'], dictTValue)
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
                if OlivaDiceCore.userConfig.getUserConfigByKey(
                    userId = tmp_hagID,
                    userType = 'group',
                    platform = plugin_event.platform['platform'],
                    userConfigKey = 'logEnable',
                    botHash = plugin_event.bot_info.hash
                ):
                    OlivaDiceCore.userConfig.setUserConfigByKey(
                        userConfigKey = 'logEnable',
                        userConfigValue = False,
                        botHash = plugin_event.bot_info.hash,
                        userId = tmp_hagID,
                        userType = 'group',
                        platform = plugin_event.platform['platform']
                    )
                    tmp_reply_str = OlivaDiceCore.msgCustomManager.formatReplySTR(dictStrCustom['strLoggerLogOff'], dictTValue)
                else:
                    tmp_reply_str = OlivaDiceCore.msgCustomManager.formatReplySTR(dictStrCustom['strLoggerLogAlreadyOff'], dictTValue)
                OlivaDiceCore.userConfig.writeUserConfigByUserHash(
                    userHash = OlivaDiceCore.userConfig.getUserHash(
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
                OlivaDiceCore.userConfig.setUserConfigByKey(
                    userConfigKey = 'logEnable',
                    userConfigValue = False,
                    botHash = plugin_event.bot_info.hash,
                    userId = tmp_hagID,
                    userType = 'group',
                    platform = plugin_event.platform['platform']
                )
                tmp_logName = OlivaDiceCore.userConfig.getUserConfigByKey(
                    userId = tmp_hagID,
                    userType = 'group',
                    platform = plugin_event.platform['platform'],
                    userConfigKey = 'logNowName',
                    botHash = plugin_event.bot_info.hash
                )
                if tmp_logName != None:
                    OlivaDiceCore.userConfig.setUserConfigByKey(
                        userConfigKey = 'logNowName',
                        userConfigValue = None,
                        botHash = plugin_event.bot_info.hash,
                        userId = tmp_hagID,
                        userType = 'group',
                        platform = plugin_event.platform['platform']
                    )
                    tmp_reply_str = OlivaDiceCore.msgCustomManager.formatReplySTR(dictStrCustom['strLoggerLogEnd'], dictTValue)
                    replyMsg(plugin_event, tmp_reply_str)
                    dictTValue['tLogName'] = tmp_logName
                    tmp_reply_str = OlivaDiceCore.msgCustomManager.formatReplySTR(dictStrCustom['strLoggerLogSave'], dictTValue)
                    replyMsg(plugin_event, tmp_reply_str)
                    OlivaDiceLogger.logger.releaseLogFile(tmp_logName)
                    OlivaDiceLogger.logger.uploadLogFile(tmp_logName)
                    dictTValue['tLogUrl'] = '%s%s' % (
                        OlivaDiceLogger.data.dataLogPainterUrl,
                        tmp_logName
                    )
                    tmp_reply_str = OlivaDiceCore.msgCustomManager.formatReplySTR(dictStrCustom['strLoggerLogUrl'], dictTValue)
                    replyMsg(plugin_event, tmp_reply_str)
                else:
                    tmp_reply_str = OlivaDiceCore.msgCustomManager.formatReplySTR(dictStrCustom['strLoggerLogAlreadyEnd'], dictTValue)
                    replyMsg(plugin_event, tmp_reply_str)
                OlivaDiceCore.userConfig.writeUserConfigByUserHash(
                    userHash = OlivaDiceCore.userConfig.getUserHash(
                        userId = tmp_hagID,
                        userType = 'group',
                        platform = plugin_event.platform['platform']
                    )
                )
                return
            else:
                replyMsgLazyHelpByEvent(plugin_event, 'log')
            return
