from vnpy.app.cta_strategy import (
    CtaTemplate,
    StopOrder,
    TickData,
    BarData,
    TradeData,
    OrderData,
    BarGenerator,
    ArrayManager,
)

from vnpy.trader.object import*
from vnpy.app.cta_strategy.cpcta.cpa_business_widget import*
from vnpy.app.cta_strategy.cpcta.cp_constant import *
from vnpy.app.cta_strategy.cpcta.cp_object import*

import threading
import time
import datetime
import re
from multiprocessing import Process
import string

class CpFirstStrategy(CtaTemplate):
    """"""

    author = "LGX"

    #参数
    change_rate = 1.01
    zhisun_ratio1 = 0.7
    zhisun_ratio2 = 1.0
    fudu_ratio1 = 0.4
    fudu_ratio2 = 0.85

    #品种
    varietyCode = str("")
    #虚拟持仓
    virtual_pos = int(0)

    contrData = None
    marketData = None
    #开始业务处理时间
    beginBusinTime = datetime.time(14,59,50)
    endBusinTime = datetime.time(15,0,0)
    todayProcessFlag = False
    preWeekDate=None

    weekLimit = float(0.0)
    weekRevLimit = float(0.0)
    stop_price = float(0.0)
    foldOpenDate = None
    foldOffseDate = None

    max_pos = int(100)

    A11_Flag = False
    A12_Flag = False

    triggedStopFlag=False;
    processLock = threading.Lock()

    parameters = ["change_rate","zhisun_ratio1","zhisun_ratio2","fudu_ratio1","fudu_ratio2","max_pos"]
    variables = ["varietyCode","virtual_pos","A11_Flag","A12_Flag","stop_price","weekLimit"\
        ,"weekRevLimit","foldOpenDate","foldOffseDate"]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super(CpFirstStrategy, self).__init__(cta_engine, strategy_name, vt_symbol, setting)

        #self.bg = BarGenerator(self.on_bar, 60, self.on_60min_bar)
        #self.am = ArrayManager()

        self.my_engine = self.cta_engine.main_engine
        self.businWidget = None

        self.todayProcessFlag = False

    def on_init(self):
        """
        Callback when strategy is inited.
        """ 
        self.write_log("策略初始化")
        #self.load_bar(10)
        self.contrData = self.cta_engine.main_engine.get_contract(self.vt_symbol)
        if self.contrData:
            self.varietyCode = self.contrData.symbol.rstrip(string.digits)
            if not self.varietyCode:
                self.write_log("从合约" + self.vt_symbol + "中分离品种信息失败")

            vnLogger(self.vt_symbol,"合约信息",self.varietyCode,self.contrData,self.contrData.symbol)
        else:       
            self.write_log("查询" + self.vt_symbol + "合约信息失败")
            return

        
        #初始化数据
        self.businWidget = BusinessWidget(ssd.typeFirst.value,self.varietyCode,self.contrData)
        #初始化历史K线(日线与周线)
        self.initHistoryBar()

        self.write_log("保证金参数:"+str(pubConfig.getMarginRatio(self.varietyCode)))
        self.write_log("资金参数:"+str(pubConfig.getFundRatio()))

        self.write_log("指数数据实始化完成")


    def on_start(self):
        """
        Callback when strategy is started.
        """
        self.write_log("策略启动")
        self.timer_process = threading.Timer(1, self.on_timer_process)
        self.timer_process.start()

    def on_stop(self):
        """
        Callback when strategy is stopped.
        """

        if self.timer_process:
            self.timer_process.cancel()

        self.write_log("策略停止")

    def on_tick(self, tick: TickData):
        """
        Callback of new tick data update.
        """
        #self.bg.update_tick(tick)
        self.marketData = tick
        #止损判断
        self.processStopLoss()

    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        #self.bg.update_bar(bar)

    def on_60min_bar(self, bar: BarData):
        """"""
        self.cancel_all()

        #am = self.am
        #am.update_bar(bar)
        #if not am.inited:
            #return

        #self.put_event()
        #pass

    def on_order(self, order: OrderData):
        """
        Callback of new order data update.
        """
        pass

    def on_trade(self, trade: TradeData):
        """
        Callback of new trade data update.
        """

        tipmsg=",".join([trade.symbol,str(trade.direction),str(trade.offset),str(trade.price),str(trade.volume)])
        self.write_log(tipmsg)

        self.put_event()

    def on_stop_order(self, stop_order: StopOrder):
        """
        Callback of stop order update.
        """
        pass

    def datetimeToString(self,dt:datetime):
        if dt:
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        else:
            #vnLogger(self.varietyCode,"datetimeToString",dt)
            return None

    def stringToDatetime(self,strdt:str):
        if strdt:
            #vnLogger(self.varietyCode,"stringToDatetime_1",strdt)
            return datetime.datetime.strptime(strdt, "%Y-%m-%d %H:%M:%S")
        else:
            #vnLogger(self.varietyCode,"stringToDatetime",strdt)
            return None

    def processStopLoss(self):

        if not self.inited:
            return

        if not self.trading:
            return

        if self.pos==0:
            return;

        if self.triggedStopFlag:
            return;

        if self.todayProcessFlag:
            return;

        if not self.varietyCode:
            return;

        if self.marketData is None:
            vnLogger(self.varietyCode,"行情信息为空,processStopLoss")
            return

        if self.contrData is None:
            vnLogger(self.varietyCode,"合约信息为空,processStopLoss")
            return

        tradeflag = self.cta_engine.getContractTradeStatus(self.vt_symbol)
        if not tradeflag:
            vnLogger(self.varietyCode,"当前非连续交易状态",self.vt_symbol)
            return

        self.processLock.acquire()
        try: 
            self.processOffsetWidget("normal",self.contrData.pricetick,self.contrData.size,self.marketData.last_price,True)

        finally:
            self.processLock.release()

    def on_timer_process(self):
        
        self.timer_process = threading.Timer(1, self.on_timer_process)
        self.timer_process.start()

        if not self.inited:
            return

        if not self.trading:
            return

        if ssd.test_cpa.value is "test":
            return
        
        #限定处理时间
        currentime = datetime.datetime.now().time()
        if not (currentime >= self.beginBusinTime and currentime <= self.endBusinTime):
            return
        
        if self.marketData is None:
            vnLogger(self.varietyCode,"行情信息为空")
            return

        if self.contrData is None:
            vnLogger(self.varietyCode,"合约信息为空")
            return

        #判断是否可交易
        tradeflag = self.cta_engine.getContractTradeStatus(self.vt_symbol)
        if not tradeflag:
            #vnLogger(self.varietyCode,"当前非连续交易状态",self.vt_symbol)
            return

        self.processLock.acquire()
        try:

            #处理流程
            if not self.todayProcessFlag:
                #今天已处理标记
                self.todayProcessFlag = True

                bt = datetime.datetime.now()
                self.process()
                et = datetime.datetime.now()
                vnLogger(self.varietyCode,"处理时间测试",str(et - bt))
                self.write_log(self.contrData.symbol+",处理结束")

        finally:
            self.processLock.release()

    def process(self):

        #开始处理前先撤单
        self.cancel_all()

        if self.pos != 0:
            self.businWidget.indicators.setHasPosition(True)
            self.businWidget.indicators.setPosition(self.pos)
            self.businWidget.indicators.buckSingal = 0

        else:
            self.businWidget.indicators.setHasPosition(False)
            self.businWidget.indicators.setPosition(self.pos)
            self.businWidget.newHighFlag = False
            self.businWidget.newLowFlag = False

        #day
        dayrealbar = historyIndex.getDayRealTimeBar(self.varietyCode)
        if not dayrealbar:
            vnLogger(self.varietyCode,"查询实时日线为None,不做后续处理","cpa")
            return 
        #week
        weekrealbar = None
        weekday = dayrealbar.time.weekday()
        if weekday and weekday == 4:
            weekrealbar = historyIndex.getWeekRealTimeBar(self.varietyCode)
            vnLogger(self.varietyCode,"周五查询周线",str(dayrealbar.time))

        vnLogger(self.varietyCode,"---查询实时指数K线---",str(weekrealbar),str(dayrealbar))

        #写入实时指数K线,按日期处理
        self.businWidget.writeLastBarData(dayrealbar,weekrealbar)

        openflag = [False]
        if self.pos != 0:

            last_price = self.marketData.last_price
            self.processOffsetWidget("normal",self.contrData.pricetick,self.contrData.size,last_price,False)

        else:

            self.stop_price = 0.0
            self.A11_Flag = False
            self.A12_Flag = False
            self.weekLimit = 0.0
            self.weekRevLimit = 0.0

            self.processOpenWidget("normal",openflag)

        #判断是否取消标记值
        #self.businWidget.indicators.cancelWeekIndicators()
        self.businWidget.indicators.cancelDayIndicators(openflag[0],self.change_rate)

        self.put_event()
    
    def processOpenWidget(self,processtype:str,openflag:list):

        if openflag and len(openflag) <= 0:
            openflag.append(False)

        openinfo = OpenData()
        
        tick = self.contrData.pricetick
        if tick is None:
            vnLogger(self.varietyCode,"cpa","tick is None")
            return

        pervol = self.contrData.size
        if pervol is None:
            vnLogger(self.varietyCode,"cpa","pervol is None")
            return

        if processtype == "local_init":
            last_price = self.businWidget.indicators.day_am.close[-1]
        else:
            if self.marketData is None:
                vnLogger(self.varietyCode,"cap","没有收到行情")
                return

            last_price = self.marketData.last_price
            if last_price is None or cmp_float(last_price,0.0) <= 0:
                vnLogger(self.varietyCode,"cap","最新价为None或<=0",last_price)
                return

        #临时开仓手数,用于计算可开仓手数
        tempvol = 0

        #A1_2开仓判断
        if self.businWidget.openLongA1_2(tick,pervol,self.zhisun_ratio1,last_price\
            ,self.stringToDatetime(self.foldOffseDate),openinfo):

            realvol = int(min(self.max_pos,openinfo.vol))
            tempvol = realvol

            if realvol > 0 and self.max_pos > 0 and openinfo.vol > 0 and realvol < 500:

                self.A12_Flag = True
                self.weekLimit = openinfo.weekTrendLimitPrice
                self.weekRevLimit = openinfo.weekRvTrendPrice
                self.stop_price = openinfo.stop_price
                self.foldOpenDate = self.datetimeToString(openinfo.foldBeginDate)

                if processtype == "local_init":
                    #测试
                    self.pos = realvol
                else:
                    self.buy(self.marketData.limit_up,realvol)
                    self.write_log(self.contrData.symbol + ",a1_2买入开仓完成," + str(realvol))

                vnLogger(self.varietyCode,"openLongA1_2,买入开仓成功,",str(openinfo),realvol,self.max_pos,last_price,tick,pervol)
                openflag[0] = True

            else:
                vnLogger(self.varietyCode,"openLongA1_2,买入开仓失败,realvol<=0,",str(openinfo),realvol,self.max_pos,last_price,tick,pervol)
                self.write_log(self.contrData.symbol + ",a1_2买入开仓失败," + str(realvol))

        elif self.businWidget.openShortA1_2(tick,pervol,self.zhisun_ratio1,last_price\
            ,self.stringToDatetime(self.foldOffseDate),openinfo):

            realvol = int(min(self.max_pos,openinfo.vol))
            tempvol = realvol

            if realvol > 0 and self.max_pos > 0 and openinfo.vol > 0 and realvol < 500:

                self.A12_Flag = True
                self.weekLimit = openinfo.weekTrendLimitPrice
                self.weekRevLimit = openinfo.weekRvTrendPrice
                self.stop_price = openinfo.stop_price
                self.foldOpenDate = self.datetimeToString(openinfo.foldBeginDate)

                if processtype == "local_init":
                    #测试
                    self.pos = -realvol
                else:
                    self.short(self.marketData.limit_down,realvol)
                    self.write_log(self.contrData.symbol + ",a1_2卖出开仓完成," + str(realvol))

                openflag[0] = True
                vnLogger(self.varietyCode,"openShortA1_2,卖出开仓成功,",str(openinfo),realvol,self.max_pos,last_price,tick,pervol)
                
            else:
                self.write_log(self.contrData.symbol + ",a1_2卖出开仓失败," + str(realvol))

                vnLogger(self.varietyCode,"openShortA1_2,卖出开仓失败,realvol<=0,",str(openinfo),realvol,self.max_pos,last_price,tick,pervol)

        #A1_1开仓判断
        openinfo = OpenData()
        if self.businWidget.openLongA1_1(tick,pervol,last_price,self.zhisun_ratio1\
            ,self.stringToDatetime(self.foldOffseDate),openinfo):

            realvol = int(min(self.max_pos - tempvol,math.fabs(openinfo.vol)))

            if realvol > 0 and openinfo.vol > 0 and self.max_pos > 0 and realvol < 500:

                self.A11_Flag = True
                self.weekLimit = openinfo.weekTrendLimitPrice
                self.weekRevLimit = openinfo.weekRvTrendPrice
                self.stop_price = openinfo.stop_price
                self.foldOpenDate = self.datetimeToString(openinfo.foldBeginDate)

                if processtype == "local_init":
                    #测试
                    self.pos = realvol
                else:
                    self.buy(self.marketData.limit_up,realvol)
                    self.write_log(self.contrData.symbol + ",a1_1买入开仓完成," + str(realvol))

                openflag[0] = True
                vnLogger(self.varietyCode,"openLongA1_1,买入开仓成功",str(openinfo),realvol,self.max_pos,last_price,tick,pervol)

            else:
                vnLogger(self.varietyCode,"openLongA1_1,买入开仓失败,手数<=0,",str(openinfo),realvol,self.max_pos,last_price,tick,pervol)
                self.write_log(self.contrData.symbol + ",a1_1买入开仓失败," + str(realvol))

        elif self.businWidget.openShortA1_1(tick,pervol,last_price,self.zhisun_ratio1,self.fudu_ratio1\
            ,self.stringToDatetime(self.foldOffseDate),openinfo):

            realvol = min(self.max_pos - tempvol,math.fabs(openinfo.vol))

            if realvol > 0 and openinfo.vol > 0 and self.max_pos > 0 and realvol < 500:

                self.A11_Flag = True
                self.weekLimit = openinfo.weekTrendLimitPrice
                self.weekRevLimit = openinfo.weekRvTrendPrice
                self.stop_price = openinfo.stop_price
                self.foldOpenDate = self.datetimeToString(openinfo.foldBeginDate)

                if processtype == "local_init":
                    #测试
                    self.pos = -realvol
                else:
                    self.short(self.marketData.limit_down,realvol)
                    self.write_log(self.contrData.symbol + ",a1_1卖出开仓完成," + str(realvol))

                openflag[0] = True
                vnLogger(self.varietyCode,"openShortA1_1,卖出开仓成功,",self.stop_price,str(openinfo),realvol,self.max_pos,last_price,tick,pervol)  
             
            else:
                self.write_log(self.contrData.symbol + ",a1_1卖出开仓失败," + str(realvol))
                vnLogger(self.varietyCode,"openShortA1_1,买入开仓失败,手数<=0,",str(openinfo),realvol,self.max_pos\
                    ,last_price,tick,pervol)


    def processOffsetWidget(self,processtype:str,tick:float,pervol:int,last_price:float,stopflag:bool):

        """
        平仓判断
        """
        if self.pos > 0:

            if self.businWidget.offsetLong(last_price,self.stop_price,self.weekLimit,self.weekRevLimit,self.fudu_ratio2\
                ,self.stringToDatetime(self.foldOpenDate),processtype,stopflag):

                if stopflag:
                    self.triggedStopFlag=True
                    self.write_log("行情触发止损,"+str(self.pos)+","+str(self.stop_price)+","+str(self.marketData.last_price))
                    vnLogger(self.varietyCode,"行情触发止损,"+str(self.pos)+","+str(self.stop_price)+","+str(self.marketData.last_price))


                #记录平仓折的开始时间
                self.foldOffseDate = self.datetimeToString(self.businWidget.indicators.day_area[-1].initDate)

                if processtype == "local_init":
                    #测试
                    self.pos = 0
                    vnLogger(self.varietyCode,str(self.businWidget.indicators.day_am.dateList[-1]),"开或平条件成立","卖出平仓成功,测试")
                else:
                    #卖平
                    self.sell(self.marketData.limit_down,math.fabs(self.pos))
                    self.write_log(self.contrData.symbol + ",卖出平仓完成," + str(self.pos))

                    vnLogger(self.varietyCode,str(self.businWidget.indicators.day_am.dateList[-1]),"开或平条件成立","卖出平仓条件成立"\
                    ,self.pos,self.marketData.limit_down)

            else:
                if self.A12_Flag and (not self.A11_Flag) and (not stopflag):
                    
                    #加仓判断
                    openinfo = OpenData()
                    if self.businWidget.openLongA1_1(tick,pervol,last_price,self.zhisun_ratio1\
                        ,self.stringToDatetime(self.foldOffseDate),openinfo):

                        self.A11_Flag = True

                        leftvol = self.max_pos - math.fabs(self.pos)
                        realvol = min(leftvol,openinfo.vol)

                        if realvol > 0 and self.max_pos > 0 and leftvol > 0 and realvol < 500:

                            self.weekLimit = openinfo.weekTrendLimitPrice
                            self.weekRevLimit = openinfo.weekRvTrendPrice
                            self.stop_price = openinfo.stop_price
                            self.foldOpenDate = self.datetimeToString(openinfo.foldBeginDate)

                            if processtype == "local_init":

                                self.pos+=realvol

                                vnLogger(self.varietyCode,"openLongA1_1,买入加仓,测试,",str(openinfo),realvol,self.max_pos\
                                   ,last_price,tick,pervol,openinfo.weekRvTrendPrice)
                    
                            else :
                                #买开
                                leftopenvol=self.businWidget.getLeftOpenVol(last_price,pervol)
                                if leftopenvol>0:
                                    realvol=min(realvol,leftopenvol)
                                    self.buy(self.marketData.limit_up,realvol)
                                    self.write_log(self.contrData.symbol + ",a1_1买入加仓完成," + str(realvol))

                                    vnLogger(self.varietyCode,"openLongA1_1,买入加仓,",leftopenvol,str(openinfo),realvol,self.max_pos\
                                        ,last_price,tick,pervol)

                                else:
                                    vnLogger(self.varietyCode,"openLongA1_1,买入加仓,未实际加仓,资金条件不符合,",leftopenvol,str(openinfo),realvol,self.max_pos\
                                            ,last_price,tick,pervol)          
                                
                        else:
                            self.write_log(self.contrData.symbol + ",a1_1买入加仓让失败," + str(realvol))
                            vnLogger(self.varietyCode,"openLongA1_1,买入加仓,加仓条件不成立",realvol)

        elif self.pos < 0:

            if self.businWidget.offsetShort(last_price,self.stop_price,self.weekLimit,self.weekRevLimit,self.fudu_ratio2\
                ,self.stringToDatetime(self.foldOpenDate),processtype,stopflag):

                if stopflag:
                    self.triggedStopFlag=True
                    self.write_log("行情触发止损,"+str(self.pos)+","+str(self.stop_price)+","+str(self.marketData.last_price))
                    vnLogger(self.varietyCode,"行情触发止损,"+str(self.pos)+","+str(self.stop_price)+","+str(self.marketData.last_price))

                #记录平仓折的开始时间
                self.foldOffseDate = self.datetimeToString(self.businWidget.indicators.day_area[-1].initDate)

                if processtype == "local_init":
                    #虚拟
                    self.pos = 0

                    vnLogger(self.varietyCode,str(self.businWidget.indicators.day_am.dateList[-1]),"开或平条件成立","买入平仓条件成立,测试")
                else:
                    #买平
                    self.cover(self.marketData.limit_up,math.fabs(self.pos))
                    self.write_log(self.contrData.symbol + ",买入平仓完成," + str(self.pos))

                    vnLogger(self.varietyCode,str(self.businWidget.indicators.day_am.dateList[-1]),"开或平条件成立","买入平仓条件成立"\
                    ,self.pos,self.marketData.limit_up)
            else:

                if self.A12_Flag and (not self.A11_Flag) and (not stopflag):
                    
                    openinfo = OpenData()
                    if self.businWidget.openShortA1_1(tick,pervol,last_price,self.zhisun_ratio1,self.fudu_ratio1\
                        ,self.stringToDatetime(self.foldOffseDate),openinfo):

                        self.A11_Flag = True

                        leftvol = self.max_pos - math.fabs(self.pos)
                        realvol = min(leftvol,openinfo.vol)

                        if realvol > 0 and openinfo.vol > 0 and leftvol > 0 and realvol < 500:

                            self.weekLimit = openinfo.weekTrendLimitPrice
                            self.weekRevLimit = openinfo.weekRvTrendPrice
                            self.stop_price = openinfo.stop_price
                            self.foldOpenDate = self.datetimeToString(openinfo.foldBeginDate)

                            if processtype == "local_init":

                                self.pos = -realvol

                                vnLogger(self.varietyCode,"openLongA1_1,卖出加仓成功,测试",str(openinfo),realvol,self.max_pos\
                                 ,last_price,tick,pervol)
                            else:
                                #卖开
                                leftopenvol=self.businWidget.getLeftOpenVol(last_price,pervol)
                                if leftopenvol>0:
                                    realvol=min(realvol,leftopenvol)
                                    self.short(self.marketData.limit_down,realvol)
                                    self.write_log(self.contrData.symbol + ",a1_1卖出加仓完成," + str(realvol))

                                    vnLogger(self.varietyCode,"openLongA1_1,卖出加仓成功,",leftopenvol,str(openinfo),realvol,self.max_pos\
                                    ,last_price,tick,pervol)
                                else:
                                    vnLogger(self.varietyCode,"openLongA1_1,卖出加仓,未实际加仓,资金条件不符合,",leftopenvol,str(openinfo),realvol,self.max_pos\
                                            ,last_price,tick,pervol)

                        else:
                            vnLogger(self.varietyCode,"openLongA1_1,卖出加仓失败,realvol<=0,",str(openinfo),realvol,self.max_pos\
                                ,last_price,tick,pervol,self.pos)
                            self.write_log(self.contrData.symbol + ",a1_1卖出加仓失败," + str(realvol))
    
    #取历史K线
    def getHistoryBar(self):
 
        endate = datetime.datetime.now().date()
        begindate = endate - datetime.timedelta(days=365 * 20)
        strenddate = str(endate).replace("-","")
        strbegindate = str(begindate).replace("-","")

        errormsg = []
        daybarlist = historyIndex.getDayHistoryBar(self.varietyCode,strbegindate,strenddate,errormsg)
        
        #week
        weekbarlist = historyIndex.getWeekHistoryBar(self.varietyCode,strbegindate,strenddate,errormsg)

        return daybarlist,weekbarlist

    #初始化历史K线
    def initHistoryBar(self):    
     
        #取所有日线与K线
        daybarlist,weekbarlist = self.getHistoryBar()

        if len(daybarlist) <= 0:
            vnLogger(self.varietyCode,"initHistoryBar,查询日线数据,返回空表")
            self.write_log(self.varietyCode+"查询日线失败,没有数据")
            return

        #初始化虚拟持仓
        self.virtual_pos = 0

        for index,bar in enumerate(daybarlist):

            #虚拟持仓
            if self.pos != 0:
                self.businWidget.indicators.setHasPosition(True)
                self.businWidget.indicators.setPosition(self.pos)
                if self.businWidget.indicators.buckSingal != 0:
                    self.businWidget.indicators.buckSingal = 0
                    vnLogger(self.varietyCode,"取消逆势信号",self.businWidget.indicators.buckSingal)
            else:
                self.businWidget.indicators.setHasPosition(False)
                self.businWidget.indicators.setPosition(self.pos)
                self.businWidget.newHighFlag = False
                self.businWidget.newLowFlag = False

            weekdate = self.businWidget.indicators.getWeekDate(bar.time)
            vnLogger(self.varietyCode,"初始化日线与周线,从日线得到当前的周线",bar.time,weekdate)
    
            weekbar = None
            if weekdate and (weekdate in weekbarlist):

                if self.preWeekDate and weekdate and (weekdate-self.preWeekDate)>datetime.timedelta(days=7):
                    tempdate=self.preWeekDate+datetime.timedelta(days=1)
                    while tempdate<weekdate:

                        tempweekday = tempdate.weekday()
                        if tempweekday==0 and (tempdate in weekbarlist) :#周五需要写入
                            tempweekbar=weekbarlist.pop(tempdate)
                            self.businWidget.writeLastBarData(None,tempweekbar)
                            vnLogger(self.varietyCode,"周线K线数据","上次与本次之前有跳过的周五,需写入",str(tempweekbar))

                        tempdate+=datetime.timedelta(days=1)

                #最新周线
                self.preWeekDate=weekdate

                weekbar = weekbarlist.pop(weekdate)
                vnLogger(self.varietyCode,"初始化日线与周线,查询周线数据,取出并从周线表中删除",str(weekbar),len(weekbarlist))

            #正常情况下日线不为None,周线可能为None
            self.businWidget.writeLastBarData(bar,weekbar)

            openflag = [False]
            #虚拟持仓
            if self.pos != 0:
                last_price = self.businWidget.indicators.day_am.close[-1]
                self.processOffsetWidget("local_init",self.contrData.pricetick,self.contrData.size,last_price,False)

            else:
  
                self.stop_price = 0.0
                self.A11_Flag = False
                self.A12_Flag = False
                self.weekLimit = 0.0
                self.weekRevLimit = 0.0

                self.processOpenWidget("local_init",openflag)

            self.businWidget.indicators.cancelDayIndicators(openflag[0],self.change_rate)

        self.virtual_pos = self.pos
        self.reInitVariables()

        self.write_log(self.varietyCode+"的历史最新K线时间:"+str(daybarlist[-1].time.date()))

        if ssd.test_cpa.value == "test":
            for i, val in enumerate(self.businWidget.indicators.testDayArea):
                vnLogger(self.varietyCode,"日线折",str(val))

        self.put_event()

    def reInitVariables(self):
        self.pos=0
        self.A11_Flag=False
        self.A12_Flag=False
        self.stop_price=0.0
        self.weekLimit=0.0
        self.weekRevLimit=0.0
        self.foldOpenDate=None
        self.foldOffseDate=None