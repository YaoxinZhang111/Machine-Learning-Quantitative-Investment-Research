from turtle import shape
import pybrain 
import pandas as pd
import os
import sys
files_path = "./datas/"


HISTORY      = 10                             # 通过前十日数据预测

from pybrain.datasets import SupervisedDataSet
### 建立数据集
def make_training_data():
    ds = SupervisedDataSet(HISTORY, 1)
    '''for stock in os.listdir(files_path):
        modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
        datapath = os.path.join(modpath, files_path + stock)
        print(datapath)
    
        raw_data = pd.read_csv(datapath)'''
    raw_data = pd.read_csv('stock.csv')    
    plist = list(raw_data.iloc[:,5])
    for idx in range(1, len(plist) - HISTORY - 1):
        sample = []
        for i in range(HISTORY):
            sample.append(plist[idx + i - 1] / plist[idx + i] - 1)
        answer = plist[idx + HISTORY - 1] / plist[idx + HISTORY] - 1

        ds.addSample(sample, answer)
    return ds

### 建立测试集
def make_testing_data():
    ds = SupervisedDataSet(HISTORY, 1)
    
    raw_data = pd.read_csv('sh.600519.csv')
    plist = list(raw_data.iloc[1875:,5])
    for idx in range(1, len(plist) - HISTORY - 1):
        sample = []
        for i in range(HISTORY):
            sample.append(plist[idx + i - 1] / plist[idx + i] - 1)
        answer = plist[idx + HISTORY - 1] / plist[idx + HISTORY] - 1

        ds.addSample(sample, answer)
    return ds

from pybrain.supervised.trainers import BackpropTrainer
### 构造BP训练实例
def make_trainer(net, ds, momentum = 0.1, verbose = True, weightdecay = 0.01): # 网络, 训练集, 训练参数
    trainer = BackpropTrainer(net, ds, momentum = momentum, verbose = verbose, weightdecay = weightdecay)
    return trainer

### 开始训练
def start_training(trainer, epochs = 15): # 迭代次数
    trainer.trainEpochs(epochs)

def start_testing(net, dataset):
    return net.activateOnDataset(dataset)

### 保存参数
from pybrain.tools.customxml import NetworkWriter
def save_arguments(net):
    NetworkWriter.writeToFile(net, 'huge_data.csv')
    print ('Arguments save to file net.csv')

from pybrain.tools.shortcuts import buildNetwork
### 初始化神经网络
fnn = buildNetwork(HISTORY, 15, 7, 1)

training_dataset = make_training_data()
testing_dataset  = make_testing_data()
trainer = make_trainer(fnn, training_dataset)
start_training(trainer, 5)
save_arguments(fnn)
print (start_testing(fnn, testing_dataset))
