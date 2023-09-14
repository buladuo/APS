import csv

# 要写入的数据
column1 = ['John', 'Alice', 'Bob']
column2 = [28, 32, 45]
column3 = ['New York', 'San Francisco', 'Chicago']

# 打开CSV文件进行写入
with open('data.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    
    
    # 逐列写入数据
    writer.writerow(['Name'] + column1)
    writer.writerow(['Age'] + column2)
    writer.writerow(['City'] + column3)

print('数据已成功写入CSV文件。')
