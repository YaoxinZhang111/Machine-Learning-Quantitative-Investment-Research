import baostock as bs
import pandas as pd

start_date='2010-07-01'

#### 登陆系统 ####
lg = bs.login()
# 显示登陆返回信息
print('login respond error_code:'+lg.error_code)
print('login respond  error_msg:'+lg.error_msg)
#下载HS300数据
stock_50 = bs.query_sz50_stocks()
stock_300 = bs.query_hs300_stocks()
stock_50r = stock_50.get_data()
stock_300r = stock_300.get_data()
#循环下载数据
ends = pd.DataFrame()
for code in stock_50r["code"]:
    print("Downloading :" + code)
    
    rs = bs.query_history_k_data_plus(code, 
        "date,code,open,high,low,close,volume,turn",
         start_date='2010-01-01', end_date='2022-5-15',
         frequency="d", adjustflag="3")
    
    #### 打印结果集 ####
    data_list = []
    while (rs.error_code == '0') & rs.next():
        # 获取一条记录，将记录合并在一起
            data_list.append(rs.get_row_data())
    result = pd.DataFrame(data_list, columns=rs.fields)
    result['date'] = pd.to_datetime(result['date']).dt.strftime('%Y%m%d')
    #### 结果集输出到csv文件 ####   
    #result.to_csv("D:\\history_A_stock_k_data.csv", index=False)
    ends = pd.concat([ends,result],ignore_index=True) #写入dataframe
ends.to_csv('sz50.csv')   
#### 登出系统 ####
bs.logout()