
_db_mng_map = {}


def MYSQL_SET__GROUP_CONCAT_MAX_LEN(mysql_db, maxLen):
    '''设置mysql group_concat 函数 最大字符数量'''
    try:
        lines = mysql_db.query("show variables like 'group_concat_max_len';")
        if len(lines) == 1:
            curLen = int(lines[0][0])
            if curLen>=maxLen: return
        mysql_db.execute("SET GLOBAL group_concat_max_len = %d;" % maxLen)
        mysql_db.execute("SET SESSION group_concat_max_len = %d;" % maxLen)
        print('mysql concat_group max len: %d ' % maxLen)
    except: pass

def setting_database(database_obj):
    if database_obj.databaseType == 'mysql':
        MYSQL_SET__GROUP_CONCAT_MAX_LEN(database_obj, 4294967295)


def load_database_config(config):
    from modules.database.class_define import DatabaseClearThread,DatabaseManagerBean
    db_clear_thread = DatabaseClearThread()
    # print('连接检测线程',db_clear_thread)
    for session in  config.sections():
        if session.startswith('dbload::'):
            mngName = session.replace('dbload::','',1)
            database_obj = DatabaseManagerBean(config.get(session, 'dbtype'),
                                                       config.get(session, 'host'),
                                                       config.get(session, 'port'),
                                                       config.get(session, 'username'),
                                                       config.get(session, 'password'),
                                                       config.get(session, 'database'),
                                                       db_clear_thread)
            setting_database(database_obj)
            _db_mng_map[mngName] = database_obj
            print("加载数据库管理 %s,%s" % (mngName, str(_db_mng_map[mngName])))


def getDatabaseOperation(databaseName):
    mng = _db_mng_map.get(databaseName,None)
    if mng == None: raise ValueError("找不到指定数据库对象:%s" % databaseName)
    return mng

