import backtrader as bt
import os
import sys
import datetime
import pybrain as brain
from pybrain.tools.shortcuts import buildNetwork
from pybrain.tools.customxml import NetworkReader
import matplotlib.pyplot as plt
import matplotlib

matplotlib.rcParams['font.family'] = 'SimHei'

matplotlib.rcParams['font.size'] = 10

matplotlib.rcParams['axes.unicode_minus']=False
from pylab import mpl
mpl.rcParams['font.sans-serif']=['SimHei']

HISTORY      = 10                             # 通过前十日数据预测
fnn = buildNetwork(HISTORY, 15, 7, 1)         # 初始化神经网络


class TestStrategy(bt.Strategy):
    """
    继承并构建自己的bt策略
    """

    def log(self, txt, dt=None, doprint=False):
        ''' 日志函数，用于统一输出日志格式 '''
        if doprint:
            dt = dt or self.datas[0].datetime.date(0)
            print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):

        # 初始化相关数据
        self.dataclose = self.datas[0].close
        self.order = None
        self.buyprice = None
        self.buycomm = None
        fnn = NetworkReader.readFrom('huge_data.csv')
        
       

    def notify_order(self, order):
        """
        订单状态处理

        Arguments:
            order {object} -- 订单状态
        """
        if order.status in [order.Submitted, order.Accepted]:
            # 如订单已被处理，则不用做任何事情
            return

        # 检查订单是否完成
        if order.status in [order.Completed]:
            if order.isbuy():
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            self.bar_executed = len(self)

        # 订单因为缺少资金之类的原因被拒绝执行
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        # 订单状态处理完成，设为空
        self.order = None

    def notify_trade(self, trade):
        """
        交易成果
        
        Arguments:
            trade {object} -- 交易状态
        """
        if not trade.isclosed:
            return

        # 显示交易的毛利率和净利润
        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm), doprint=True)

    def next(self):
        ''' 下一次执行 '''
        fnn = buildNetwork(HISTORY, 15, 7, 1)
        try:
            
            sample = self.datas[0].lines.close.get(ago=0, size=10)
            print(sample)
            possibility = fnn.activate(sample)
            print(possibility)   
            
            # 记录收盘价
            self.log('Close, %.2f' % self.dataclose[0])

            # 是否正在下单，如果是的话不能提交第二次订单
            if self.order:
                return

            # 是否已经买入
            if not self.position:
                # 还没买，如果 MA5 > MA10 说明涨势，买入
                if possibility>2:
                    self.order = self.buy()
            else:
                # 已经买了，如果 MA5 < MA10 ，说明跌势，卖出
                if possibility<-2:
                    self.order = self.sell()
            
        except:
            pass
    def stop(self):
        self.log(u'(金叉死叉有用吗) Ending Value %.2f' %
                 (self.broker.getvalue()), doprint=True)


if __name__ == '__main__':

    # 初始化模型
    cerebro = bt.Cerebro()

    # 构建策略
    strats = cerebro.addstrategy(TestStrategy)
    # 每次买100股
    cerebro.addsizer(bt.sizers.FixedSize, stake=1000)

    # 加载数据到模型中
    data = bt.feeds.GenericCSVData(
        dataname='sh.600048.csv',
        fromdate=datetime.datetime(2010, 1, 1),
        todate=datetime.datetime(2020, 1, 1),
        dtformat='%Y%m%d',
        datetime=0,
        open=2,
        high=3,
        low=4,
        close=5,
        volume=6
    )
    cerebro.adddata(data)

    # 设定初始资金和佣金
    startcash = 1000000.0
    cerebro.broker.setcash(startcash)
    cerebro.broker.setcommission(0.005)

    # 策略执行前的资金
    print('启动资金: %.2f' % cerebro.broker.getvalue())
    
    # 策略执行
    cerebro.run()
    portvalue = cerebro.broker.getvalue()
    
    pnl = portvalue - startcash
    print(f'净收益: {round(pnl,2)}')
    cerebro.plot()