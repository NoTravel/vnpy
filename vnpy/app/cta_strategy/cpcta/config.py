import configparser
import os
from vnpy.app.ssd_logger.ProcessLogger import*

class RatioConfig:

    ratio={}
    fund={}

    def __init__(self, *args, **kwargs):
        self.readMarginRatio()
        return super().__init__(*args, **kwargs)

    def readMarginRatio(self):
        try:
            filepath=os.path.dirname(os.path.abspath(__file__))
            cf=configparser.ConfigParser()
            cf.read(filepath+"/cp_config.ini",encoding="utf-8")

            items=cf.items("margin_ratio")
            #保证金比率
            for index in items:
                self.ratio[index[0]]=float(index[1])
            #资金及比率
            items=cf.items("fund")
            for index in items:
                self.fund[index[0]]=float(index[1])

        except Exception:
            vnLogger("读取cp配置文件失败")
            print("读取cp配置文件失败")
        else:
            vnLogger("读取cp配置文件成功",str(self.ratio),str(self.fund))
            print("读取cp配置文件成功,"+str(self.ratio)+str(self.fund))

    def getMarginRatio(self,variety:str):
        return self.ratio.get(variety,0.1)

    def getFundRatio(self):
        total=self.fund.get("total",1000000)
        ratio=self.fund.get("ratio",0.1)

        return total,ratio

    def getVarietyFund(self):
        variety_fund=self.fund.get("variety_fund",0);
        return variety_fund;
    
pubConfig=RatioConfig()
