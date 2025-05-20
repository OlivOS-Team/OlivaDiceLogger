# -*- encoding: utf-8 -*-
'''
_______________________    _________________________________________
__  __ \__  /____  _/_ |  / /__    |__  __ \___  _/_  ____/__  ____/
_  / / /_  /  __  / __ | / /__  /| |_  / / /__  / _  /    __  __/   
/ /_/ /_  /____/ /  __ |/ / _  ___ |  /_/ /__/ /  / /___  _  /___   
\____/ /_____/___/  _____/  /_/  |_/_____/ /___/  \____/  /_____/   

@File      :   userConfig.py
@Author    :   lunzhiPenxil仑质
@Contact   :   lunzhipenxil@gmail.com
@License   :   AGPL
@Copyright :   (C) 2020-2021, OlivOS-Team
@Desc      :   None
'''

import OlivaDiceCore
import OlivaDiceLogger

dictUserConfigNoteDefault = {
    'logEnable' : False,
    'logNowName' : None,
    'logActiveName': None,  # 当前活跃的日志名
    'logNameList' : [],     # 所有日志名列表
    'logNameDict' : {}      # 日志名到UUID的映射
}

def initUserConfigNoteDefault(bot_info_dict):
    OlivaDiceCore.userConfig.dictUserConfigNoteDefault.update(
        OlivaDiceLogger.userConfig.dictUserConfigNoteDefault
    )
