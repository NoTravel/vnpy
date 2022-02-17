
class MacdArea:
    
    type=str("")#red=红,green=绿
    beginIndex=int(0)
    endIndex=int(0)
    barPrice=float(0)
    yellowPrice=float(0)
    area=float(0)
    num=int(0)#柱子的数量

    highPrice=float(0.0)
    lowPrice=float(0.0)

    greatE34Tag=False
    lessE34Tag=False

    initDate=None
    confirmDate=None

    #绿柱最低价时均线值,或红柱最高价时的均线值,日线
    e13=float(0)
    e34=float(0)
    e55=float(0)

    def __str__(self):
        ss=[self.type,str(self.initDate),str(self.confirmDate),str(self.beginIndex),str(self.endIndex),str(self.barPrice)\
            ,str(self.yellowPrice),str(self.area) ,str(self.highPrice),str(self.lowPrice),str(self.greatE34Tag),str(self.lessE34Tag)\
            ,str(self.e13),str(self.e34),str(self.e55),str(self.num)]
        return ",".join(ss)

class OpenData:
    bs=str("")
    stop_price=float(0.0)
    vol=int(0)
    weekTrendLimitPrice=float(0.0)
    #weekRvTrendPrice=float(0.0)
    weekRvTrendPrice=float(0.0)
    dayTrendLimitPrice=float(0.0)
    foldBeginDate=None

    def __str__(self):
        return ",".join([self.bs,"止损价="+str(self.stop_price),str(self.vol),str(self.weekTrendLimitPrice)\
           ,str(self.weekRvTrendPrice),str(self.dayTrendLimitPrice),str(self.foldBeginDate)])

class WeekData:
    preTrend=int(0)
    cTrend=int(0)
    trendNewLimitFlag=False
    high=float(0.0)
    low=float(0.0)

    def __init__(self,pretrend,ctrend,limitflag,high,low):
        self.preTrend=pretrend
        self.cTrend=ctrend
        self.trendNewLimitFlag=limitflag
        self.high=high
        self.low=low
    def __str__(self):
        return ",".join([str(self.preTrend),str(self.cTrend),str(self.trendNewLimitFlag),str(self.high),str(self.low)])

class EmaData:
    e13=float(0.0)
    e34=float(0.0)
    e55=float(0.0)
    e170=float(0.0)
    e275=float(0.0)

    def __init__(self, e13,e34,e55,e170,e275):
        self.e13=e13
        self.e34=e34
        self.e55=e55
        self.e170=e170
        self.e275=e275

    def __str__(self):
        return ",".join([str(self.e13),str(self.e34),str(self.e55),str(self.e170),str(self.e275)])


class BackTagData:
    flag=int(0)
    eValue=float(0.0)
    high=float(0.0)
    low=float(0.0)

    def __init__(self, fg=int(0),ev=float(0.0),hi=float(0.0),lw=float(0.0)):
        self.flag=fg
        self.eValue=ev
        self.high=hi
        self.low=lw

    def __str__(self):
        return ",".join(["BackTagData",str(self.flag),str(self.eValue),str(self.high),str(self.low)])

    def reInit(self):
        self.flag=0
        self.eValue=0.0
        self.high=0.0
        self.low=0.0

    def set(self,fg,ev,hi,lw):
        self.flag=fg
        self.eValue=ev
        self.high=hi
        self.low=lw

class DepartData:
    flag=int(0)
    high=float(0.0)
    low=float(0.0)

    def __init__(self, fg=int(0),hi=float(0.0),lw=float(0.0)):
        self.flag=fg
        self.high=hi
        self.low=lw

    def __str__(self):
        return ",".join(["DepartData",str(self.flag),str(self.high),str(self.low)])

    def reInit(self):
        self.flag=0
        self.high=0.0
        self.low=0.0

    def set(self,fg,hi,lw):
        self.flag=fg
        self.high=hi
        self.low=lw

class MacdTwoLimitData:
    limitPrice=float(0.0)
    count=int(0)

class LastBarData:
    open:float(0.0)
    high:float(0.0)
    close:float(0.0)
    low:float(0.0)
    time:None

    def __init__(self, open,high,close,low,time):
        self.open=open
        self.high=high
        self.close=close
        self.low=low
        self.time=time

    def __str__(self):
        return ",".join(["LastBarData",str(self.open),str(self.high),str(self.close),str(self.low),str(self.time)])
