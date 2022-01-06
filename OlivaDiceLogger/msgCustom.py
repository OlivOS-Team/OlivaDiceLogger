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
    'strLoggerLogOn': '开始记录日志',
    'strLoggerLogAlreadyOn': '已经正在记录日志',
    'strLoggerLogContinue': '继续记录日志',
    'strLoggerLogOff': '暂停记录日志',
    'strLoggerLogAlreadyOff': '没有正在进行的日志',
    'strLoggerLogEnd': '停止记录日志',
    'strLoggerLogAlreadyEnd': '没有正在进行的日志',
    'strLoggerLogSave': '日志[{tLogName}]已保存',
    'strLoggerLogUrl': '日志已上传，请在[{tLogUrl}]提取日志'
}

dictStrConst = {
}

dictGValue = {
}

dictTValue = {
    'tLogName': 'N/A',
    'tLogUrl': 'N/A'
}

dictHelpDocTemp = {
    'log': '''跑团日志记录
.log on 开始记录
.log off 暂停记录
.log end 完成记录并发送日志文件
日志上传存在失败可能，届时请联系后台管理索取''',

    'OlivaDiceLogger': '''[OlivaDiceLogger]
OlivaDice日志模块
本模块为青果跑团掷骰机器人(OlivaDice)跑团日志模块，集成与跑团相关的跑团日志记录功能。
核心开发者: lunzhiPenxil仑质
[.help OlivaDiceLogger更新] 查看本模块更新日志
注: 本模块为可选重要模块。''',

    'OlivaDiceLogger更新': '''[OlivaDiceLogger]
3.0.2: 用户记录优化
3.0.0: 初始化项目''',

    '日志': '&log'
}