
import math
import copy
import datetime

from vnpy.trader.object import ContractData
from vnpy.app.cta_strategy.cpcta.indicators_widget import* 
from vnpy.app.cta_strategy.cpcta.cp_object import*
from vnpy.app.cta_strategy.cpcta.cp_constant import*
from vnpy.app.cta_strategy.cpcta.config import*

class BusinessWidget:
    
    def __init__(self,iwType:str,variety:str,contr:ContractData):

        #self.contrData = contr
        self.variety = variety

        self.indicators = IndicatorWidget(iwType,self.variety)
        self.vReverseFlag = False
        #判断卖出平仓时的新高条件
        self.newHighFlag = False
        #判断买入平仓时用到的新低条件
        self.newLowFlag = False

    def getDayEma(self):

        dayema = self.indicators.day_am.getLastEma()
        if dayema:
            return dayema.e13,dayema.e34,dayema.e55
        else:
            return None,None,None

    def writeLastBarData(self,lastdaybar:LastBarData,lastweekbar:LastBarData):
        #更新指标数据
        self.indicators.updateLastIndicators(lastdaybar,lastweekbar)

    #A1_1多头开仓
    def openLongA1_1(self,tick:float,pervol:int,last_price:float,zhisun_ratio1:float,preoffsetdate:datetime,openinfo:OpenData):
        
        if self.indicators.weekTrend <= 0:
            #非周线多头
            vnLogger(self.variety,"openLongA1_1,非周多头")
            return False

        preconflag = False
        if self.indicators.week_adjacent_depart.flag == 1 or self.indicators.week_trend_depart.flag == 1:
            if self.indicators.backTag["E275"].flag == 1:
                preconflag = True

                vnLogger(self.variety,"买入开仓,a1_1,背离条件成立",self.indicators.week_adjacent_depart.flag,\
                    self.indicators.week_trend_depart.flag,self.indicators.backTag["E275"].flag)
        else:
            if self.indicators.backTag["E170"].flag == 1 or self.indicators.backTag["E275"].flag == 1:
                preconflag = True
                vnLogger(self.variety,"买入开仓,a1_1,背离条件不成立,满足回踩条件",self.indicators.week_adjacent_depart.flag,\
                    self.indicators.week_trend_depart.flag,self.indicators.backTag["E170"].flag,self.indicators.backTag["E275"].flag)

        if not preconflag:
            #不满足前置条件
            vnLogger(self.variety,"openLongA1_1,买入开仓开仓,前置条件不成立",self.indicators.day_am.dateList[-1],self.indicators.week_adjacent_depart.flag\
            ,self.indicators.week_trend_depart.flag,self.indicators.backTag["E275"].flag,self.indicators.backTag["E170"].flag)
            return False

        dayopen = 0.0 if len(self.indicators.day_am.open) <= 0 else self.indicators.day_am.open[-1]
        dayclose = 0.0 if len(self.indicators.day_am.close) <= 0 else self.indicators.day_am.close[-1]
        if  cmp_float(dayopen,0.0) <= 0 or cmp_float(dayclose,0.0) <= 0 or cmp_float(dayclose,dayopen) <= 0:
            vnLogger(self.variety,"openLongA1_1,买入开仓,非阳线",dayclose,dayopen)
            return False

        e13,e34,e55 = self.getDayEma()
        if e13 is None or cmp_float(dayclose,e13) <= 0:
            vnLogger(self.variety,"openLongA1_1,买入开仓,e13条件不满足",dayclose,e13,e34,e55)
            return False 

        if e34 is None or cmp_float(dayclose,e34) <= 0:
            vnLogger(self.variety,"openLongA1_1,买入开仓,e34条件不满足",dayclose,e13,e34,e55)
            return False
        
        if e55 is None or cmp_float(dayclose,e55) <= 0:
            vnLogger(self.variety,"openLongA1_1,买入开仓,e55条件不满足",dayclose,e13,e34,e55)
            return False
        
        #可开仓
        openinfo.weekRvTrendPrice=self.indicators.weekRvTrendPrice
        openinfo.bs = "buy"
        openinfo.stop_price = self.getStopPice("buy",tick,zhisun_ratio1,last_price)
        openinfo.vol = int(self.getOpenVol(last_price,pervol))
        openinfo.weekTrendLimitPrice = self.indicators.weekTrendLimitPrice
        
        openinfo.foldBeginDate = self.indicators.day_area[-1].initDate

        vnLogger(self.variety,str(self.indicators.day_am.dateList[-1]),"开或平条件成立","a1_1买入开仓条件成立"\
            ,openinfo.weekRvTrendPrice,str(openinfo))

        return True

    #A1_1空头开仓
    def openShortA1_1(self,tick:float,pervol:int,last_price:float,zhisun_ratio1:float,fudu_ratio1:float\
        ,preoffsetdate:datetime,openinfo:OpenData):
        
        if self.indicators.weekTrend >= 0:
            #非周线空头
            vnLogger(self.variety,"openShortA1_1,非周线空头")
            return False

        preconflag = False
        if self.indicators.week_adjacent_depart.flag == -1 or self.indicators.week_trend_depart.flag == -1:
            if self.indicators.backTag["E275"].flag == -1:
                preconflag = True
        else:
            if self.indicators.backTag["E170"].flag == -1 or self.indicators.backTag["E275"].flag == -1:
                preconflag = True

        if not preconflag:
            #不满足前置条件
            vnLogger(self.variety,"openShortA1_1,卖出开仓,前置条件不成立",str(self.indicators.day_am.dateList[-1].date()),self.indicators.week_adjacent_depart.flag\
            ,self.indicators.week_trend_depart.flag,self.indicators.backTag["E275"].flag,self.indicators.backTag["E170"].flag)
            return False

        dayopen = 0.0 if len(self.indicators.day_am.open) <= 0 else self.indicators.day_am.open[-1]
        dayclose = 0.0 if len(self.indicators.day_am.close) <= 0 else self.indicators.day_am.close[-1]
        if cmp_float(dayopen,0.0) <= 0 or cmp_float(dayclose,0.0) <= 0 or cmp_float(dayclose,dayopen) >= 0:

            vnLogger(self.variety,"openShortA1_1,卖出开仓开条件不成立,非阴线",dayopen,dayclose)
            return False

        e13,e34,e55 = self.getDayEma()
        vnLogger(self.variety,"openShortA1_1,测试",e13,e34,e55)
        if e13 is None or cmp_float(dayclose,e13) >= 0:
            return False 

        if e34 is None or cmp_float(dayclose,e34) >= 0:
            return False
        
        if e55 is None or cmp_float(dayclose,e55) >= 0:
            return False

        vnLogger(self.variety,"卖出开仓测试值,a1_1",dayopen,dayclose,e13,e34,e55)

        #判断V反条件
        if not self.vReverseFlag:
            prehigh,prelow = self.getWeekFlodLimit()
            if cmp_float(prehigh,0.0) <= 0 or cmp_float(prelow,0.0) <= 0:
                vnLogger(self.variety,"卖出开仓测试值,周线一折跌幅",prehigh,prelow)
                return False
            
            #dropvalue = math.fabs(prehigh - prelow)
            if cmp_float(prehigh,0.0)>0 and cmp_float(round_to(prelow/prehigh,0.01),1-fudu_ratio1) < 0 \
                and self.indicators.backTag["E170"].flag == -1:
                self.vReverseFlag = True

                vnLogger(self.variety,"v反条件成立,禁止开仓,", str(prehigh) ,str(prelow),str(round_to(prelow/prehigh,0.01))\
                    ,str(1-fudu_ratio1))

                return False 

        self.vReverseFlag = False#不对
        
        #可开仓
        openinfo.bs = "sell"
        openinfo.stop_price = self.getStopPice("sell",tick,zhisun_ratio1,last_price)
        openinfo.vol = int(self.getOpenVol(last_price,pervol))
        openinfo.weekTrendLimitPrice = self.indicators.weekTrendLimitPrice
        openinfo.weekRvTrendPrice = self.indicators.weekRvTrendPrice
        openinfo.foldBeginDate = self.indicators.day_area[-1].initDate

        vnLogger(self.variety,str(self.indicators.day_am.dateList[-1]),"开或平条件成立","openShortA1_1,卖出开仓条件成立",str(openinfo))

        return True

    #A1_2多头开仓条件
    def openLongA1_2(self,tick:float,pervol:int,zhisun_ratio1:float,last_price:float,preoffsetdate:datetime,openinfo:OpenData):
        
        close = self.indicators.day_am.close[-1]
        open = self.indicators.day_am.open[-1]

        if cmp_float(close,open) <= 0:
            vnLogger(self.variety,"openLongA1_2,买入开仓条件不成立,非阳线",close,open)
            return False

        if self.indicators.weekTrend <= 0:
            vnLogger(self.variety,"openLongA1_2,买入开仓条件不成立,非多头趋势",self.indicators.weekTrend)
            return False

        vnLogger(self.variety,"openLongA1_2,买开,逆势测试值",self.indicators.buckSingal,self.indicators.getDayAdjacentDepart())
        canflag = False
        if self.indicators.buckSingal == 1:
            daflag = self.indicators.getDayAdjacentDepart()
            if daflag == -1:
                canflag = True
                vnLogger(self.variety,"openLongA1_2,买开,逆势条件成立,",self.indicators.brokeNeckSignalFlag,daflag)
            else:
                vnLogger(self.variety,"openLongA1_2,买开,逆势但底背离条件不成立,",self.indicators.brokeNeckSignalFlag,daflag)

        else:
            canflag = True

        if not canflag:
            vnLogger(self.variety,"openLongA1_2,买开失败,前提条件不成立",self.indicators.brokeNeckSignalFlag,canflag)
            return False

        if not (cmp_float(close,self.indicators.t3t2FixedPrice)>=0 and cmp_float(self.indicators.t3t2FixedPrice,0.0)>0):
            vnLogger(self.variety,"openShortA1_2,买入开仓条件不成立,未破高点",close,self.indicators.t3t2FixedPrice)
            return False
        '''
        if self.indicators.t321OpenFlag != 1:
            vnLogger(self.variety,"openLongA1_2,价格高低点条件不成立" ,str(self.indicators.t321OpenFlag))
            return False
        '''
        
        openinfo.bs = "buy"
        openinfo.stop_price = self.indicators.t2Price
        openinfo.vol = int(self.getOpenVol(last_price,pervol))
        openinfo.weekTrendLimitPrice = self.indicators.weekTrendLimitPrice
        openinfo.weekRvTrendPrice = self.indicators.weekRvTrendPrice
        openinfo.foldBeginDate = self.indicators.day_area[-1].initDate

        vnLogger(self.variety,str(self.indicators.day_am.dateList[-1]),"开或平条件成立","openLongA1_2,买入开仓条件成立",str(openinfo))

        return True

    #A1_2空头开仓条件
    def openShortA1_2(self,tick:float,pervol:int,zhisun_ratio1:float,last_price:float,preoffsetdate:datetime,openinfo:OpenData):
        
        open = self.indicators.day_am.open[-1]
        close = self.indicators.day_am.close[-1]

        if cmp_float(close,open) >= 0:
            vnLogger(self.variety,"openShortA1_2,卖出开仓条件不成立,非阴线",close,open)
            return False

        if self.indicators.weekTrend >= 0:
            vnLogger(self.variety,"openShortA1_2,卖出开仓条件不成立,非空头趋势",self.indicators.weekTrend)
            return False

        canflag = False

        if self.indicators.buckSingal == -1:
            daflag = self.indicators.getDayAdjacentDepart()
            if daflag == 1:
                canflag = True
                vnLogger(self.variety,"openShortA1_2,卖开,逆势条件成立,",self.indicators.brokeNeckSignalFlag,daflag)
            else:
                vnLogger(self.variety,"openShortA1_2,卖开,逆势条件不成立,",self.indicators.brokeNeckSignalFlag,daflag)
        else:
            canflag = True

        vnLogger(self.variety,"openShortA1_2,卖出开仓条件测试值",close,self.indicators.t3t2FixedPrice)
        if not (cmp_float(close,self.indicators.t3t2FixedPrice)<=0 and cmp_float(self.indicators.t3t2FixedPrice,0.0)>0):
            vnLogger(self.variety,"openShortA1_2,卖出开仓条件不成立,未破低点",close,self.indicators.t3t2FixedPrice)
            return False
            
        if not canflag:
            vnLogger(self.variety,"openShortA1_2,卖开失败,前提条件不成立",self.indicators.brokeNeckSignalFlag,self.indicators.t321OpenFlag\
               ,self.indicators.buckSingal,self.indicators.getDayAdjacentDepart())
            return False
        '''
        if self.indicators.t321OpenFlag != -1:
            vnLogger(self.variety,"openShortA1_2卖出开仓条件不成立,t321OpenFlag不满足",self.indicators.t321OpenFlag)
            return False
        '''
        
        openinfo.bs = "sell"
        openinfo.stop_price = self.indicators.t2Price
        openinfo.vol = int(self.getOpenVol(last_price,pervol))
        openinfo.weekTrendLimitPrice = self.indicators.weekTrendLimitPrice
        openinfo.weekRvTrendPrice = self.indicators.weekRvTrendPrice
        openinfo.foldBeginDate = self.indicators.day_area[-1].initDate
        
        vnLogger(self.variety,str(self.indicators.day_am.dateList[-1]),"开或平条件成立","openShortA1_2,卖出开仓",\
            self.indicators.t321OpenFlag ,self.indicators.buckSingal)

        return True

    def getOpenVol(self,last_price:float,pervol:int):

        fund,ratio = pubConfig.getFundRatio()
        varietyratio = pubConfig.getMarginRatio(self.variety)

        cvalue = last_price * pervol * varietyratio
        if cmp_float(cvalue,0.0) > 0:
           return fund * ratio / (cvalue)

        return 0

    def getLeftOpenVol(self,last_price:float,pervol:int):

        fund,ratio = pubConfig.getFundRatio()
        varietyratio = pubConfig.getMarginRatio(self.variety)
        varietyfund=pubConfig.getVarietyFund()

        singlefund=fund*ratio
        leftvol=0;
        cvalue = last_price * pervol * varietyratio
        vnLogger("test_left_vol,compute addvol",last_price,pervol,varietyratio,cvalue)
        if cmp_float(cvalue,0.0) > 0 and (varietyfund-singlefund)>0:
            leftvol= (varietyfund-singlefund) / (cvalue)
        
        return int(leftvol)

    def getStopPice(self,type:str,tick:float,zhisun_ratio1:float,last_price:float):

        high,low = self.getDayFlodLimit()
        dayclose=self.indicators.day_am.close[-1]

        if type == "buy":
            stopprice = low - 2 * tick
            stopdrop = dayclose - stopprice
            newstop = last_price - stopdrop * zhisun_ratio1

            vnLogger(self.variety,type,"计算止损价格,测试值,买开",low,tick,stopprice,last_price,stopdrop,zhisun_ratio1,newstop,dayclose)

            return newstop

        elif type == "sell":
            stopprice = high + 2 * tick
            stopdrop = stopprice - dayclose
            newstop = last_price + stopdrop * zhisun_ratio1

            vnLogger(self.variety,type,"计算止损价格,测试值,卖开",high,tick,stopprice,last_price,stopdrop,zhisun_ratio1,newstop,dayclose)
            return newstop
        else:
            return 0.0
       
    def getWeekFlodLimit(self):
        
        high = float(0.0)
        low = float(0.0)

        if len(self.indicators.week_area) >= 2:

            firstarea = self.indicators.week_area[-1]
            secondarea = self.indicators.week_area[-2]
            if firstarea.type == "red":
                high = firstarea.highPrice
            elif firstarea.type == "green":
                low = firstarea.lowPrice

            if secondarea.type == "red":
                high = secondarea.highPrice
            elif secondarea.type == "green":
                low = secondarea.lowPrice

        return high,low

    def getDayFlodLimit(self):
        
        high = float(0.0)
        low = float(0.0)

        if self.indicators.getDayAreaNum() >= 2:

            firstarea = self.indicators.day_area[-1]
            secondarea = self.indicators.day_area[-2]
            if firstarea.type == "red":
                high = firstarea.highPrice
            elif firstarea.type == "green":
                low = firstarea.lowPrice

            if secondarea.type == "red":
                high = secondarea.highPrice
            elif secondarea.type == "green":
                low = secondarea.lowPrice

        return high,low

    def getDaySubFlodLimit(self):
        
        high = float(0.0)
        low = float(0.0)

        if self.indicators.getDayAreaNum() >= 4:

            firstarea = self.indicators.day_area[-3]
            secondarea = self.indicators.day_area[-4]
            if firstarea.type == "red":
                high = firstarea.highPrice
            elif firstarea.type == "green":
                low = firstarea.lowPrice

            if secondarea.type == "red":
                high = secondarea.highPrice
            elif secondarea.type == "green":
                low = secondarea.lowPrice

        return high,low

    #卖出平仓
    def offsetLong(self,last_price:float,stopprice:float,weeklimitprice:float,reverseweeklimitprice:float,fudu_ratio2:float\
        ,openfoldDate:datetime,processtype:str,stopflag:bool):
  
        if processtype == "local_init":
            last_price = self.indicators.day_am.low[-1]

        if cmp_float(last_price,0.0)<=0:
            vnLogger(self.variety,"卖出平仓条件不成立,最新价<=0,",last_price)
            return False

        if cmp_float(last_price,stopprice) < 0 and cmp_float(stopprice,0.0) > 0:
            vnLogger(self.variety,"卖出平仓条件成立,止损平仓,",last_price,stopprice)
            return True

        if stopflag:
            return False;

        timeflag = False
        lastarea = self.indicators.day_area[-1]
        if lastarea and openfoldDate and lastarea.initDate and lastarea.initDate > openfoldDate and cmp_float(self.indicators.day_am.hist[-1],0.0) < 0:
            timeflag = True
            vnLogger(self.variety,"卖出平仓时间测试值",lastarea.type,lastarea.initDate,openfoldDate)

        if self.indicators.PreWeekTrend == 1 and self.indicators.weekTrend == -1 and timeflag:
            vnLogger(self.variety,"卖出平仓条件成立,周趋从多转为空,",self.indicators.PreWeekTrend,self.indicators.weekTrend)
            return True
        
        if self.indicators.weekTrend <= 0:
            #周线不是多头趋势跳过,不处理
            vnLogger(self.variety,"卖出平仓条件不成立,当前趋势不是周线多头",self.indicators.weekTrend)
            return False
        
        dayhigh = 0.0 if len(self.indicators.day_am.high) <= 0 else self.indicators.day_am.high[-1]
        daylow = 0.0 if len(self.indicators.day_am.low) <= 0 else self.indicators.day_am.low[-1]
        dayclose = 0.0 if len(self.indicators.day_am.close) <= 0 else self.indicators.day_am.close[-1]
        dayopen = 0.0 if len(self.indicators.day_am.open) <= 0 else self.indicators.day_am.open[-1]

        if cmp_float(dayhigh,0.0) <= 0 or cmp_float(dayclose,0.0) <= 0:
            vnLogger(self.variety,"判断卖出平仓时,最高或收盘价<=0," + str(dayhigh) + "," + str(dayclose))
            return False

        e13,e34,e55 = self.getDayEma()
        if e13 is None or e34 is None or e55 is None:
            vnLogger(self.variety,"判断卖出平仓时,,e13,e34,e55,其中有值为空")
            return False

        #日线低点>周线的高点
        if cmp_float(daylow,weeklimitprice) > 0:
            self.newHighFlag = True
            vnLogger(self.variety,"卖出平仓时确认新高",daylow,weeklimitprice)

        if not self.newHighFlag:

            dyflag = self.indicators.getDayAdjacentDepart()
            vnLogger(self.variety,"卖出平仓条件测试值,未创新高",dayhigh,daylow,dayclose,weeklimitprice,reverseweeklimitprice,dyflag)
            if dyflag == 1 and self.indicators.tempDayIsHistSwitch == -1 and timeflag and lastarea.num > 2:
                vnLogger(self.variety,"卖出平仓条件成立,周线未创新高,相邻顶背离确认,",dyflag)
                return True

            breaksignal=self.indicators.getBreakSingal(dayhigh,daylow,dayclose,dayopen,"offset")
            if breaksignal == -1 and self.indicators.day_area[-1].type == "red" and timeflag:
                vnLogger(self.variety,"卖出平仓条件成立,周线未创新高,反正反破颈条件成立(向下),",self.indicators.brokeNeckSignalFlag)
                return True

            #（当前日线折的高点 - 周线低点）/（周线开仓时的低点到开仓时的高点 - 周线低点）
            if cmp_float(math.fabs(weeklimitprice - reverseweeklimitprice),0.0) > 0:
                foldhigh,foldlow = self.getDayFlodLimit()
                subfoldhigh,subfoldlow = self.getDaySubFlodLimit()

                ampratio = math.fabs(foldhigh - reverseweeklimitprice) / math.fabs(weeklimitprice - reverseweeklimitprice)
                interval = self.getOPenSerialNum(openfoldDate)

                vnLogger(self.variety,"卖出平仓条件测试值,未创新高 幅度测试,",dayhigh,dayclose,weeklimitprice,reverseweeklimitprice\
                        ,foldhigh,foldlow,subfoldhigh,subfoldlow,ampratio,fudu_ratio2,e13,e34,e55)
                
                if cmp_float(ampratio,fudu_ratio2) > 0 and cmp_float(foldhigh,subfoldhigh) > 0 \
                    and cmp_float(dayclose,min(e13,e34,e55)) < 0 and interval >= 4 and timeflag: 

                    vnLogger(self.variety,"卖出平仓条件成立,周线未创新高,涨幅条件成立,",dayhigh,dayclose,weeklimitprice,reverseweeklimitprice\
                        ,foldhigh,foldlow,subfoldhigh,subfoldlow,ampratio,fudu_ratio2,e13,e34,e55)
                    return True
        else:
            #新高,日线的高点<周线的最低点
            interval = self.getOPenSerialNum(openfoldDate)
            vnLogger(self.variety,"2折条件测试,卖平",openfoldDate,interval)#self.indicators..getDayAreaNum() >= 4 and 
            if self.indicators.tempDayIsHistSwitch == -1 and interval >= 3 and timeflag:
                vnLogger(self.variety,"卖出平仓条件成立,日线2折平仓条件成立",interval)
                return True

            if cmp_float(dayclose,min(e13,e34,e55)) < 0:
                vnLogger(self.variety,"卖出平仓条件成立,日线不足2折,收盘价条件成立,小于条件",dayclose,e13,e34,e55)
                return True

        return False

    #平多头的时候是绿柱,平空时是红柱
    #买入平仓,weeklimitprice=开仓时的低点,reverseweeklimitprice=开仓时到当前的高点
    def offsetShort(self,last_price:float,stopprice:float,weeklimitprice:float,reverseweeklimitprice:float,fudu_ratio2:float\
        ,openfoldDate:datetime,processtype:str,stopflag:bool):

        if processtype == "local_init":
            last_price = self.indicators.day_am.high[-1]

        if cmp_float(last_price,0.0)<=0:
            vnLogger(self.variety,"买入平仓条件不成立,最新价<=0,",last_price)
            return False

        if cmp_float(last_price,stopprice) > 0 and cmp_float(stopprice,0.0) > 0:
            vnLogger(self.variety,"买入平仓条件成立,止损平仓,",last_price,stopprice)
            return True

        if stopflag:
            return False;

        timeflag = False
        lastarea = self.indicators.day_area[-1]
        if lastarea.initDate and lastarea and openfoldDate and lastarea.initDate > openfoldDate \
            and cmp_float(self.indicators.day_am.hist[-1],0.0) > 0:
            timeflag = True
            vnLogger(self.variety,"买入平仓时间测试值",lastarea.type,lastarea.initDate,openfoldDate)

        if self.indicators.PreWeekTrend == -1 and self.indicators.weekTrend == 1 and timeflag:
            vnLogger(self.variety,"买入平仓条件成立,周趋从空转为多,",self.indicators.PreWeekTrend,self.indicators.weekTrend)
            return True
        
        if self.indicators.weekTrend >= 0:
            #周线不是空头趋势跳过,不处理
            return False
        
        dayhigh = 0.0 if len(self.indicators.day_am.high) <= 0 else self.indicators.day_am.high[-1]
        daylow = 0.0 if len(self.indicators.day_am.low) <= 0 else self.indicators.day_am.low[-1]
        dayclose = 0.0 if len(self.indicators.day_am.close) <= 0 else self.indicators.day_am.close[-1]
        dayopen = 0.0 if len(self.indicators.day_am.open) <= 0 else self.indicators.day_am.open[-1]

        if cmp_float(daylow,0.0) <= 0 or cmp_float(dayclose,0.0) <= 0:
            vnLogger(self.variety,"判断买入平仓时,最低价或收盘价<=0," + str(daylow) + "," + str(dayclose))
            return False

        e13,e34,e55 = self.getDayEma()
        if e13 is None or e34 is None or e55 is None:
            vnLogger(self.variety,"判断买入平仓时,,e13,e34,e55,其中有值为空")
            return False

        #日线的高点<周线的最低点
        if cmp_float(dayhigh,weeklimitprice) < 0:
            self.newLowFlag = True
            vnLogger(self.variety,"买入平仓时确认新高",dayhigh,weeklimitprice)

        #新低,日线的低点>周线的最高点
        if not self.newLowFlag:#未新低

            dyflag = self.indicators.getDayAdjacentDepart()
            if dyflag == -1 and self.indicators.tempDayIsHistSwitch == 1 and timeflag and lastarea.num > 2:
                vnLogger(self.variety,"买入平仓条件成立,周线未创新低,相邻底背离确认,",dyflag)
                return True

            vnLogger(self.variety,"买入平仓条件,反正反测试值",timeflag)
            breaksignal=self.indicators.getBreakSingal(dayhigh,daylow,dayclose,dayopen,"offset")
            if  breaksignal== 1 and self.indicators.day_area[-1].type == "green" and timeflag:
                vnLogger(self.variety,"买入平仓条件成立,周线未创新低,反正反破颈条件成立(向上),",self.indicators.brokeNeckSignalFlag)
                return True

            #（周线的高点 - 当前日线折的低点）/（周线高点 - 周线开仓时的高点到开仓时的低点）,此条件待测
            if cmp_float(math.fabs(reverseweeklimitprice - weeklimitprice),0.0) > 0:
                foldhigh,foldlow = self.getDayFlodLimit()
                subfoldhigh,subfoldlow = self.getDaySubFlodLimit()
                #if cmp_float(reverseweeklimitprice-foldlow,0.0)>0:#需确认

                ampratio = math.fabs(reverseweeklimitprice - foldlow) / math.fabs(reverseweeklimitprice - weeklimitprice)
                interval = self.getOPenSerialNum(openfoldDate)

                vnLogger(self.variety,"买入平仓条件测试值",daylow,dayclose,weeklimitprice,reverseweeklimitprice\
                        ,foldhigh,foldlow,subfoldhigh,subfoldlow,ampratio,fudu_ratio2,e13,e34,e55,interval,timeflag)

                if cmp_float(ampratio,fudu_ratio2) > 0 and cmp_float(foldlow,subfoldlow) < 0 \
                    and cmp_float(dayclose,max(e13,e34,e55)) > 0 and interval >= 4 and timeflag:

                    vnLogger(self.variety,"买入平仓条件成立,周线未创新低,跌幅条件成立,",daylow,dayclose,weeklimitprice,reverseweeklimitprice\
                        ,foldhigh,foldlow,ampratio,fudu_ratio2,e13,e34,e55,interval)
                    return True

        #新高
        else:
            interval = self.getOPenSerialNum(openfoldDate)
            vnLogger(self.variety,"2折条件测试,买平",openfoldDate,interval)#self.indicators..getDayAreaNum() >= 4 and
            if  self.indicators.tempDayIsHistSwitch == 1 and interval >= 3 and timeflag:
                vnLogger(self.variety,"买入平仓条件成立,日线2折平仓条件成立",interval)
                return True

            if cmp_float(dayclose,max(e13,e34,e55)) > 0:
                vnLogger(self.variety,"买入平仓条件成立,日线不足2折,收盘价条件成立,大于条件",dayclose,e13,e34,e55)
                return True

        return False

    def getOPenSerialNum(self,opendate:datetime):

        if not self.indicators.day_area:
            return 0
        if not opendate:
            return 0

        cnum = 0
        isexist=False
        for val in reversed(self.indicators.day_area):
             if val.initDate and opendate and val.initDate >= opendate and val.type!="":
                cnum +=1
                #vnLogger(self.variety,"cnum",cnum)

                if val.initDate == opendate:
                     isexist=True

        if cnum>0 and (not isexist):
            cnum+=1

        return cnum
