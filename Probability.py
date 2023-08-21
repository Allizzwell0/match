import numpy as np
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
from scipy.integrate import quad


#采用磨损度代替故障率，以拟合故障函数和时间关系
class Fitting:
    #内部参数
    __end_wear  = 0.0                                             #预设磨损度上限
    time        = [0.0]                                           #存检测时间
    wear        = [0.0]                                           #存检测磨损度
    TestTime    = 0.0                                             #每次检测时间间隔
    __params    = np.zeros((2), dtype = float)                    #存拟合后的参数
    __startTime = 0.0                                             #开始检测时间，与外界时间统一的接口
    __params_covariance = np.zeros((2,2), dtype = float)          #存拟合后协方差矩阵
   
   

    #定义磨损度与时间函数，输入时间，预测磨损
    @staticmethod
    def wear_time(Time,shape,scale):
        return (shape/scale)*((Time/scale)**(shape - 1))     #weibull分布下的故障率函数
    
    #更新参数
    def Update(self):
        self.params, self.params_covariance = curve_fit(self.wear_time, self.time, self.wear)

    #计算时间
    def CalTime(self,wear):
        return self.params[1]*((wear*self.params[1]/self.params[0])**(1/(self.params[0] - 1)))
        
    #根据时间计算故障率
    def CalWear(self, time):
        return (self.params[0]/self.params[1])*((time/self.params[1])**(self.params[0] - 1))

    #根据拟合得到函数计算剩余时间
    #当前时间为理论和实际的算术平均
    def CalLeftTime(self):
        endtime = self.CalTime(self.end_wear)
        nowtime = self.time[-1] + self.CalTime(self.wear[-1])
        nowtime /= 2
        return endtime - nowtime
    

    #提供两个时间节点，根据拟合参数求其平均故障率
    def CalAveWear(self,startime,endtime):
        def integrand(x):
            return (self.params[0]/self.params[1])*((x/self.params[1])**(self.params[0] - 1))
        
        result, error = quad(integrand, startime, endtime)
        return result/(startime - endtime)

    #判断是否出现变点
    #如果输入数据属于变点，则自动更新，返回true
    #如果无变点，返回false
    def CheckChange(self,wear,Time):
        counter = 0
        for index in range(len(Time)):
            newear = self.CalWear(Time[index])
            if wear[index] - newear > 0.1:
                counter += 1
        if counter/len(Time) > 0.5:
            self.Clear()
            self.AddTime(Time)
            self.AddWear(wear)
            self.Update()
            return 1
        else:
            return 0
        
    #构造函数
    def __init__(self,end_wear = 0.0):
        self.end_wear = end_wear
        end_wear      = 0.0             
        self.time     = []                 
        self.wear     = []                  
        self.params   = []              
        self.params_covariance = []   
    
    #更改end_wear
    def ChangeEndWear(self,endwear):
        self.end_wear = endwear

    #添加wear
    def AddWear(self,wear):
        self.wear += wear

    #添加time
    def AddTime(self,time):
        self.time += time
    
    #更改testtime
    def SetTestTime(self,testime):
        self.TestTime = testime

    #清空数据
    def Clear(self):
        self.wear.clear()
        self.time.clear()

    #测试用函数，用于绘图
    def ShowPicture(self):

        x = np.linspace(min(self.time), max(self.time), 100)
        y = self.CalWear(x)

        plt.scatter(self.time, self.wear, label='Data')
        plt.plot(x, y, color='red', label='fit')
        plt.xlabel('time')
        plt.ylabel('wear')
        plt.legend()
        plt.show()

#由于输入磨损度可能不处于0-1，加入归一化函数
    def Normalize(self,maxvalue = 0.0):
        minvalue = min(self.wear)
        rangevalue = maxvalue - minvalue

        temp = [(x - minvalue) / rangevalue for x in self.wear]
        self.wear = temp


#测试代码
'''
fit = Fitting()

fit.ChangeEndWear(1)
x = list(range(0,4250,250))
ydata = [0,0.47,0.93,2.11,2.72,3.51,4.34,4.91,5.48,5.99,6.72,7.13,8.00,8.92,9.49,9.87,10.94]



fit.AddTime(x)
fit.AddWear(ydata)
fit.Normalize(11)           #如果不是归一化后的代码，一定要有这一步

fit.Update()

fit.ShowPicture()

print(fit.CalLeftTime())
'''
#end

#此类用于整合仓库中备件的所有信息
#各种费用、下次备件到达时间由外部确定
#剩余时间由故障率函数拟合
#损坏程度即下次配件到达前平均故障率
class Item:
    #暂定用于分类的参数
    __StorCost   = 0.0             #储存所需费用，以天计
    __PurCost    = 0.0             #购买所需费用，以件计
    __TestCost   = 0.0             #检测所需费用，以次计
    __ChangeCost = 0.0             #更换所需费用，单次单件
    __Lost       = 0.0             #损坏造成损失，单次单件
    __TransCost  = 0.0             #运输所需费用，如果仓库储备充足，此值为0
    __UseTime    = 0.0             #配件已使用时间

    __ArriveTime = 0.0             #下次备件到达时间，即运输时间
    __LeftTime   = 0.0             #由上述故障函数拟合得到的剩余使用时间
    __Wear       = 0.0             #损坏程度，下次更换前的平均故障率

    #构造函数
    def __init__(self):
        self.StorCost   = 0.0             #储存所需费用，以天计
        self.PurCost    = 0.0             #购买所需费用，以件计
        self.TestCost   = 0.0             #检测所需费用，以次计
        self.ChangeCost = 0.0             #更换所需费用，单次单件
        self.Lost       = 0.0             #损坏造成损失，单次单件
        self.TransCost  = 0.0             #运输所需费用，如果仓库储备充足，此值为0
        self.UseTime    = 0.0             #配件已使用时间

        self.ArriveTime = 0.0             #下次备件到达时间，即购买日期加运输时间
        self.LeftTime   = 0.0             #由上述故障函数拟合得到的剩余使用时间
        self.Wear       = 0.0             #损坏程度，此处可理解为最终时间时的故障率
    
    #各个参数的更改函数
    def SetStorCost(self,storcost):
        self.StorCost = storcost
    
    def SetPurCost(self,purcost):
        self.PurCost = purcost

    def SetTestCost(self,testcost):
        self.TestCost = testcost
    
    def SetChangeCost(self, changecost):
        self.ChangeCost = changecost

    def SetLost(self, lost):
        self.Lost = lost

    def SetTransCost(self,transcost):
        self.TransCost = transcost

    def SetUseTime(self,usetime):
        self.UseTime = usetime

    def SetArriveTime(self, arrivetime):
        self.ArriveTime = arrivetime

    def SetLeftTime(self, leftime):
        self.LeftTime = leftime

    def SetWear(self,wear):
        self.Wear = wear

    #计算最终替换的损失期望
    def CalDelayCost(self):
        cost = self.Wear * self.LeftTime * self.Lost
        cost += self.StorCost * (self.LeftTime - self.ArriveTime)
        return cost
    
    #计算立刻替换的损失期望
    #即配件平均每日花费
    def CalImCost(self):
        cost = self.PurCost + self.ChangeCost + self.TransCost
        cost = cost * (self.LeftTime/(self.LeftTime + self.UseTime)) * (1 - self.Wear)
        return cost
    
    #决定此时是否需要更换配件
    def DecideChange(self):
        DelayCost = self.CalDelayCost()
        ImCost    = self.CalImCost()
        return ImCost < DelayCost
    
#仓库类
#主要作用为根据目前的数据得到单品的最大存量和最小存量
class Warehouse:
    #私有变量
    __Fittings  = [Fitting]              #列表用于储存当前所有配件信息
    __PreWear   = 0.0             #一个预计磨损度，达到此水平则预定备件
    __MinNum    = 0               #最小值
    __MaxNum    = 0               #最大值
    __ChangeNum = 0               #此时需要替换配件数量
    __OrderNum  = 0               #不需要替换但是预定配件数量

    #构造函数
    def __init__(self):
        self.__PreWear   = 0.0
        self.__MinNum    = 0
        self.__MaxNum    = 0
        self.__ChangeNum = 0
        self.__OrderNum  = 0
    
    #用于给仓库中增加配件
    #参数为一个Fitting对象
    def AddItem(self, Item:Fitting): 
        self.__Fittings.append(Item)
    
    #其余几个参数的改变
    def SetPreWear(self,prewear):
        self.__PreWear = prewear

    def SetMinNum(self,minum):
        self.__MinNum = minum

    def SetMaxNum(self,maxnum):
        self.__MaxNum = maxnum

    def SetChangeNum(self, changenum):
        self.__ChangeNum = changenum

    def SetOrderNum(self,ordernum):
        self.__OrderNum = ordernum

    #计算存量
    #minnum = ordernum + changenum
    #maxnum = minum + 其余不需更换配件在下次检测前可能损坏期望
    def UpdateNum(self):
        counter = 0.0
        for fit in self.__Fittings:
            fit.Update()          #先更新参数
            wear = fit.CalWear(fit.time[-1] + fit.TestTime)
            if wear < self.__PreWear:
                counter += fit.TestTime * fit.CalAveWear(fit.time[-1], fit.TestTime)
            elif wear < fit.__end_wear:
                self.__OrderNum  += 1
            else:
                self.__ChangeNum += 1
        self.__MinNum = self.__OrderNum  + self.__ChangeNum
        self.__MaxNum = int(counter + 1) + self.__MinNum      #期望向上取整