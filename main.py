import pandas as pd
from datetime import datetime
import Wiener as wi
import matplotlib.pyplot as plt
from Probability import Fitting

data = pd.read_csv('rul_hrs.csv')

#时间导入
time_data = data.iloc[12:15100,1]
time_format =  "%Y/%m/%d %H:%M"
time_ints = []
for time_str in time_data:
    dt = datetime.strptime(time_str, time_format)
    time_int = (dt - datetime(2018, 4, 1)).total_seconds()//60
    time_ints.append(float(time_int))


#磨损度导入
wear_data = data.iloc[12:15100,52]
wear_floats = []
for wear_str in wear_data:
    wear_floats.append(300.0 - float(wear_str))



#故障率模型测测试
fit = Fitting()

fit.ChangeEndWear(0.95)
x = time_ints
ydata = wear_floats



fit.AddTime(x)
fit.AddWear(ydata)
fit.Normalize(300)           #如果不是归一化后的代码，一定要有这一步

fit.Update()

fit.ShowPicture()

print(fit.CalLeftTime())






#wiener模型测试
'''
Model = wi.Wiener()

Model.End_Wear    = 300.0
Model.Reliability = 0.95

Model.AddTime(time_ints)
Model.AddWear(wear_floats)

Model.UpdateParams()

print(Model.CalReliability(17157))

print(Model.CalTime())


#可视化部分


plt.scatter(time_ints,wear_floats, label='Data')
plt.xlabel('time')
plt.ylabel('wear')
plt.legend()
plt.show()
'''





