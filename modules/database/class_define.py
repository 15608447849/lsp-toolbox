import pymysql,clickhouse_driver,pymssql,threading,datetime,time,traceback
from pymssql import _mssql
from pymssql import _pymssql


class DatabaseConnectBean(object):
    '''数据库连接对象'''
    def __init__(self,connect, checkConnectValidFunc):
        self.connect = connect
        self.lastTime = datetime.datetime.now()
        self.isUse = False
        self.checkConnectValidFunc = checkConnectValidFunc

    def isValid(self):
        if self.connect is None:
            return False
        try:
           return self.checkConnectValidFunc(self.connect)
        except Exception as e:
            traceback.print_exc()
            self.closeConnect()
            return False

    def getConnect(self):
        self.isUse = True
        self.lastTime = datetime.datetime.now()
        return self.connect

    def putConnect(self):
        self.isUse = False
        self.lastTime = datetime.datetime.now()

    def checkOutTime(self, timeout):
        if self.connect is None :
            return True
        if self.isUse is False and (datetime.datetime.now() - self.lastTime).seconds > timeout:
            return True
        return False

    def closeConnect(self):
        try:
            # print("关闭数据库连接",self,self.connect)
            if self.connect is not None:
                self.connect.close()
        except Exception as e:
            traceback.print_exc()
        finally:
            self.connect = None

class DatabaseClearThread(object):
    '''数据库连接池清理对象'''
    def __init__(self,idleTime=5*60):
        self.idleTime = idleTime
        self.databaseManagerList = []
        threading.Thread(name='数据库连接池空闲清理', target=self.run, daemon=True).start()

    def run(self):
        while True:
            time.sleep(self.idleTime)
            for dbmng in self.databaseManagerList:
                # print("连接检测 %s>> %s" % (threading.current_thread().name,str(dbmng.flag)))
                dbmng.clearInvalidConnect()

class DatabaseManagerBean(object):
    '''数据库管理对象'''
    def __init__(self,databaseType,host,port,username,password,databaseName,databaseClearThread):
        if databaseType ==  'mysql' or databaseType == 'clickHouse' or databaseType == 'sqlServer':
            self.flag = "数据库(%s,%s,%s,%s,%s,%s)-%s" \
                        % (databaseType, host, port,username, password,databaseName, datetime.datetime.now().strftime('%Y%m%d%H%M%S'))
        else:
            raise RuntimeError("不支持的数据库类型: %s" % databaseType)

        self.databaseType = databaseType
        self.host = host
        self.port = int(port)
        self.username = username
        self.password = password
        self.databaseName = databaseName
        self.idleTime = databaseClearThread.idleTime
        # Map<线程,数据库连接对象>
        self._thread_databaseConnect_map = {}
        databaseClearThread.databaseManagerList.append(self)

    def clearInvalidConnect(self):
        '''清理无效连接'''
        for threadUse in list(self._thread_databaseConnect_map.keys()):
            try:
                connectHolder = self._thread_databaseConnect_map[threadUse]
                if connectHolder.checkOutTime(self.idleTime):
                    connectHolder.closeConnect()
                    self._thread_databaseConnect_map.pop(threadUse)
            except Exception as e:
                traceback.print_exc()

    def _databaseConnectCreate(self):
        '''创建数据库连接'''
        if self.databaseType == 'mysql':
            return pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.username,
                password=self.password,
                db=self.databaseName,
                charset='utf8',
                autocommit=False,
                read_timeout=self.idleTime,
                write_timeout=self.idleTime)
        if self.databaseType == "clickHouse":
            return clickhouse_driver.connect(
                host=self.host,
                port=self.port,
                user=self.username,
                password=self.password,
                database=self.databaseName,
                connect_timeout=self.idleTime,
                compression=False)
        if self.databaseType == 'sqlServer':
            return  pymssql.connect(
                host=self.host,
                user=self.username,
                password=self.password,
                database=self.databaseName,
                timeout=self.idleTime,
                login_timeout=self.idleTime)
        return None

    def _getConnectCheckFunc(self):
        '''获取连接是否正常的检测函数'''
        func = None
        if self.databaseType == 'mysql':
            def _executeFunc(connect):
                try:
                    connect.ping(reconnect=True)
                    return True
                except:
                    return False
            func = _executeFunc
        if self.databaseType == 'clickHouse':
            def _executeFunc(connect):
                try:
                    return True if connect.is_closed is False else False
                except:
                    return False
            func = _executeFunc
        if self.databaseType == 'sqlServer':
            def _executeFunc(connect):
                try:
                    return connect._conn.connected
                except Exception as e:
                    return False
            func = _executeFunc
        return func

    def threadGetDatabaseConnect(self):
        '''线程获取数据库连接'''
        try:
            connectHolder = self._thread_databaseConnect_map.get(threading.currentThread())
            if connectHolder is None or connectHolder.isValid() is False:
                db_connect = self._databaseConnectCreate()
                connectHolder = DatabaseConnectBean(db_connect, self._getConnectCheckFunc())
                self._thread_databaseConnect_map[threading.currentThread()] = connectHolder
            if connectHolder is None:raise Exception('%s 无法获取数据库连接,当前线程:%s' % (self.flag, threading.currentThread()))

        except Exception as e:
            traceback.print_exc()
            return None, None
        return connectHolder, connectHolder.getConnect()

    def dataErrorCallback(self, e, dataErrorCallback):
        if dataErrorCallback is not None:
            try:
                from pymysql.err import DataError
                if type(e) == DataError:
                    dataErrorCallback(e.args[1])
            except:
                pass

    def query(self, sql, isPrint = False, descriptionList = None):
        '''查询'''
        connectHolder, connect = self.threadGetDatabaseConnect()
        if connect is None: return []
        cursor = None
        try:
            import datetime
            t = datetime.datetime.now()
            cursor = connect.cursor()
            cursor.execute(sql)
            datas = cursor.fetchall()
            connect.commit()  # 解决查询存在缓存问题
            t1 = datetime.datetime.now()
            diff = t1 - t
            if isPrint:
                print('%s\n查询SQL: %s\n数据大小: %d\n时长: %s' % (self.flag, sql, len(datas), str(diff)))
            if descriptionList is not None:
                for des in cursor.description:
                    descriptionList.append(des[0])
            return datas
        except Exception as e:
            traceback.print_exc()
            print('%s 查询错误\nSQL: %s\nERROR: %s' % (self.flag, sql,e ))
        finally:
            try:
                if cursor is not None:
                    cursor.close()
            except:
                pass
            connectHolder.putConnect()
        return []

    def execute(self,sql,dataErrorCallback=None):
        '''执行SQL'''
        connectHolder, connect = self.threadGetDatabaseConnect()
        if connect is None: return -1

        cursor = None
        try:
            cursor = connect.cursor()
            cursor.execute(sql)
            connect.commit()
            return cursor.rowcount
        except Exception as e:
            traceback.print_exc()
            try:
                if connect is not None: connect.rollback()
            except: pass
            print('%s 执行错误\nSQL: %s\nERROR: %s' % (self.flag, sql, e))

            self.dataErrorCallback(e,dataErrorCallback)
        finally:
            try:
                if cursor is not None: cursor.close()
            except: pass
            connectHolder.putConnect()
        return -1

    def execute_transaction(self, sqlList, dataErrorCallback=None):
            '''事务执行SQL'''
            if len(sqlList) == 0 : return -1

            connectHolder, connect = self.threadGetDatabaseConnect()
            if connect is None: return -1

            cursor = None
            try:
                rows = 0
                cursor = connect.cursor()
                for index in range(0,len(sqlList)):
                    sql = sqlList[index]
                    try:
                        cursor.execute(sql)
                        rows += cursor.rowcount
                    except Exception as  e:
                        print('%s 事务执行错误\nINDEX: %d, SQL: %s\nERROR: %s' % (self.flag, index, sql, e))
                        raise e

                connect.commit()
                sqlList.clear()
                return rows
            except Exception as e:
                traceback.print_exc()
                try:
                    if connect is not None: connect.rollback()
                except:
                    pass
                self.dataErrorCallback(e, dataErrorCallback)
            finally:
                try:
                    if cursor is not None: cursor.close()
                except:
                    pass
                connectHolder.putConnect()
            return -1

    def execute_batch(self, sql, paramTupleList, dataErrorCallback=None):
        '''执行SQL'''
        if len(paramTupleList) == 0: return -1
        connectHolder, connect = self.threadGetDatabaseConnect()
        if connect is None: return -1
        cursor = None
        try:
            cursor = connect.cursor()
            cursor.executemany(sql, paramTupleList)
            connect.commit()
            paramTupleList.clear()
            return cursor.rowcount
        except Exception as e:
            import traceback
            traceback.print_exc()
            try:
                if connect is not None: connect.rollback()
            except:pass
            print('%s 批量执行错误\nSQL: %s\n批量条数:%d\nERROR: %s' % (self.flag, sql, len(paramTupleList), e))

            self.dataErrorCallback(e,dataErrorCallback)
        finally:
            try:
                if cursor is not None: cursor.close()
            except: pass
            connectHolder.putConnect()
        return -1

    def __str__(self) -> str:
        return super().__str__() + self.flag





