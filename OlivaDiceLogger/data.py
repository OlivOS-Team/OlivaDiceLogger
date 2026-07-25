# -*- encoding: utf-8 -*-
r"""
_______________________    _________________________________________
__  __ \__  /____  _/_ |  / /__    |__  __ \___  _/_  ____/__  ____/
_  / / /_  /  __  / __ | / /__  /| |_  / / /__  / _  /    __  __/
/ /_/ /_  /____/ /  __ |/ / _  ___ |  /_/ /__/ /  / /___  _  /___
\____/ /_____/___/  _____/  /_/  |_/_____/ /___/  \____/  /_____/

@File      :   data.py
@Author    :   lunzhiPenxil仑质
@Contact   :   lunzhipenxil@gmail.com
@License   :   AGPL
@Copyright :   (C) 2020-2026, OlivOS-Team
@Desc      :   None
"""

OlivaDiceLogger_ver = '3.0.40'
OlivaDiceLogger_svn = 48
OlivaDiceLogger_ver_short = '%s(%s)' % (str(OlivaDiceLogger_ver), str(OlivaDiceLogger_svn))

dataPath = './plugin/data/OlivaDice/unity'
dataLogPath = '/logger'
dataCompatibilityPath = '/logger_compatibility'
dataCompatibilityFlagFile = 'compatibility_done'

dataLogUpload = 'http://api.dice.center/dicelogger/'
dataLogPainterUrl = 'https://logrender.dice.center/#2-'

# 跨平台续接码（纯内存，不落盘）
# 结构: {uuid_str: {'code': 'A3F9K2', 'time': 1721448000.0, 'old_group_hash': 'md5hex'}}
dictContinueCode = {}
