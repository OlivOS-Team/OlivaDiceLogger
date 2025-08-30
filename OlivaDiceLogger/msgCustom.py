# -*- encoding: utf-8 -*-
'''
_______________________    _________________________________________
__  __ \__  /____  _/_ |  / /__    |__  __ \___  _/_  ____/__  ____/
_  / / /_  /  __  / __ | / /__  /| |_  / / /__  / _  /    __  __/   
/ /_/ /_  /____/ /  __ |/ / _  ___ |  /_/ /__/ /  / /___  _  /___   
\____/ /_____/___/  _____/  /_/  |_/_____/ /___/  \____/  /_____/   

@File      :   msgCustom.py
@Author    :   lunzhiPenxil仑质
@Contact   :   lunzhipenxil@gmail.com
@License   :   AGPL
@Copyright :   (C) 2020-2021, OlivOS-Team
@Desc      :   None
'''

import OlivOS
import OlivaDiceCore
import OlivaDiceLogger

dictStrCustomDict = {}

dictStrCustom = {
    'strLoggerLogOn': '开始记录日志 [{tLogName}]',
    'strLoggerLogAlreadyOn': '已经正在记录日志 [{tLogName}]',
    'strLoggerLogContinue': '继续记录日志 [{tLogName}] (当前已记录 {tLogLines} 行，日志总时长: {tLogTime})',
    'strLoggerLogInvalidName': '日志名称 [{tLogName}] 不合法',
    'strLoggerLogOff': '暂停记录日志 [{tLogName}] (当前已记录 {tLogLines} 行，日志总时长: {tLogTime})',
    'strLoggerLogAlreadyOff': '没有正在进行的日志',
    'strLoggerLogEnd': '结束记录日志 [{tLogName}] (当前已记录 {tLogLines} 行，日志总时长: {tLogTime})',
    'strLoggerLogAlreadyEnd': '没有正在进行的日志',
    'strLoggerLogSave': '日志 [{tLogName}] (UUID: {tLogUUID}) 已保存',
    'strLoggerLogUrl': '日志已上传，请在[ {tLogUrl} ]提取日志',
    'strLoggerLogList': '本群有以下日志:\n{tLogList}',
    'strLoggerLogListEmpty': '本群暂无日志',
    'strLoggerLogStop': '已强制停止日志 [{tLogName}] (UUID: {tLogUUID}) (当前已记录 {tLogLines} 行，日志总时长: {tLogTime})',
    'strLoggerLogStopError': '已强制停止日志 [{tLogName}] (UUID: {tLogUUID}) (日志已损坏)',
    'strLoggerLogActiveSwitch': '已切换活跃日志为 [{tLogName}]',
    'strLoggerLogUploadNoName': '请指定要上传的日志的UUID',
    'strLoggerLogFileNotFound': '未找到[{tLogUUID}]对应的日志文件',
    'strLoggerLogUploadSuccess': '日志 [{tLogName}](UUID: {tLogUUID}) 重新上传成功，日志总时长: {tLogTime}，请在[ {tLogUrl} ]提取日志',
    'strLoggerLogUploadFailed': '日志 [{tLogName}](UUID: {tLogUUID}) 重新上传失败，请稍后再试',
    'strLoggerLogNameNotFound': '本群日志列表中未找到名称为[{tLogName}]的日志',
    'strLoggerLogTempSuccess': '临时日志 [{tLogName}] (UUID: {tLogUUID}) 上传成功，日志总时长: {tLogTime}，请在[ {tLogUrl} ]提取日志',
    'strLoggerLogTempFailed': '临时日志 [{tLogName}] (UUID: {tLogUUID}) 上传失败，请稍后再试',
    'strLoggerLogNotFound': '未找到日志 [{tLogName}]',
    'strLoggerLogRenameSuccess': '日志 [{tLogOldName}] 已重命名为 [{tLogNewName}]',
    'strLoggerLogRenameActiveSuccess': '当前活动日志 [{tLogOldName}] 已重命名为 [{tLogNewName}]',
    'strLoggerLogRenameSameName': '新名称 [{tLogName}] 与旧日志名称相同',
    'strLoggerLogRenameNameExists': '日志名称 [{tLogName}] 已存在',
    'strLoggerLogStatus': '当前日志状态:\n名称: {tLogName}\nUUID: {tLogUUID}\n状态: {tLogStatus}\n行数: {tLogLines}\n总时长: {tLogTime}',
    'strLoggerLogStatusNoLog': '当前没有活跃日志'
}

dictStrConst = {
}

dictGValue = {
}

dictTValue = {
    'tLogName': 'N/A',
    'tLogUUID': 'N/A',
    'tLogList': 'N/A',
    'tLogLines': 'N/A',
    'tLogUrl': 'N/A',
    'tLogStatus': 'N/A',
    'tLogTime': '0s'
}

dictHelpDocTemp = {
    'log': '''跑团日志记录
.log on (名字) 开始记录日志
    记录的日志名可以是默认名称或指定名称
.log off (名字) 暂停记录指定日志或当前日志
.log end (名字) 完成记录并发送日志文件
.log status (名字) - 查看指定日志或当前日志的状态
.log temp (名字) 临时上传指定的日志
    临时上传日志不影响记录，若不指定名字则默认为活跃日志
.log stop (名字) 强制停止日志不上传
    若不指定名字则默认为活跃日志
.log set [名字] 切换活跃日志
.log rename [新名字](/旧名字) 重命名活跃日志或指定日志
    若重命名指定日志，新旧名字用 '/' 分隔
.log list 查看本群日志列表
.log upload [UUID] 手动上传指定UUID的日志
    指定UUID的日志必须为已经end/stop的日志

输入 .log 不带参数为查看当前日志状态
日志的默认名称为 default
日志上传存在失败可能，届时请联系后台管理索取''',

    'OlivaDiceLogger': '''[OlivaDiceLogger]
OlivaDice日志模块
本模块为青果跑团掷骰机器人(OlivaDice)跑团日志模块，集成与跑团相关的跑团日志记录功能。
核心开发者: lunzhiPenxil仑质
[.help OlivaDiceLogger更新] 查看本模块更新日志
注: 本模块为可选重要模块。''',

    'OlivaDiceLogger更新': '''[OlivaDiceLogger]
3.0.4: 支持新版OlivOS
3.0.2: 用户记录优化
3.0.0: 初始化项目''',

    '日志': '&log'
}
