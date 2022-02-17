import numpy as np
import datetime
from vnpy.app.cta_strategy.QueryIndexWidget.Query_Index_Bar import*
from vnpy.app.cta_strategy.public import *
from vnpy.app.cta_strategy.cpcta.cp_constant import *
from vnpy.app.cta_strategy.cpcta.cp_object import *
from vnpy.app.ssd_logger.ProcessLogger import*

#原始数据
class BarManager:

    #type: day,week
    def __init__(self,type:str,variety:str):

        self.lastBarFlag = False
        self.type = type
        self.variety = variety

        #原始数据,使用python列表保存
        self.high = []
        self.low = []
        self.open = []
        self.close = []
        self.dateList = []
        self.indexList = []
        self.dateIndexList = {}
        #均线数据
        self.E13 = []
        self.E34 = []
        self.E55 = []
        self.E170 = []
        self.E275 = []

        self.E12 = []
        self.E26 = []
        self.E9 = []

        #计算数据
        self.macd = []
        self.signal = []
        self.hist = []



    def __updateTotalAvg(self):
        #ema
        self.E13 = []
        self.E34 = []
        self.E55 = []
        self.E170 = []
        self.E275 = []

        self.E12 = []
        self.E26 = []
        #self.E9=[]

        #计算数据
        self.macd = []
        self.signal = []
        self.hist = []

        for i, val in enumerate(self.close):

            if i == 0:
                self.E13.append(val)
                self.E34.append(val)
                self.E55.append(val)
                self.E170.append(val)
                self.E275.append(val)

                self.E12.append(val)
                self.E26.append(val)
                #self.E9.append(close)
            else:
                e13 = self.__calSigEma(self.E13[-1],val,13)
                e34 = self.__calSigEma(self.E34[-1],val,34)
                e55 = self.__calSigEma(self.E55[-1],val,55)
                e170 = self.__calSigEma(self.E170[-1],val,170)
                e275 = self.__calSigEma(self.E275[-1],val,275)

                e12 = self.__calSigEma(self.E12[-1],val,12)
                e26 = self.__calSigEma(self.E26[-1],val,26)
                #e9=self.__calSigEma(self.E9[-1],val,9)

                self.E13.append(e13)
                self.E34.append(e34)
                self.E55.append(e55)
                self.E170.append(e170)
                self.E275.append(e275)

                self.E12.append(e12)
                self.E26.append(e26)

                pass

        #macd=diff,signal=dea,hist=macd
        self.macd, self.signal, self.hist = self.__calMacd(self.close)

        pass

    def __calMacd(self,close:list):
        
        difflist = np.around(np.array(self.E12) - np.array(self.E26),2)
        dealist = []

        for i,diff in enumerate(difflist):
            if i == 0:
                dealist.append(diff)
                continue
            else:
                dea = dealist[-1] * 8 / 10 + diff * 2 / 10
                dealist.append(dea)

        dealist = np.around(np.array(dealist),2)
        histlist = np.around(difflist - dealist,2)

        return difflist.tolist(),dealist.tolist(),histlist.tolist()

    def __calSigEma(self,preEma:float,close:float,N:int):
        cema = ((N - 1) * preEma + 2 * close) / (N + 1)
        return round_to(cema,0.01)

    #仅更新最新一条
    def updateLastBar(self,lastbar:LastBarData):

        if lastbar:
            open = lastbar.open
            high = lastbar.high
            close = lastbar.close
            low = lastbar.low
            lasttime = lastbar.time

            self.__updateLastBar(open,high,close,low,lasttime)

    def __updateLastBar(self,open:float,high:float,close:float,low:float,begintime):

        if len(self.dateList) > 0:# and self.dateList[-1] == begintime:

            if begintime == self.dateList[-1]:
                #update
                self.open[-1] = open
                self.high[-1] = high
                self.close[-1] = close
                self.low[-1] = low
                self.dateList[-1] = begintime
                #更新时间信息
                index = len(self.dateList)
                #self.indexlist.append(index)
                self.dateIndexList[begintime] = index

                vnLogger(self.variety,self.type,"更新K线" ,str(begintime))

            elif begintime > self.dateList[-1]:
                #append
                self.open.append(open)
                self.high.append(high)
                self.close.append(close)
                self.low.append(low)
                self.dateList.append(begintime)
                #更新时间信息
                index = len(self.dateList)
                self.indexList.append(index)
                self.dateIndexList[begintime] = index

                vnLogger(self.variety,self.type,"------增加新的K线------" ,self.type,str(begintime))

                pass
            else:
                #时间不对,放弃
                vnLogger(self.variety,self.type,"time is wrong,drop," , str(begintime) ,str(self.dateList[-1]))
                pass
        else:
            #append
            self.open.append(open)
            self.high.append(high)
            self.close.append(close)
            self.low.append(low)
            self.dateList.append(begintime)
            #更新时间信息
            index = len(self.dateList)
            self.indexList.append(index)
            self.dateIndexList[begintime] = index

            vnLogger(self.variety,self.type,"初始化K线," + str(begintime))

            pass

        #重新计算最后一条的均线等数据
        self.__calLastEma(self.E13,close,13)
        self.__calLastEma(self.E34,close,34)
        self.__calLastEma(self.E55,close,55)
        self.__calLastEma(self.E170,close,170)
        self.__calLastEma(self.E275,close,275)
        self.__calLastEma(self.E12,close,12)
        self.__calLastEma(self.E26,close,26)

        #更新最后一条macd
        diff = self.E12[-1] - self.E26[-1]
        dea = 0.0
        if len(self.signal) > 0:
            dea = self.signal[-1] * 8 / 10 + diff * 2 / 10
        else:
             dea = diff

        hist = diff - dea

        self.macd.append(round_to(diff,0.01))
        self.signal.append(round_to(dea,0.01))
        self.hist.append(round_to(hist,0.01))

    def __calLastEma(self,elist:list,close:float,period:int):
        if len(elist) > 0:
            evalue = self.__calSigEma(elist[-1],close,period)
            elist.append(evalue)
        else:
            elist.append(close)

    #返回最后一条
    def getLastEma(self):

        if len(self.E13) <= 0 or len(self.E34) <= 0 or len(self.E55) <= 0 or len(self.E170) <= 0 or len(self.E275) <= 0:
            return None
        else:
            return  EmaData(self.E13[-1],self.E34[-1],self.E55[-1],self.E170[-1],self.E275[-1])

    #周线
    def getWeekZipList(self):

        ema13 = self.E13
        ema34 = self.E34
        ema55 = self.E55
        histlist = self.hist
        sglist = self.signal
        closelist = self.close
        highlist = self.high
        lowlist = self.low
        datelist = self.dateList
        indexlist = self.indexList

        return zip(indexlist,datelist,ema13,ema34,ema55,histlist,sglist,closelist,highlist,lowlist)

    def getLastWeekZipList(self):

        ema13 = self.E13[-1:]
        ema34 = self.E34[-1:]
        ema55 = self.E55[-1:]

        histlist = self.hist[-1:]
        sglist = self.signal[-1:]
        closelist = self.close[-1:]
        highlist = self.high[-1:]
        lowlist = self.low[-1:]
        datelist = self.dateList[-1:]
        indexlist = self.indexList[-1:]

        return zip(indexlist,datelist,ema13,ema34,ema55,histlist,sglist,closelist,highlist,lowlist)

    #日线
    def getDayZipList(self):

        ema13 = self.E13
        ema34 = self.E34
        ema55 = self.E55
        ema170 = self.E170
        ema275 = self.E275

        histlist = self.hist
        sglist = self.signal
        closelist = self.close
        highlist = self.high
        lowlist = self.low
        openlist = self.open
        datelist = self.dateList

        lenlist = range(len(closelist))
        return zip(lenlist,datelist,ema13,ema34,ema55,ema170,ema275\
            ,histlist,sglist,closelist,highlist,lowlist,openlist)

    def getLastDayZipList(self):

        ema13 = self.E13[-1:]
        ema34 = self.E34[-1:]
        ema55 = self.E55[-1:]
        ema170 = self.E170[-1:]
        ema275 = self.E275[-1:]

        histlist = self.hist[-1:]
        sglist = self.signal[-1:]
        closelist = self.close[-1:]
        highlist = self.high[-1:]
        lowlist = self.low[-1:]
        openlist = self.open[-1:]
        datelist = self.dateList[-1:]

        lenlist = range(len(closelist))
        return zip(lenlist,datelist,ema13,ema34,ema55,ema170,ema275\
            ,histlist,sglist,closelist,highlist,lowlist,openlist)