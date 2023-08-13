import backtrader as bt
import pandas as pd
import datetime
import pybrain as brain
from pybrain.tools.shortcuts import buildNetwork
from pybrain.tools.customxml import NetworkReader
import matplotlib.pyplot as plt
import matplotlib

HISTORY      = 10                             # 通过前十日数据预测
fnn = buildNetwork(HISTORY, 15, 7, 1)         # 初始化


# 实例化 cerebro
cerebro = bt.Cerebro()

daily_price = pd.read_csv("stock.csv", parse_dates=['date'])

class PandasData_more(bt.feeds.PandasData):
    lines = ('pctChg',)
    params = (('pctChg',-1),)

# 按股票代码，依次循环传入数据
for stock in daily_price['code'].unique():
    # 日期对齐
    data = pd.DataFrame(daily_price['date'].unique(), columns=['date'])  # 获取回测区间内所有交易日
    df = daily_price.query(f"code=='{stock}'")[
        ['date', 'open', 'high', 'low', 'close', 'volume', 'pctChg']]
    data_ = pd.merge(data, df, how='left', on='date')
    data_ = data_.set_index("date")
    # print(data_.dtypes)
    # 缺失值处理：日期对齐时会使得有些交易日的数据为空，所以需要对缺失数据进行填充
    data_.loc[:, ['volume', 'pctChg']] = data_.loc[:, ['volume', 'pctChg']].fillna(0)
    data_.loc[:, ['open', 'high', 'low', 'close']] = data_.loc[:, ['open', 'high', 'low', 'close']].fillna(method='pad')
    data_.loc[:, ['open', 'high', 'low', 'close']] = data_.loc[:, ['open', 'high', 'low', 'close']].fillna(0)
    # 导入数据
    datafeed = PandasData_more(dataname=data_, fromdate=datetime.datetime(2010, 1, 1),
                                   todate=datetime.datetime(2022, 5, 15))
    cerebro.adddata(datafeed, name=stock)  # 通过 name 实现数据集与股票的一一对应
    print(f"{stock} Done !")

print("All stock Done !")


# 回测策略
class TestStrategy(bt.Strategy):
    '''选股策略'''
    params = (('maperiod', 15),
              ('printlog', False),)

    def __init__(self):
        
        print(self.datas[0].lines.getlinealiases())
        self.order_list = []  # 记录以往订单，方便调仓日对未完成订单做处理
        self.buy_stocks_pre = []  # 记录上一期持仓

    def next(self):
        fnn = buildNetwork(HISTORY, 15, 7, 1)
        dt = self.datas[0].datetime.date(0)  # 获取当前的回测时间点
        # 如果是调仓日，则进行调仓操作
        sell_stock = []
        long_list = []
        try:
            
            bucket = []
            for d, i in enumerate(self.datas):
                sample = i.lines.close.get(ago=-1, size=10)
                
                possibility = fnn.activate(sample)
                
                bucket.append((possibility, i))
                if possibility < 0 :
                    sell_stock.append(i._name)
            
            bucket = sorted(bucket, key=lambda x: x[0], reverse=True)
            print (bucket[0][0])
            
            if bucket[0][0] < 0:
                raise Exception('Network Error')

            for a in bucket[:10]:
                if a[0]>0.5:
                    long_list.append(a[1]._name)
            
        except:
            pass  
            
            
        print("--------------{} 为调仓日----------".format(dt))
        # 在调仓之前，取消之前所下的没成交也未到期的订单
        if len(self.order_list) > 0:
            for od in self.order_list:
                self.cancel(od)  # 如果订单未完成，则撤销订单
            self.order_list = []  # 重置订单列表
        # 提取当前调仓日的持仓列表
        
        print('long_list', long_list)  # 打印持仓列表
        # 对现有持仓中，调仓后不再继续持有的股票进行卖出平仓
        
        print('sell_stock', sell_stock)  # 打印平仓列表
        if len(sell_stock) > 0:
            print("-----------对不再持有的股票进行平仓--------------")
            for stock in sell_stock:
                data = self.getdatabyname(stock)
                if self.getposition(data).size > 0:
                    od = self.close(data=data)
                    self.order_list.append(od)  # 记录卖出订单
        # 买入此次调仓的股票：多退少补原则
        print("-----------买入此次调仓期的股票--------------")
        for stock in long_list:
            
            data = self.getdatabyname(stock)
            order = self.buy(data=data, size=1000000)  # 为减少可用资金不足的情况，留 5% 的现金做备用
            self.order_list.append(order)

        self.buy_stocks_pre = long_list  # 保存此次调仓的股票列表

        # 交易记录日志（可省略，默认不输出结果）

    def log(self, txt, dt=None, doprint=False):
        if self.params.printlog or doprint:
            dt = dt or self.datas[0].datetime.date(0)
            print(f'{dt.isoformat()},{txt}')

    def notify_order(self, order):
        # 未被处理的订单
        if order.status in [order.Submitted, order.Accepted]:
            return
        # 已经处理的订单
        if order.status in [order.Completed, order.Canceled, order.Margin]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, ref:%.0f，Price: %.2f, Cost: %.2f, Comm %.2f, Size: %.2f, Stock: %s' %
                    (order.ref,  # 订单编号
                     order.executed.price,  # 成交价
                     order.executed.value,  # 成交额
                     order.executed.comm,  # 佣金
                     order.executed.size,  # 成交量
                     order.data._name))  # 股票名称
            else:  # Sell
                self.log('SELL EXECUTED, ref:%.0f, Price: %.2f, Cost: %.2f, Comm %.2f, Size: %.2f, Stock: %s' %
                         (order.ref,
                          order.executed.price,
                          order.executed.value,
                          order.executed.comm,
                          order.executed.size,
                          order.data._name))


# 初始资金 100,000,000
startcash = 1000000000.0
cerebro.broker.setcash(startcash)
# 佣金，双边各 0.0003
cerebro.broker.setcommission(commission=0.0003)
# 滑点：双边各 0.0001
cerebro.broker.set_slippage_perc(perc=0.0001)

cerebro.addanalyzer(bt.analyzers.TimeReturn, _name='pnl')  # 返回收益率时序数据
cerebro.addanalyzer(bt.analyzers.AnnualReturn, _name='_AnnualReturn')  # 年化收益率
cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='_SharpeRatio')  # 夏普比率
cerebro.addanalyzer(bt.analyzers.DrawDown, _name='_DrawDown')  # 回撤

# 将编写的策略添加给大脑，别忘了 ！
cerebro.addstrategy(TestStrategy, printlog=True)

# 启动回测
result = cerebro.run()
# 从返回的 result 中提取回测结果
strat = result[0]
# 返回日度收益率序列
daily_return = pd.Series(strat.analyzers.pnl.get_analysis())
# 打印评价指标
print("--------------- AnnualReturn -----------------")
print(strat.analyzers._AnnualReturn.get_analysis())
print("--------------- SharpeRatio -----------------")
print(strat.analyzers._SharpeRatio.get_analysis())
print("--------------- DrawDown -----------------")
print(strat.analyzers._DrawDown.get_analysis())
portvalue = cerebro.broker.getvalue()
    
pnl = portvalue / startcash - 1
print(f'净收益率: {round(pnl,2)}%')