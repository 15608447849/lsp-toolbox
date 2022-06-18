'''
数据库工具类
'''

import os
import traceback
import threading
import json
import datetime
import decimal

pid_index = '%02d' % (os.getpid() % 99)
mLock = threading.RLock()

# 获取当前时间戳 毫秒
def _getCurrentTimestamp():
    import time
    timestamp = int(round(time.time() * 1000))
    return timestamp

def _getCurrentTimestampSec():
    import time
    timestamp = int(time.time())
    return timestamp


########################################################### 每秒产生最多9999个ID
lastTime = _getCurrentTimestamp()
seqIndex = 1
# 时间戳生成唯一ID
def genTimestampDataID():
    global mLock,lastTime,seqIndex
    mLock.acquire()
    try:
        curTime = _getCurrentTimestamp()
        if curTime - lastTime < 1000 and seqIndex <= 9999:
            num_str = '%04d' % seqIndex
            seqIndex = seqIndex + 1
            return '%s%s%s' % (lastTime, num_str, pid_index)
        else:
            lastTime = curTime
            seqIndex = 1
            return genTimestampDataID()

    except Exception as e:
        traceback.print_exc()
        print('获取时间戳产生的数据标识错误',e)
    finally:
        mLock.release()

############################################################## 每秒产生最多999个ID且可设置后缀
lastTimeSec = _getCurrentTimestampSec()
seqIndexSec = 1
# 时间戳生成唯一ID
def genTimestampDataIDSec(suffix='0000%s'% pid_index ):
        global mLock,lastTimeSec,seqIndexSec
        mLock.acquire()
        try:
            curTimeSec = _getCurrentTimestampSec()
            if curTimeSec == lastTimeSec and seqIndexSec <= 999:
                num_str = '%03d' % seqIndexSec
                seqIndexSec = seqIndexSec + 1
                return '%s%s%s' % (lastTimeSec, num_str, suffix)
            else:
                while True:
                    if _getCurrentTimestampSec() > curTimeSec: break
                lastTimeSec = _getCurrentTimestampSec()
                seqIndexSec = 1
                return genTimestampDataIDSec(suffix)
        except Exception as e:
            traceback.print_exc()
            print('获取时间戳产生的数据标识错误', e)
        finally:
            mLock.release()


# 数据行转map
def rowConvertDict(rows,*dictKeys):
    '''按照顺序对 指定键 赋值'''
    dict = {}
    if type(dictKeys[0]) == list:
        dictKeys = dictKeys[0]
    try:
        for i in range(len(dictKeys)):
            try:
                keyObj = dictKeys[i]
                if type(keyObj) == str:
                    _v = rows[i]
                    if isinstance(_v,datetime.datetime):
                        _v = datetime.datetime.strftime(_v, '%Y-%m-%d %H:%M:%S')
                    dict[keyObj] = str(_v if _v is not None else '')


                if type(keyObj) == tuple:
                    kstr = keyObj[0]
                    index = keyObj[1]
                    if len(keyObj) >= 3:
                        func = keyObj[2]
                    else:
                        func = lambda row_index_v: row_index_v
                    _v = func(rows[index])
                    dict[kstr] = str(_v if _v is not None else '')
            except :
                traceback.print_exc()
    except:
        traceback.print_exc()
    return dict

def rowConvertDict_str(rows,dictKeys_str):
    return rowConvertDict(rows,dictKeys_str.split(","))

def linesConvertDict(lines,descriptionList):
    list = []
    for rows in lines:
        maps = rowConvertDict(rows, descriptionList)
        list.append(maps)
    return list

def pauseCreateTableDDL(createDDL, isPrint=False):
    try:
        from ddlparse import DdlParse
        createDDL = createDDL.replace('Nullable(DateTime)', 'DateTime')
        createDDL = createDDL.replace('Array(String)', 'String')
        table = DdlParse().parse(createDDL, source_database=DdlParse.DATABASE.mysql)
        fieldTupleList = []
        for col in table.columns.values():
            if isPrint : print(table.name, col.name, col.data_type, col.comment)
            fieldTupleList.append((col.comment, col.name, col.data_type))
        return table.name , fieldTupleList
    except: return None,None




class _MysqlRowDateToJsonEncoder(json.JSONEncoder):
    def default(self, obj):
            if isinstance(obj, datetime.datetime):
                return obj.strftime('%Y-%m-%d %H:%M:%S')
            elif isinstance(obj, datetime.date):
                return obj.strftime("%Y-%m-%d")
            elif isinstance(obj,datetime.time):
                return obj.strftime("%H:%M:%S")
            elif isinstance(obj, datetime.timedelta):
                return (datetime.datetime.min + obj).time().strftime("%H:%M:%S")
            elif isinstance(obj, decimal.Decimal):
                return str(decimal.Decimal(obj).quantize(decimal.Decimal('0.00')))
            elif isinstance(obj, bytes):
                return str(obj, encoding='utf-8')
            elif isinstance(obj,list):
                return json.dumps(obj, cls=_MysqlRowDateToJsonEncoder,ensure_ascii=False)
            elif isinstance(obj,dict):
                return json.dumps(obj, cls=_MysqlRowDateToJsonEncoder,ensure_ascii=False)
            else:
                return json.JSONEncoder.default(self, obj)

def MysqlRowDateToJsonEncoderFunc(rowsDict):
    return json.dumps(rowsDict, cls=_MysqlRowDateToJsonEncoder,ensure_ascii=False)
