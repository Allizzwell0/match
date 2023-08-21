#根据已知数据推断此元件处于wiener退化过程状态
#具体理论见文档
#计算其未来寿命及置信度

import math
from scipy.stats import norm
import numpy as np

class Wiener:
    Wear        = [float]          #储存数据
    Time        = [float]
    DeltaWear   = [float]
    DeltaTime   = [float]

    sigma       = 0.0              #拟合参数
    miu         = 0.0

    End_Wear    = 0.0              #计算所需参数
    Reliability = 0.0

    def __init__(self):
      self.Wear        = []
      self.Time        = []
      self.DeltaTime   = []
      self.DeltaWear   = []
      self.sigma       = 0.0
      self.miu         = 0.0
      self.End_Wear    = 0.0
      self.Reliability = 0.0

    #输入数据更新wear和deltawear
    def AddWear(self,wear):
        if(self.Wear):
            self.DeltaWear.append(wear[0] - self.Wear[-1])

        self.Wear += wear

        for index in range(0,len(wear) - 1):
            self.DeltaWear.append(wear[index + 1] - wear[index])
    
    #输入数据更新time和deltatime
    def AddTime(self,time):
        if(self.Time):
            self.DeltaTime.append(time[0] - self.Time[-1])
        self.Time += time

        for index in range(0,len(time) - 1):
            self.DeltaTime.append(time[index + 1] - time[index])


    #参数更新，使用极大似然估计
    def UpdateParams(self):
        sumtime = self.Time[-1] - self.Time[0]

        self.miu = sum(self.DeltaWear)/sumtime

        temp = 0.0
        for index in range(0,len(self.DeltaTime)):
            temp += (self.DeltaWear[index] - self.miu*self.DeltaTime[index])**2
        
        self.sigma = (len(self.DeltaTime) * temp)/((len(self.DeltaTime) - 1) * sumtime)
        self.sigma = math.sqrt(self.sigma)

    #考虑计算wear，加入查找函数，从已有time中找到小于查找值的最近一个下标
    def CheckTime(self,time,start,end):
        mid = (start + end)/2
        if start == end:
            return start
        if self.Time[mid] < time:
            return self.CheckTime(time, mid, end)
        else:
            return self.CheckTime(time, start, mid) 

    #计算给予time下的wear
    def CalWear(self,time):
        if time < self.Time[-1]:
            start = self.CheckTime(time,0,len(self.Time))
        else:
            start = -1
        deltime = time - self.Time[start]
        delwear = deltime*self.miu
        return delwear + self.Wear[start] 
        
       
    #滤波函数
    #首先在此模型中是否需要滤波函数待定
    #目前感觉滤波函数应该是硬件传感器解决
    def filter(self,data,time):
        pass
    
    #清除数据
    def Clear(self):
        self.Time.clear()
        self.Wear.clear()

    #变点监测
    #防止偶然误差，建议输入一组数据而不是一个
    def CheckChange(self,wear = [float],Time = [float]):
        counter = 0

        for index in range(len(Time)):
            newear = self.CalWear(Time[index])
            deltime = Time[index] - self.Time[-1]
            temp = norm.cdf(wear[index],newear,self.sigma * deltime)
            if temp < 0.1 or temp > 0.9:
                counter += 1
            
            
        if counter/len(Time) > 0.5:
            self.Clear()
            self.AddTime(Time)
            self.AddWear(wear)
            self.UpdateParams()
            return 1
        else:
            self.AddTime(Time)
            self.AddWear(wear)
            return 0

    #计算剩余寿命和对应概率
    #给定时间，计算可靠度，即配件寿命达到该时间点的概率
    def CalReliability(self,time):
        #如果给定时间小于目前最近检测时间，则返回100%
        if(time <= self.Time[-1]):
            return 1
        
        deltatime = time - self.Time[-1]
        reliability = 0.0
        temp = self.End_Wear - self.Wear[-1] - self.miu * deltatime
        temp /= self.sigma * math.sqrt(deltatime)
        reliability = norm.cdf(temp)
        return reliability
    
    #给定可靠度，计算该可靠度下对应的最小时间点
    #可靠度是类内参数
    def CalTime(self):
        temp = norm.ppf(self.Reliability)
        deltawear = self.Wear[-1] - self.End_Wear

        #二次函数参数
        coefficients = [self.miu, temp*self.sigma, deltawear]
        #解函数
        roots = np.roots(coefficients)

        #可以推导该二次函数得到结果必为一正一负，故取正值
        deltatime = roots[1]**2
       
        #返回时间点
        return deltatime + self.Time[-1]