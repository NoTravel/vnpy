import datetime
from vnpy.app.cta_strategy.cpcta.bar_manager import* 
from vnpy.app.cta_strategy.cpcta.cp_object import*
from vnpy.app.cta_strategy.cpcta.cp_constant import*
import copy

#计算数据
class IndicatorWidget:

    def __init__(self,iwtype:str,variety:str):

        self.iwType = iwtype
        self.variety = variety

        #week
        self.week_am = BarManager("week",self.variety)

        #macd片区
        self.week_area = [MacdArea()] * 5
        #相邻背离,top=顶背离,bottom=底背离
        self.week_adjacent_depart = DepartData()
        self.week_trend_depart = DepartData()
        #周趋势,趋势只有1与-1,1=long,-1=short
        self.weekTrend = int(0)
        self.PreWeekTrend = int(0)
        #周趋势次高片区
        self.weekLimitFlag = False
        self.weekSwitchFlag = False
        self.weekNewHighFlag = False
        self.week_pre_limit_area = MacdArea()
        #是否有仓标记
        self.hasPosition = False
        #趋势新高,用在日线回踩E275判断
        self.trendNewLimit = float(0.0)
        self.trendNewLimitFlag = False
        #周趋极值和极值确定时的反向极值
        self.weekTrendLimitPrice = float(0.0)
        self.weekRvTrendPrice = float(0.0)
        self.weekTrendLimitFlag = float(0)

        #day
        self.day_am = BarManager("day",self.variety)
        #回踩标记
        self.backTag = {"E13":BackTagData(),"E34":BackTagData(),"E55":BackTagData(),"E170":BackTagData(),"E275":BackTagData()}
        #macd片区
        self.day_area = [MacdArea()] * 10
        #日线趋势
        self.dayTrend = int(0)
        self.dayLimitPrice = float(0.0)
        #日线背离
        self.dayTrendDepart = int(0)
        self.dayPreLimitPrice = float(0.0)
        self.dayPreLimitArea = MacdArea()
        self.dayNewHighFlag = False
        self.dayLimitFlag = False
        self.daySwitchFlag = False

        #破颈
        self.brokeNeckSignalFlag = float(0)
        #逆势信号
        self.buckSingal = float(0)
        self.newE275BackFlag = False
        
        #日线趋势高低点
        self.dayTrendLimitPrice = float(0.0)
        self.dayTrendLimitFlag = False

        #A1_2
        self.t1Flag = False
        self.t3Flag = False
        self.t2Price = float(0.0)
        self.t3t2HighPrice = float(0.0)
        self.preChangeLimitPrice=float(0.0)
        self.t321OpenFlag = int(0)#1:开多,-1:开空,0不做操作
        self.t3t2FixedPrice=float(0.0)

        #A3,需要通过接口初始化
        self.pos = int(0)
        self.posNewLimitPrice = float(0.0)
        self.posMacPrice1 = float(0.0)
        self.posMacPrice2 = float(0.0)

        #temp week var
        self.tempWeekPreInit = False
        self.tempWeekPreHist = float(0.0)
        self.tempWeekAreaInitFlag = False
        self.tempWeekCurrentArea = MacdArea()
        #红绿柱切换标志
        self.tempWeekIsHistSwitch = int(0)

        #temp day var
        #self.tempDayPreInit=False
        self.tempDayPreHist = float(0.0)
        #self.tempDayAreaInitFlag=False
        self.tempDayCurrentArea = None
        #红绿柱切换标志
        self.tempDayIsHistSwitch = int(0)
        #日线片区实始化
        self.dayAreaIntFlag = False

        self.testDayArea={}

    def setPosInfo(self,pos:int,prelimit:float,mac1:float,mac2:float):
        self.pos = pos
        self.prelimit = prelimit
        self.posMacPrice1 = mac1
        self.posMacPrice2 = mac2

    def setHasPosition(self,flag):
        self.hasPosition = flag

    def setPosition(self,position:int):
        self.pos = position

    def getLastFoldData(self):
        if self.getDayAreaNum() <= 0:
            return 0.0,0.0

        lastarea = self.day_area[-1]
        secarea = self.day_area[-2]

        high = 0.0
        low = 0.0
        if lastarea.type == "red":
            high = lastarea.highPrice
        elif lastarea.type == "green":
            low = lastarea.lowPrice

        if secarea.type == "red":
            high = secarea.highPrice
        elif secarea.type == "green":
            low = secarea.lowPrice

        return high,low

    #周线指标数据,
    def initWeekIndicators(self,srctype:str):

        ziplist = self.week_am.getLastWeekZipList()
        if not ziplist:
            vnLogger(self.variety,"initWeekIndicators,最新的周线数据是空值,不需要更新")
            return

        for index, begindate,e13,e34,e55 ,hist,dea,close,high,low in ziplist:  
           
            if ssd.test_cpa.value == "test":
                vnLogger(self.variety,"周线K线数据",index,begindate,e13,e34,e55,hist,dea,close,high,low)

            #新的周线来了,判断周线趋势
            self.PreWeekTrend = self.weekTrend

            if cmp_float(self.trendNewLimit,0.0) == 1:
                if self.weekTrend == 1 and cmp_float(self.trendNewLimit,high) == 1:
                    self.trendNewLimitFlag = True
                    self.trendNewLimit = high
                    vnLogger(self.variety,"周趋势多,创新高",begindate,self.trendNewLimit)

                elif self.weekTrend == -1 and cmp_float(self.trendNewLimit,low) == -1:
                    self.trendNewLimitFlag = True
                    self.trendNewLimit = low
                    vnLogger(self.variety,"周趋势空,创新低",begindate,self.trendNewLimit)
            
            if self.PreWeekTrend == 1 and self.weekTrend == 1:
                #趋势为多
                if cmp_float(high,self.weekTrendLimitPrice) > 0:
                    #新高时更新最高价与最低价
                    self.weekTrendLimitPrice = high
                    self.weekRvTrendPrice = low
                    self.weekTrendLimitFlag = 1

                    self.cancelWeekE275BackTag()

                    vnLogger(self.variety,"周趋势","周趋势为多,更新周趋势最高价,重新初始化最低价,取消e275回踩",begindate,self.weekTrendLimitPrice\
                        ,self.weekRvTrendPrice,high,low,self.weekTrendLimitFlag)

                else:
                    self.weekRvTrendPrice = min(self.weekRvTrendPrice,low)
                    vnLogger(self.variety,"周趋势","周趋势为多,不需要更新最高价,更新最低价",begindate,self.weekTrendLimitPrice\
                        ,self.weekRvTrendPrice,high,low,self.weekTrendLimitFlag)

            elif self.PreWeekTrend == -1 and self.weekTrend == -1:
                #趋势为空
                if cmp_float(low,self.weekTrendLimitPrice) < 0:
                    #新高时更新最高价与最低价
                    self.weekTrendLimitPrice = low
                    self.weekRvTrendPrice = high
                    self.weekTrendLimitFlag = -1

                    self.cancelWeekE275BackTag()

                    vnLogger(self.variety,"周趋势","周趋势为空,更新周趋势最低价,重新初始化最高价,取消e275回踩",begindate,self.weekTrendLimitPrice\
                        ,self.weekRvTrendPrice,high,low,self.weekTrendLimitFlag)

                else:
                    self.weekRvTrendPrice = max(self.weekRvTrendPrice,high)
                    vnLogger(self.variety,"周趋势","周趋势为空,不需要更新最低价,更新最高价",begindate,self.weekTrendLimitPrice\
                        ,self.weekRvTrendPrice,high,low,self.weekTrendLimitFlag)

            #趋势方向,1=多,-1=空,0=no
            if self.PreWeekTrend == 1:
                if cmp_float(e13,min(e34,e55)) == -1 and cmp_float(close,min(e13,e34,e55)) == -1:
                    self.weekTrend = -1
                    self.trendNewLimit = low
                    self.trendNewLimitFlag = False

                    self.weekTrendLimitPrice = low
                    self.weekRvTrendPrice = high
                    self.weekTrendLimitFlag = 0

                    vnLogger(self.variety,"周趋势","周趋势从多变为空,初始化新低,",begindate,self.trendNewLimit,self.weekTrendLimitPrice,self.weekRvTrendPrice,self.weekTrendLimitFlag)

            elif self.PreWeekTrend == -1:
                if cmp_float(e13,max(e34,e55)) == 1 and cmp_float(close,max(e13,e34,e55)) == 1:
                    self.weekTrend = 1
                    self.trendNewLimit = high
                    self.trendNewLimitFlag = False

                    self.weekTrendLimitPrice = high
                    self.weekRvTrendPrice = low
                    self.weekTrendLimitFlag = 0

                    vnLogger(self.variety,"周趋势","周趋势从空变为多,初始化新高,",begindate,self.trendNewLimit,self.weekTrendLimitPrice,self.weekRvTrendPrice,self.weekTrendLimitFlag)

            elif self.PreWeekTrend == 0:
                if cmp_float(e13,max(e34,e55)) == 1 and cmp_float(close,max(e13,e34,e55)) == 1:
                    self.weekTrend = 1
                    self.trendNewLimit = high
                    self.trendNewLimitFlag = False

                    self.weekTrendLimitPrice = high
                    self.weekRvTrendPrice = low
                    self.weekTrendLimitFlag = 0

                    vnLogger(self.variety,"周趋势","周趋势从0变为前多,初始化新高,",begindate,self.trendNewLimit,self.weekTrendLimitPrice,self.weekRvTrendPrice,self.weekTrendLimitFlag)

                elif cmp_float(e13,min(e34,e55)) == -1 and cmp_float(close,min(e13,e34,e55)) == -1:
                    self.weekTrend = -1
                    self.trendNewLimit = low
                    self.trendNewLimitFlag = False

                    self.weekTrendLimitPrice = low
                    self.weekRvTrendPrice = high
                    self.weekTrendLimitFlag = 0

                    vnLogger(self.variety,"周趋势","周趋势从0变为空,初始化新低,",begindate,self.trendNewLimit,self.weekTrendLimitPrice,self.weekRvTrendPrice,self.weekTrendLimitFlag)

                else:
                    self.weekTrend = 0

            #处理周趋势改变需要清理的数据
            self.cancelWeekIndicators()

            tempinitflag = self.tempWeekPreInit
            if not tempinitflag and cmp_float(hist,0.0) != 0:
                self.tempWeekPreHist = hist
                self.tempWeekPreInit = True
            else:
                #确定片区
                if  not self.tempWeekAreaInitFlag:
                    if cmp_float(hist,0.0) == -1 or cmp_float(hist,0.0) == 1:
                        self.tempWeekAreaInitFlag = True
                        pass

                if self.tempWeekAreaInitFlag:

                        if cmp_float(self.tempWeekPreHist,0.0) == 1 and cmp_float(hist,0.0) == 1 and self.tempWeekCurrentArea.type == "red":
                            self.tempWeekCurrentArea.barPrice = max(self.tempWeekCurrentArea.barPrice,close)
                            self.tempWeekCurrentArea.yellowPrice = max(self.tempWeekCurrentArea.yellowPrice,dea)
                            self.tempWeekCurrentArea.area = self.tempWeekCurrentArea.area + math.fabs(hist)
                            self.tempWeekCurrentArea.highPrice = max(self.tempWeekCurrentArea.highPrice,high)
                            self.tempWeekCurrentArea.lowPrice = min(self.tempWeekCurrentArea.lowPrice,low)

                            self.tempWeekIsHistSwitch = 0

                            pass
                        elif cmp_float(self.tempWeekPreHist,0.0) == -1 and cmp_float(hist,0.0) == -1 and self.tempWeekCurrentArea.type == "green":
                            self.tempWeekCurrentArea.barPrice = min(self.tempWeekCurrentArea.barPrice,close)
                            self.tempWeekCurrentArea.yellowPrice = min(self.tempWeekCurrentArea.yellowPrice,dea)
                            self.tempWeekCurrentArea.area = self.tempWeekCurrentArea.area +  math.fabs(hist)
                            self.tempWeekCurrentArea.highPrice = max(self.tempWeekCurrentArea.highPrice,high)
                            self.tempWeekCurrentArea.lowPrice = min(self.tempWeekCurrentArea.lowPrice,low)

                            self.tempWeekIsHistSwitch = 0

                            pass
                        elif cmp_float(self.tempWeekPreHist,0.0) == -1 and cmp_float(hist,0.0) == 1:
                        
                            self.week_area[:-1] = self.week_area[1:]
                            self.week_area[-1] = copy.deepcopy(self.tempWeekCurrentArea)

                            self.tempWeekCurrentArea = MacdArea()
                            self.tempWeekCurrentArea.type = "red"
                            self.tempWeekCurrentArea.beginIndex = index
                            self.tempWeekCurrentArea.barPrice = close
                            self.tempWeekCurrentArea.yellowPrice = dea
                            self.tempWeekCurrentArea.area =  math.fabs(hist)
                            self.tempWeekCurrentArea.highPrice = high
                            self.tempWeekCurrentArea.lowPrice = low
                            self.tempWeekCurrentArea.initDate = begindate

                            self.tempWeekIsHistSwitch = 1

                            pass
                        elif cmp_float(self.tempWeekPreHist,0.0) == 1 and cmp_float(hist,0.0) == -1:

                            self.week_area[:-1] = self.week_area[1:]
                            self.week_area[-1] = copy.deepcopy(self.tempWeekCurrentArea)

                            self.tempWeekCurrentArea = MacdArea()
                            self.tempWeekCurrentArea.type = "green"
                            self.tempWeekCurrentArea.beginIndex = index
                            self.tempWeekCurrentArea.barPrice = close
                            self.tempWeekCurrentArea.yellowPrice = dea
                            self.tempWeekCurrentArea.area =  math.fabs(hist)
                            self.tempWeekCurrentArea.highPrice = high
                            self.tempWeekCurrentArea.lowPrice = low
                            self.tempWeekCurrentArea.initDate = begindate

                            self.tempWeekIsHistSwitch = -1

                            pass

                        self.tempWeekPreHist = hist
                pass

            #背离判断
            if self.weekTrend == -1:
                ctarea = self.week_area[-1]
                subarea = self.week_area[-3]
                if ctarea and subarea and cmp_float(ctarea.lowPrice,subarea.lowPrice) < 0 and cmp_float(ctarea.yellowPrice,subarea.yellowPrice) > 0\
                   and ctarea.type == "green" and self.tempWeekIsHistSwitch==1:

                    self.week_adjacent_depart.set(-1,high,low)#相邻底背离
                    vnLogger(self.variety,"周背离","相邻底背离确认",begindate,ctarea.lowPrice,subarea.lowPrice,ctarea.yellowPrice,subarea.yellowPrice)
                    
            elif self.weekTrend == 1:
                ctarea = self.week_area[-1]
                subarea = self.week_area[-3]
                if ctarea and subarea and cmp_float(ctarea.highPrice,subarea.highPrice) > 0 and cmp_float(ctarea.yellowPrice,subarea.yellowPrice) < 0 \
                    and ctarea.type == "red" and self.tempWeekIsHistSwitch==-1:

                    self.week_adjacent_depart.set(1,high,low)#相邻顶背离
                    vnLogger(self.variety,"周背离","相邻顶背离确认",begindate,ctarea.lowPrice,subarea.lowPrice,ctarea.yellowPrice,subarea.yellowPrice)

            #趋势转换后重新初始化
            if ((self.PreWeekTrend == 0 or self.PreWeekTrend == -1) and self.weekTrend == 1) or (self.PreWeekTrend == 1 and self.weekTrend == -1) or ((self.PreWeekTrend == 0 or self.PreWeekTrend == 1) and self.weekTrend == -1) or (self.PreWeekTrend == -1 and self.weekTrend == 1):
               
                self.week_pre_limit_area = MacdArea()
                self.weekNewHighFlag = False
                self.weekLimitFlag = False
                self.weekSwitchFlag = False
                self.week_trend_depart.reInit()

                vnLogger(self.variety,"周趋势背离","趋势转换,初始化",str(begindate.date()),self.PreWeekTrend,self.weekTrend)

            elif self.PreWeekTrend == 1 and self.weekTrend == 1:
                if not self.weekSwitchFlag:

                    if self.tempWeekIsHistSwitch==-1:
                        if self.weekLimitFlag:
                            self.weekSwitchFlag = True
                            pass
                        else:
                            #确定次高点
                            self.weekLimitFlag = True
                            self.week_pre_limit_area = copy.deepcopy(self.week_area[-1])
                            pass

                if self.weekSwitchFlag:
                    #macd切换且出现新高
                    limitarea = self.week_area[-1]
                    prearea = self.week_pre_limit_area
                    if cmp_float(limitarea.highPrice,prearea.highPrice) == 1:
                        self.weekNewHighFlag = True
                        pass

                    #新高后继续切换
                    if self.tempWeekIsHistSwitch==-1 and self.weekNewHighFlag and self.weekLimitFlag:
                        #判断是否趋势高低点背离
                        

                        if cmp_float(limitarea.yellowPrice,prearea.yellowPrice) == -1 and limitarea.type == "red":
                           if cmp_float(limitarea.area,self.week_area[-3].area) == -1:
                                self.week_trend_depart.set(1,high,low) #趋势顶背离
                                vnLogger(self.variety,"周趋势背离","顶背离_1",str(begindate.date()))
                           else:
                                if self.getWeekAreaNum() >= 5:
                                    t1 = self.week_area[-3]
                                    t2 = self.week_area[-5]
                                    tsum = t1.area + t2.area
                                    if cmp_float(limitarea.area,tsum) == -1:
                                        self.week_trend_depart.set(1,high,low)#趋势底背离
                                        vnLogger(self.variety,"周趋势背离","顶背离_2",str(begindate.date()))

                        self.week_pre_limit_area = copy.deepcopy(self.week_area[-1])
                        self.weekNewHighFlag = False
                        self.weekSwitchFlag = False
                        pass

            elif self.PreWeekTrend == -1 and self.weekTrend == -1:
                if not self.weekSwitchFlag:

                    if self.tempWeekIsHistSwitch==1:
                        if self.weekLimitFlag:
                            self.weekSwitchFlag = True
                            pass
                        else:
                            #确定次高点
                            self.weekLimitFlag = True
                            self.week_pre_limit_area = copy.deepcopy(self.week_area[-1])
                            pass

                if self.weekSwitchFlag:
                    #macd切换且出现新低
                    limitarea = self.week_area[-1]
                    prearea = self.week_pre_limit_area

                    if cmp_float(limitarea.lowPrice,prearea.lowPrice) <0:
                        self.weekNewHighFlag = True

                    #新低后继续切换
                    if self.tempWeekIsHistSwitch==1 and self.weekNewHighFlag and self.weekLimitFlag:
                        #判断是否趋势高低点背离

                        if cmp_float(limitarea.yellowPrice,prearea.yellowPrice) == 1 and limitarea.type == "green":
                            if cmp_float(limitarea.area,self.week_area[-3].area) == 1:
                                self.week_trend_depart.set(-1,high,low)#趋势底背离
                                vnLogger(self.variety,"周趋势背离","底背离_1",str(begindate.date()),str(limitarea),str(prearea),str(self.week_area[-3]))
                            else:
                                if self.getWeekAreaNum() >= 5:
                                    t1 = self.week_area[-3]
                                    t2 = self.week_area[-5]
                                    tsum = t1.area + t2.area
                                    if cmp_float(limitarea.area,tsum) == 1:
                                        self.week_trend_depart.set(-1,high,low)#趋势底背离
                                        vnLogger(self.variety,"周趋势背离","底背离_2",str(begindate.date()))

                        self.week_pre_limit_area = copy.deepcopy(self.week_area[-1])
                        self.weekNewHighFlag = False
                        self.weekSwitchFlag = False
                        vnLogger(self.variety,"周趋势背离","出现新低",str(begindate.date()),self.PreWeekTrend,self.weekTrend,self.week_pre_limit_area)

    #取消周线判断值
    def cancelWeekIndicators(self):

        #背离取消判断
        if self.PreWeekTrend != self.weekTrend:
            self.week_adjacent_depart.reInit()
            self.week_trend_depart.reInit()

            vnLogger(self.variety,"周背离","周趋势改变取消背离",self.PreWeekTrend,self.weekTrend)

            self.backTag["E13"].reInit()
            self.backTag["E34"].reInit()
            self.backTag["E55"].reInit()
            self.backTag["E170"].reInit()
            self.backTag["E275"].reInit()
        
            self.t321OpenFlag = 0
            self.t1Flag = False
            self.t3Flag = False
            self.t2Price = float(0.0)
            self.t3t2HighPrice = float(0.0)
            self.t3t2FixedPrice=0.0
            self.preChangeLimitPrice=0.0

            vnLogger(self.variety,"周趋势改变,实时回踩标记,取消回踩标志,a1_2高点低,t3t2HighPrice",str(self.backTag["E13"]),str(self.backTag["E34"])\
                ,str(self.backTag["E55"]),str(self.backTag["E170"]),str(self.backTag["E275"]))

            self.buckSingal = 0 
            vnLogger(self.variety,"周趋势改变,取消逆势信号")

        else:
            emdata = self.week_am.getLastEma()
            if emdata and len(self.week_am.close) > 0:
                close = self.week_am.close[-1]
                if self.weekTrend == 1 and self.hasPosition and cmp_float(close,max(emdata.e13,emdata.e34,emdata.e55)) > 0:
                    self.week_adjacent_depart.reInit()
                    self.week_trend_depart.reInit()

                    vnLogger(self.variety,"周背离","均线条件取消背离(多)",self.PreWeekTrend,self.weekTrend,close,emdata.e13,emdata.e34,emdata.e55)
                   
                elif self.weekTrend == -1 and self.hasPosition and cmp_float(close,min(emdata.e13,emdata.e34,emdata.e55)) < 0:
                    self.week_adjacent_depart.reInit()
                    self.week_trend_depart.reInit()

                    vnLogger(self.variety,"周背离","均线条件取消背离(空)",self.PreWeekTrend,self.weekTrend,close,emdata.e13,emdata.e34,emdata.e55)

    #根据日线取周线日期
    def getWeekDate(self,daydate):
        weekday = daydate.weekday()
        #4=星期五,
        weekbegindate = None
        if weekday == 4:
            weekbegindate = daydate - datetime.timedelta(days=daydate.weekday())#本周一
            pass
        else:
            weekbegindate = daydate - datetime.timedelta(days=daydate.weekday() + 7)#上周一
            pass

        return weekbegindate

    #取周线趋势
    def getWeekTrend(self,daydate):
 
        weekday = daydate.weekday()
        #4=星期五,
        weekbegindate = None
        if weekday == 4:
            weekbegindate = daydate - datetime.timedelta(days=daydate.weekday())#本周一
            pass
        else:
            weekbegindate = daydate - datetime.timedelta(days=daydate.weekday() + 7)#上周一
            pass

        wdata = self.weekTrendList.get(weekbegindate,None)

        return wdata


    #日线指标数据
    def initDayIndicators(self,srctype:str):

        ziplist = self.day_am.getLastDayZipList()
        if not ziplist:
            vnLogger(self.variety,"initDayIndicators,取最新日线数据失败,不需要更新")
            return 

        self.newE275BackFlag = False

        for index, daydate,e13,e34,e55,e170,e275 ,hist,dea,close,high,low,open in ziplist: 
            
            if ssd.test_cpa.value == "test":
                vnLogger(self.variety,"日线数据",index,daydate,e13,e34,e55,e170,e275 ,hist,dea,close,high,low,open)

            predaytrend = self.dayTrend

            if predaytrend != 1 and cmp_float(e13,max(e34,e55)) == 1 and cmp_float(close,max(e13,e34,e55)) == 1:
                self.dayTrend = 1
                self.dayTrendLimitPrice = low
            elif predaytrend != -1 and cmp_float(e13,min(e34,e55)) == -1 and cmp_float(close,min(e13,e34,e55)) == -1:
                self.dayTrend = -1
                self.dayTrendLimitPrice = high

            preweektrend = self.PreWeekTrend
            weektrend = self.weekTrend

            vnLogger("日线判断时取到的周线趋势",str(daydate.date()),preweektrend,weektrend,predaytrend,self.dayTrend)

            #回踩判断
            if weektrend == 1:
                if cmp_float(high,e13) == 1 and cmp_float(low,e13) == -1 and self.backTag["E13"].flag==0:
                    self.backTag["E13"].set(1,e13,high,low)
                    pass
                if cmp_float(high,e34) == 1 and cmp_float(low,e34) == -1 and self.backTag["E34"].flag==0:
                    self.backTag["E34"].set(1,e34,high,low)
                    pass
                if cmp_float(high,e55) == 1 and cmp_float(low,e55) == -1 and self.backTag["E55"].flag==0:
                    self.backTag["E55"].set(1,e55,high,low)
                    pass
                if cmp_float(high,e170) == 1 and cmp_float(low,e170) == -1 and self.backTag["E170"].flag==0:
                    self.backTag["E170"].set(1,e170,high,low)
                    pass
                if cmp_float(high,e275) == 1 and cmp_float(low,e275) == -1 and self.backTag["E275"].flag==0:
                    self.backTag["E275"].set(1,e275,high,low)
                    self.newE275BackFlag = True

            elif weektrend == -1:
                if cmp_float(high,e13) == 1 and cmp_float(low,e13) == -1 and self.backTag["E13"].flag==0:
                    self.backTag["E13"].set(-1,e13,high,low)
                    pass
                if cmp_float(high,e34) == 1 and cmp_float(low,e34) == -1 and self.backTag["E34"].flag==0:
                    self.backTag["E34"].set(-1,e34,high,low)
                    pass
                if cmp_float(high,e55) == 1 and cmp_float(low,e55) == -1 and self.backTag["E55"].flag==0:
                    self.backTag["E55"].set(-1,e55,high,low)
                    pass
                if cmp_float(high,e170) == 1 and cmp_float(low,e170) == -1 and self.backTag["E170"].flag==0:
                    self.backTag["E170"].set(-1,e170,high,low)
                    pass
                if cmp_float(high,e275) == 1 and cmp_float(low,e275) == -1 and self.backTag["E275"].flag==0:
                    self.backTag["E275"].set(-1,e275,high,low)
                    self.newE275BackFlag = True                     

            vnLogger(self.variety,"实时回踩标志",str(daydate),str(self.backTag["E13"]),str(self.backTag["E34"])\
                ,str(self.backTag["E55"]),str(self.backTag["E170"]),str(self.backTag["E275"]))

            predayhist = self.tempDayPreHist
            self.tempDayPreHist = hist

            #日线趋势改变,清理,确定片区
            if self.tempDayCurrentArea is None:

                if cmp_float(hist ,0.0) != 0:
                    self.tempDayCurrentArea = MacdArea()
                    self.tempDayCurrentArea.beginIndex = index
                    self.tempDayCurrentArea.barPrice = close
                    self.tempDayCurrentArea.yellowPrice = dea
                    self.tempDayCurrentArea.area = hist
                    self.tempDayCurrentArea.num+=1
                    self.tempDayCurrentArea.highPrice = high
                    self.tempDayCurrentArea.lowPrice = low
                    self.tempDayCurrentArea.initDate = daydate
                    self.tempDayCurrentArea.e13 = e13
                    self.tempDayCurrentArea.e34 = e34
                    self.tempDayCurrentArea.e55 = e55

                    if cmp_float(hist,0.0) > 0:
                        self.tempDayCurrentArea.type = "red"
                    elif cmp_float(hist,0.0) < 0:
                        self.tempDayCurrentArea.type = "green"
                    #and self.dayTrend < 0

                    if cmp_float(high,e34)>0:
                        self.tempDayCurrentArea.greatE34Tag=True

                    if cmp_float(low,e34)<0:
                        self.tempDayCurrentArea.lessE34Tag=True

            else:
                if cmp_float(predayhist,0.0) == 1 and cmp_float(hist,0.0) == 1 and self.tempDayCurrentArea.type == "red":
                        self.tempDayCurrentArea.barPrice = max(self.tempDayCurrentArea.barPrice,close)
                        self.tempDayCurrentArea.yellowPrice = max(self.tempDayCurrentArea.yellowPrice,dea)
                        self.tempDayCurrentArea.area = self.tempDayCurrentArea.area + hist
                        self.tempDayCurrentArea.num+=1

                        if cmp_float(high,self.tempDayCurrentArea.highPrice) == 1:
                            self.tempDayCurrentArea.e13 = e13
                            self.tempDayCurrentArea.e34 = e34
                            self.tempDayCurrentArea.e55 = e55
                            self.tempDayCurrentArea.highPrice = high

                        if cmp_float(low,self.tempDayCurrentArea.lowPrice) == -1:
                            self.tempDayCurrentArea.lowPrice = low

                        if cmp_float(high,e34)>0:
                            self.tempDayCurrentArea.greatE34Tag=True
                        if cmp_float(low,e34)<0:
                            self.tempDayCurrentArea.lessE34Tag=True

                        self.tempDayIsHistSwitch = 0    
                  
                elif cmp_float(predayhist,0.0) == -1 and cmp_float(hist,0.0) == -1 and self.tempDayCurrentArea.type == "green":
                    self.tempDayCurrentArea.barPrice = min(self.tempDayCurrentArea.barPrice,close)
                    self.tempDayCurrentArea.yellowPrice = min(self.tempDayCurrentArea.yellowPrice,dea)
                    self.tempDayCurrentArea.area = self.tempDayCurrentArea.area + hist
                    self.tempDayCurrentArea.num+=1

                    if cmp_float(high,self.tempDayCurrentArea.highPrice) == 1:
                        self.tempDayCurrentArea.highPrice = high

                    if cmp_float(low,self.tempDayCurrentArea.lowPrice) == -1:
                        self.tempDayCurrentArea.e13 = e13
                        self.tempDayCurrentArea.e34 = e34
                        self.tempDayCurrentArea.e55 = e55
                        self.tempDayCurrentArea.lowPrice = low


                    if cmp_float(high,e34)>0:
                            self.tempDayCurrentArea.greatE34Tag=True
                    if cmp_float(low,e34)<0:
                        self.tempDayCurrentArea.lessE34Tag=True

                    self.tempDayIsHistSwitch = 0

                elif cmp_float(predayhist,0.0) <= 0 and cmp_float(hist,0.0) > 0 : 
                    #绿切红,待处理的是绿柱
                    if self.dayAreaIntFlag:
                        
                        vnLogger(self.variety,"zhe","临时",str(self.tempDayCurrentArea))

                        cdayarea = copy.deepcopy(self.day_area[-1])
                        updatetype = str("")#add=添加,merge=合并

                        if self.dayTrend>0: 
                            if self.tempDayCurrentArea.lessE34Tag:
                                
                                if cdayarea.type=="red":
                                    updatetype = "add"
                                    vnLogger("zhe","日多,cday是红,当前是绿,当前回踩,添加")
                                else:
                                    updatetype = "merge"
                                    vnLogger("zhe","日多,cday是非红,当前是绿,当前没有回踩,合并")

                            else:
                                updatetype = "merge"
                                vnLogger("zhe","日多,cday是绿,,当前是绿,当前没有回踩,合并")
                        else:
                            if cdayarea.type=="red":
                                updatetype = "add"
                                vnLogger("zhe","日空,cday是红,当前是绿,添加")
                            else:
                                updatetype = "merge"
                                vnLogger("zhe","日空,cday是绿,当前是绿,合并")

                        #实际执行
                        if updatetype == "add":
                            self.day_area[-1].confirmDate = self.tempDayCurrentArea.initDate
                            self.day_area[:-1] = self.day_area[1:]
                            self.day_area[-1] = copy.deepcopy(self.tempDayCurrentArea)

                        elif updatetype=="merge":
                            
                            #合并绿柱内容到绿柱
                            self.day_area[-1].barPrice = min(self.day_area[-1].barPrice,self.tempDayCurrentArea.barPrice)
                            self.day_area[-1].yellowPrice = min(self.day_area[-1].yellowPrice,self.tempDayCurrentArea.yellowPrice)
                            #self.day_area[-1].initDate =cdayarea.initDate
                            self.day_area[-1].highPrice = max(self.day_area[-1].highPrice,self.tempDayCurrentArea.highPrice)
                            #self.tempDayCurrentArea.area+=cdayarea.area+self.tempDayCurrentArea.area
                            #self.tempDayCurrentArea.num+=cdayarea.num
                            self.day_area[-1].num+=self.tempDayCurrentArea.num

                            if cmp_float(self.tempDayCurrentArea.lowPrice,self.day_area[-1].lowPrice) < 0:
                                self.day_area[-1].e13 = self.tempDayCurrentArea.e13
                                self.day_area[-1].e34 = self.tempDayCurrentArea.e34
                                self.day_area[-1].e55 = self.tempDayCurrentArea.e55
                                self.day_area[-1].lowPrice = self.tempDayCurrentArea.lowPrice

                            #self.day_area[-1].e34BackTag = self.day_area[-1].e34BackTag or cdayarea.e34BackTag or self.tempDayCurrentArea.e34BackTag
                            #test
                            #self.testDeleteDict(cdayarea.initDate)
                            #self.testDeleteDict(self.tempDayCurrentArea.initDate)

                        else:
                            vnLogger(self.variety,daydate,"日线区处理错误,待处理是绿柱")

                    else:
                        self.day_area[-1].confirmDate = self.tempDayCurrentArea.initDate
                        self.day_area[:-1] = self.day_area[1:]
                        self.day_area[-1] = copy.deepcopy(self.tempDayCurrentArea)

                        vnLogger("zhe","init")

                        self.dayAreaIntFlag = True

                        pass

                    self.tempDayIsHistSwitch = 1

                    self.tempDayCurrentArea = MacdArea()
                    self.tempDayCurrentArea.type = "red"
                    self.tempDayCurrentArea.beginIndex = index
                    self.tempDayCurrentArea.barPrice = close
                    self.tempDayCurrentArea.yellowPrice = dea
                    self.tempDayCurrentArea.area = hist
                    self.tempDayCurrentArea.num+=1
                    self.tempDayCurrentArea.highPrice = high
                    self.tempDayCurrentArea.lowPrice = low
                    self.tempDayCurrentArea.initDate = daydate
                    self.tempDayCurrentArea.e13 = e13
                    self.tempDayCurrentArea.e34 = e34
                    self.tempDayCurrentArea.e55 = e55

                    if cmp_float(high,e34)>0:
                            self.tempDayCurrentArea.greatE34Tag=True

                    if cmp_float(low,e34)<0:
                        self.tempDayCurrentArea.lessE34Tag=True
                   
                elif cmp_float(predayhist,0.0) >= 0 and cmp_float(hist,0.0) < 0:#red area
                    #红切绿,当前是待处理的是红柱,临时是绿柱
                    if self.dayAreaIntFlag:

                        cdayarea = copy.deepcopy(self.day_area[-1])
                        updatetype = str("")#add=添加,merge=合并

                        if self.dayTrend<0: 
                            if self.tempDayCurrentArea.greatE34Tag:
                                
                                if cdayarea.type=="green":
                                    updatetype = "add"
                                    vnLogger("zhe","日空,cday是绿,当前是红,当前回踩,添加")
                                else:
                                    updatetype = "merge"
                                    vnLogger("zhe","日空,cday是红,当前是红,当前回踩,合并")

                            else:
                                datetype = "merge"
                                vnLogger("zhe","日空,cday是红,当前是红,当前没有回踩,合并")
                        else:
                            if cdayarea.type=="green":
                                updatetype = "add"
                                vnLogger("zhe","日多,cday是绿,当前是红,添加")
                            else:
                                updatetype = "merge"
                                vnLogger("zhe","日多,cday非绿,当前是绿红,合并")

                        #实际执行
                        if updatetype == "add":
                            self.day_area[-1].confirmDate = self.tempDayCurrentArea.initDate
                            self.day_area[:-1] = self.day_area[1:]
                            self.day_area[-1] = copy.deepcopy(self.tempDayCurrentArea)
                        
                        elif updatetype == "merge":
                            
                            self.day_area[-1].barPrice = max(self.day_area[-1].barPrice,self.tempDayCurrentArea.barPrice)
                            self.day_area[-1].yellowPrice = max(self.day_area[-1].yellowPrice,self.tempDayCurrentArea.yellowPrice)
                            #self.day_area[-1].initDate =
                            #cdayarea.initDate
                            self.day_area[-1].lowPrice = min(self.day_area[-1].lowPrice,self.tempDayCurrentArea.lowPrice)
                            #self.tempDayCurrentArea.area+=cdayarea.area+self.tempDayCurrentArea.area
                            #self.tempDayCurrentArea.num+=cdayarea.num
                            self.day_area[-1].num+=self.tempDayCurrentArea.num

                            if cmp_float(self.tempDayCurrentArea.highPrice,self.day_area[-1].highPrice) > 0:
                                self.day_area[-1].e13 = self.tempDayCurrentArea.e13
                                self.day_area[-1].e34 = self.tempDayCurrentArea.e34
                                self.day_area[-1].e55 = self.tempDayCurrentArea.e55
                                self.day_area[-1].highPrice = self.tempDayCurrentArea.highPrice

                            #self.day_area[-1].e34BackTag = self.day_area[-1].e34BackTag or cdayarea.e34BackTag or self.tempDayCurrentArea.e34BackTag
                            #test
                            #self.testDeleteDict(self.tempDayCurrentArea.initDate)
                        else:
                            vnLogger(self.variety,daydate,"日线区处理错误")

                    else:
                        self.day_area[-1].confirmDate = self.tempDayCurrentArea.initDate
                        self.day_area[:-1] = self.day_area[1:]
                        self.day_area[-1] = copy.deepcopy(self.tempDayCurrentArea)
                        vnLogger("zhe","init")

                        self.dayAreaIntFlag = True

                    self.tempDayIsHistSwitch = -1
                    self.tempDayCurrentArea = MacdArea()
                    self.tempDayCurrentArea.type = "green"
                    self.tempDayCurrentArea.beginIndex = index
                    self.tempDayCurrentArea.barPrice = close
                    self.tempDayCurrentArea.yellowPrice = dea
                    self.tempDayCurrentArea.area = hist
                    self.tempDayCurrentArea.num+=1
                    self.tempDayCurrentArea.highPrice = high
                    self.tempDayCurrentArea.lowPrice = low
                    self.tempDayCurrentArea.initDate = daydate
                    self.tempDayCurrentArea.e13 = e13
                    self.tempDayCurrentArea.e34 = e34
                    self.tempDayCurrentArea.e55 = e55
                    vnLogger(self.variety,"zhe","重新初始化绿柱")
                    
                    if cmp_float(high,e34)>0:
                            self.tempDayCurrentArea.greatE34Tag=True

                    if cmp_float(low,e34)<0:
                        self.tempDayCurrentArea.lessE34Tag=True

            if predaytrend == 1 and self.dayTrend == 1:
                self.dayTrendLimitPrice = min(self.dayTrendLimitPrice,low)
            elif predaytrend == -1 and self.dayTrend == -1:
                self.dayTrendLimitPrice = max(self.dayTrendLimitPrice,high)

            if self.getDayAreaNum() >= 3:
                #日线高低点背离
                if ((predaytrend == 0 or predaytrend == -1) and self.dayTrend == 1) or (predaytrend == 1 and self.dayTrend == -1) or ((predaytrend == 0 or predaytrend == 1) and self.dayTrend == -1) or (predaytrend == -1 and self.dayTrend == 1):

                    if self.dayTrend == 1:
                        self.dayPreLimitPrice = high#多头趋势确定时,初始化趋势高点
                    elif self.dayTrend == -1:
                        self.dayPreLimitPrice = low

                    self.dayPreLimitArea = MacdArea()
                    self.dayNewHighFlag = False
                    self.dayLimitFlag = False
                    self.daySwitchFlag = False

                    self.dayTrendDepart = 0

                elif predaytrend == 1 and self.dayTrend == 1:
                    if not self.daySwitchFlag:
                        self.dayPreLimitPrice = max(self.dayPreLimitPrice,high)

                        if self.tempDayIsHistSwitch ==-1:
                            if self.dayLimitFlag:
                                self.daySwitchFlag = True
                                pass
                            else:
                                #确定次高点
                                self.dayLimitFlag = True
                                self.dayPreLimitArea = copy.deepcopy(self.day_area[-1])
                                pass

                    if self.daySwitchFlag:
                        #macd切换且出现新高
                        if cmp_float(high,self.dayPreLimitPrice) == 1:
                            self.dayNewHighFlag = True
                            self.dayPreLimitPrice = high
                            pass

                        #新高后继续切换
                        if self.tempDayIsHistSwitch ==-1 and self.dayNewHighFlag and self.dayLimitFlag:
                            #判断是否趋势高低点背离
                            limitarea = self.day_area[-1]
                            prearea = self.dayPreLimitArea
                            if cmp_float(limitarea.yellowPrice,prearea.yellowPrice) == -1:
                                self.dayTrendDepart = 1 #趋势顶背离

                            self.dayPreLimitArea = copy.deepcopy(self.day_area[-1])
                            self.dayNewHighFlag = False
                            self.daySwitchFlag = False
                            pass
                elif predaytrend == -1 and self.dayTrend == -1:
                    if not self.daySwitchFlag:
                        self.dayPreLimitPrice = min(self.dayPreLimitPrice,low)

                        if self.tempDayIsHistSwitch ==1:
                            if self.dayLimitFlag:
                                self.daySwitchFlag = True
                                pass
                            else:
                                #确定次高点
                                self.dayLimitFlag = True
                                self.dayPreLimitArea = copy.deepcopy(self.day_area[-1])
                                pass

                    if self.daySwitchFlag:
                        #macd切换且出现新高
                        if cmp_float(low,self.dayPreLimitPrice) == -1:
                            self.dayNewHighFlag = True
                            self.dayPreLimitPrice = low
                            pass

                        #新高后继续切换
                        if self.tempDayIsHistSwitch ==1 and self.dayNewHighFlag and self.dayLimitFlag:
                            #判断是否趋势高低点背离
                            limitarea = self.day_area[-1]
                            prearea = self.dayPreLimitArea
                            if cmp_float(limitarea.yellowPrice,prearea.yellowPrice) == 1:
                                self.dayTrendDepart = -1#趋势底背离
                                
                            self.dayPreLimitArea = copy.deepcopy(self.day_area[-1])
                            self.dayNewHighFlag = False
                            self.daySwitchFlag = False
                            pass
                    pass

            #反正反破颈
            self.brokeNeckSignalFlag = self.getBreakSingal(high,low,close,open,"break")
            
            vnLogger(self.variety,"反正反破颈信号",daydate,self.brokeNeckSignalFlag,high,self.getDayAdjacentDepart())

            if self.newE275BackFlag:
                self.t321OpenFlag = 0
                self.t1Flag = False
                self.t3Flag = False
                self.t2Price = float(0.0)
                self.t3t2HighPrice = float(0.0)
                self.t3t2FixedPrice=0.0
                self.preChangeLimitPrice=0.0

                vnLogger(self.variety,daydate,"a1_2高点低,t3t2HighPrice","重置t1,t2,t3")

            #a1_2开仓条件
            if weektrend == 1:

                if  self.brokeNeckSignalFlag == -1 and self.buckSingal == 0:
                    self.buckSingal = 1
                    vnLogger(self.variety,"a1_2高点低","逆势信号成立,周多",daydate,self.buckSingal,self.brokeNeckSignalFlag)

                if self.t1Flag:

                    if self.t3Flag:
                        
                        if cmp_float(self.preChangeLimitPrice,0.0)>0:
                            self.t3t2HighPrice = max(self.preChangeLimitPrice,self.t3t2HighPrice)
                            self.preChangeLimitPrice=0.0

                        if cmp_float(close,self.t3t2HighPrice) == 1:
                            self.t321OpenFlag = 1
                            vnLogger(self.variety,"a1_2高点低",",".join(["切换红柱-2",str(daydate),str(self.t2Price),str(self.t3t2HighPrice)\
                                ,str(self.t321OpenFlag)]))

                        self.t3t2FixedPrice=self.t3t2HighPrice
                        self.t3Flag=False

                    else:

                        if self.tempDayIsHistSwitch == 1 and (not self.t3Flag):
                            vnLogger(self.variety,"a1_2高点低",weektrend,high,self.t3t2HighPrice,close,open)
                            self.t3Flag = True
                            if cmp_float(close,self.t3t2HighPrice) >=0 :
                                self.t321OpenFlag = 1
                                vnLogger(self.variety,"a1_2高点低",",".join(["切换红柱-1",str(daydate),str(self.t2Price),str(self.t3t2HighPrice)\
                                ,str(self.t321OpenFlag)]))
   
                            self.t3t2FixedPrice=self.t3t2HighPrice
                            self.preChangeLimitPrice=high
                            #self.t3t2HighPrice = max(high,self.t3t2HighPrice)
                            vnLogger(self.variety,"a1_2高点低,-1,已确定t3,更新当前高点,记录高点",high,self.t3t2HighPrice)

                        else:

                            if cmp_float(low,self.t2Price) == -1:
                                self.t2Price = low
                                self.t3t2HighPrice = high
                                vnLogger(self.variety,"a1_2高点低",",".join(["寻找t2",str(daydate),str(self.t2Price),str(self.t3t2HighPrice)]))
                            else:
                                self.t3t2HighPrice = max(self.t3t2HighPrice,high)
                                vnLogger(self.variety,"a1_2高点低",",".join(["更新t2t3高点",str(daydate),str(self.t3t2HighPrice)]))

                else:
                    if self.backTag["E275"].flag == 1 and self.newE275BackFlag:
                        self.t2Price = low
                        self.t3t2HighPrice = high
                        self.t1Flag = True
                        self.preChangeLimitPrice=0.0
                        self.t3t2t3t2FixedPrice=0.0
                            
                        vnLogger(self.variety,"a1_2高点低",",".join(["时间T1_weektrend=1",str(daydate),str(self.backTag["E275"]),str(self.t3t2HighPrice)]))

            elif weektrend == -1:

                if self.brokeNeckSignalFlag == 1 and self.buckSingal == 0 :
                    self.buckSingal = -1
                    vnLogger(self.variety,"a1_2高点低","逆势信号成立,周空",daydate,self.buckSingal,self.brokeNeckSignalFlag)

                if self.t1Flag:

                    if self.t3Flag:

                        if cmp_float(self.preChangeLimitPrice,0.0)>0:
                            self.t3t2HighPrice = min(self.preChangeLimitPrice,self.t3t2HighPrice)
                            self.preChangeLimitPrice=0.0
                            vnLogger(self.variety,"weektrend=-1,测试_1",self.t3t2HighPrice,low,close,self.preChangeLimitPrice,daydate)

                        vnLogger(self.variety,"weektrend=-1,测试",self.t3t2HighPrice,low,close,daydate)
                        if cmp_float(close,self.t3t2HighPrice) == -1:#close
                            self.t321OpenFlag = -1
                            vnLogger(self.variety,"a1_2高点低",",".join(["切换绿柱-2",str(daydate),str(self.t2Price),str(self.t3t2HighPrice)\
                                ,str(self.t321OpenFlag)]))

                        self.t3t2FixedPrice=self.t3t2HighPrice
                        self.t3Flag=False

                    else:

                        if self.tempDayIsHistSwitch == -1 and (not self.t3Flag):
                            self.t3Flag = True
                            vnLogger(self.variety,"a1_2高点低",low,self.t3t2HighPrice,close)
                            if cmp_float(close,self.t3t2HighPrice) <= 0:
                                self.t321OpenFlag = -1
                                vnLogger(self.variety,"a1_2高点低",",".join(["切换绿柱-1",str(daydate),str(self.t2Price),str(self.t3t2HighPrice)\
                                ,str(self.t321OpenFlag)]))

                            #self.t3t2HighPrice = min(low,self.t3t2HighPrice)
                            self.t3t2FixedPrice=self.t3t2HighPrice
                            self.preChangeLimitPrice=low
                            vnLogger(self.variety,"a1_2高点低,-1,已确定t3,更新当前低点,记录低点",low,self.t3t2HighPrice,self.t3t2FixedPrice)

                        else:

                            if cmp_float(high,self.t2Price) == 1:
                                self.t2Price = high
                                self.t3t2HighPrice = low

                                vnLogger(self.variety,"a1_2高点低",",".join(["寻找t2_-1",str(daydate),str(self.t2Price),str(self.t3t2HighPrice)]))
                            else:
                                self.t3t2HighPrice = min(self.t3t2HighPrice,low)
                                vnLogger(self.variety,"a1_2高点低",",".join(["更新t2t3低点_-1",str(daydate),str(self.t3t2HighPrice)]))

                else:
                    if self.backTag["E275"].flag == -1 and self.newE275BackFlag:
                        self.t2Price = high
                        self.t3t2HighPrice = low
                        self.t1Flag = True
                        self.preChangeLimitPrice=0.0

                        vnLogger(self.variety,"a1_2高点低","时间T1,weektrend=-1",str(daydate),str(self.backTag["E275"])\
                            ,self.t1Flag,self.t3t2HighPrice)
        

        #仅适用于A3
        if self.iwType == "A3" and self.pos != 0 and srctype is "last" and cmp_float(self.openLimit,0.0) == 1 and cmp_float(self.posNewLimitPrice,0.0) == 1:

            if self.pos > 0:

                if cmp_float(predayhist,0.0) == 1 and cmp_float(hist,0.0) == -1:
                    if cmp(self.posMacPrice1,0.0) <= 0:
                        self.posMacPrice1 = low
                elif cmp_float(predayhist,0.0) == -1 and cmp_float(hist,0.0) == -1: 
                    if cmp(self.posMacPrice2,0.0) <= 0:
                        self.posMacPrice2 = low
                pass
            elif self.pos < 0:
                if cmp_float(predayhist,0.0) == -1 and cmp_float(hist,0.0) == 1:
                    if cmp(self.posMacPrice1,0.0) <= 0:
                        self.posMacPrice1 = high
                elif cmp_float(predayhist,0.0) == 1 and cmp_float(hist,0.0) == 1: 
                    if cmp(self.posMacPrice2,0.0) <= 0:
                        self.posMacPrice2 = high
                pass

    #1=向上,-1=向下,0=没有,type="offset",type="break"
    def getBreakSingal(self,high,low,close,open,type:str):
        #向上的反正反
        if self.getDayAreaNum() <= 3:
            return 0

        #判断是否向上
        #if self.day_area[-1].type == "green":
        if True:
            lastlow = self.day_area[-1].lowPrice
            sechigh = self.day_area[-2].highPrice
            thirdlow = self.day_area[-3].lowPrice

            lastema = min(self.day_area[-1].e13,self.day_area[-1].e34,self.day_area[-1].e55)
            trdema = min(self.day_area[-3].e13,self.day_area[-3].e34,self.day_area[-3].e55)

            tempprice=close
            if type=="offset":
                tempprice=high

            vnLogger(self.variety,"反正反测试,向上",str(self.day_am.dateList[-1].date()),self.day_area[-1].type\
                ,lastlow,sechigh,thirdlow,lastema,trdema,close,high,low,tempprice,type,self.day_area[-2].e34)

            if cmp_float(lastlow,lastema) < 0 and cmp_float(sechigh,self.day_area[-2].e34) > 0 \
                and cmp_float(thirdlow,trdema) < 0  and cmp_float(tempprice,sechigh) >=0:

                vnLogger(self.variety,"反正反,向上",lastlow,sechigh,thirdlow,close)
                return 1

        #elif self.day_area[-1].type == "red":
        if True:

            lasthigh = self.day_area[-1].highPrice
            seclow = self.day_area[-2].lowPrice
            thirdhigh = self.day_area[-3].highPrice

            lastema = max(self.day_area[-1].e13,self.day_area[-1].e34,self.day_area[-1].e55)
            trdema = max(self.day_area[-3].e13,self.day_area[-3].e34,self.day_area[-3].e55)

            tempprice=close
            if type=="offset":
                tempprice=low

            vnLogger(self.variety,"反正反测试,向下",self.day_am.dateList[-1],self.day_area[-1].type\
                ,lasthigh,seclow,thirdhigh,lastema,trdema,close,high,low,tempprice,type,self.day_area[-2].e34)

            if cmp_float(lasthigh,lastema) > 0 and cmp_float(seclow,self.day_area[-2].e34) < 0 \
                and cmp_float(thirdhigh,trdema) > 0 and cmp_float(tempprice,seclow) <= 0:

                vnLogger(self.variety,"反正反,向下",lasthigh,seclow,thirdhigh,close)
                return -1

        return 0
            
    def cancelDayIndicators(self,openflag:bool,change_rate:float):

        lastema = self.day_am.getLastEma()
        if not lastema:
            return

        close = self.day_am.close[-1]
        open = self.day_am.open[-1]

        haspos=openflag or self.hasPosition

        vnLogger(self.variety,self.day_am.dateList[-1],"参数",change_rate,openflag,self.hasPosition)
        #回踩取消判断
        cancletag = False
        if haspos and cmp_float(close,max(lastema.e13,lastema.e34,lastema.e55,lastema.e170,lastema.e275)) == 1\
           and cmp_float(close / open, change_rate) == 1:
           cancletag = True
           vnLogger(self.variety,"有仓且满足均线条件,取消回踩条件成立_2",self.weekTrend,self.PreWeekTrend,cancletag\
               ,change_rate,close,open)

        elif haspos and cmp_float(close,min(lastema.e13,lastema.e34,lastema.e55,lastema.e170,lastema.e275)) == -1 \
            and cmp_float(open / close, change_rate) == 1:
            cancletag = True
            vnLogger(self.variety,"有仓且满足均线条件,取消回踩条件成立_4",self.weekTrend,self.PreWeekTrend,cancletag\
                ,change_rate,close,open)
                
        #回踩取消条件成立
        if cancletag:
            self.backTag["E13"].reInit()
            self.backTag["E34"].reInit()
            self.backTag["E55"].reInit()
            self.backTag["E170"].reInit()
            self.backTag["E275"].reInit()

            self.t321OpenFlag = 0
            self.t1Flag = False
            self.t3Flag = False
            self.t2Price = float(0.0)
            self.t3t2HighPrice = float(0.0)
            self.t3t2FixedPrice=0.0
            self.preChangeLimitPrice=0.0
            
            vnLogger(self.variety,self.day_am.dateList[-1],"日线,实时回踩标记,取消回踩标志,a1_2高点低,t3t2HighPrice",str(self.backTag["E13"]),str(self.backTag["E34"])\
                ,str(self.backTag["E55"]),str(self.backTag["E170"]),str(self.backTag["E275"]))

        high = self.day_am.high[-1]
        low = self.day_am.low[-1]
        if (self.week_adjacent_depart.flag == 1 or self.week_trend_depart.flag == 1) and cmp_float(low,lastema.e275) == -1:
            self.week_adjacent_depart.reInit()
            self.week_trend_depart.reInit()
        elif (self.week_adjacent_depart.flag == -1 or self.week_trend_depart.flag == -1) and cmp_float(high,lastema.e275) == 1:
            self.week_adjacent_depart.reInit()
            self.week_trend_depart.reInit()

    #取消周线E275回踩
    def cancelWeekE275BackTag(self):
        if self.backTag and self.backTag["E275"]:
             self.backTag["E275"].reInit()

    #判断日线背离, -1#底背离,1=顶背离
    def getDayAdjacentDepart(self):
        if self.getDayAreaNum() >= 3:
            #背离判断
            if self.dayTrend == -1:
                ctarea = self.day_area[-1]
                subarea = self.day_area[-3]
                if ctarea and subarea and cmp_float(ctarea.lowPrice,subarea.lowPrice) < 0 \
                    and cmp_float(ctarea.yellowPrice,subarea.yellowPrice) > 0 and ctarea.type == "green":
                    vnLogger(self.variety,"日背离,底背离",ctarea.highPrice,subarea.highPrice,ctarea.yellowPrice,subarea.yellowPrice)
                    return -1#底背离

            elif self.dayTrend == 1:
                ctarea = self.day_area[-1]
                subarea = self.day_area[-3]
                if ctarea and subarea and cmp_float(ctarea.highPrice,subarea.highPrice) > 0\
                   and cmp_float(ctarea.yellowPrice,subarea.yellowPrice) < 0 and ctarea.type == "red":

                    vnLogger(self.variety,"日背离,顶背离",ctarea.highPrice,subarea.highPrice,ctarea.yellowPrice,subarea.yellowPrice)
                    return 1#顶背离
        return 0

    def getDayAreaNum(self):
        if not self.day_area:
            return 0

        num = 0
        for area in reversed(self.day_area):
            if area.type == "green" or area.type == "red":
                num+=1

        return num

    def getWeekAreaNum(self):
        if not self.week_area:
            return 0

        num = 0
        for area in reversed(self.week_area):
            if area.type == "green" or area.type == "red":
                num+=1

        return num

    def updateLastIndicators(self,lastdaybar:LastBarData,lastweekbar:LastBarData):

        if lastweekbar:
            self.week_am.updateLastBar(lastweekbar)
            self.initWeekIndicators("last")
           
            for i, val in enumerate(self.week_area):
                vnLogger(self.variety,"周线",i,str(val))


        if lastdaybar:
            self.day_am.updateLastBar(lastdaybar)
            self.initDayIndicators("last")

            for i, val in enumerate(self.day_area):
                vnLogger(self.variety,"日线",i,str(val))
                self.testDayArea[val.initDate]=val

    def testDeleteDict(self,cdate):
            self.testDayArea.pop(cdate,None)