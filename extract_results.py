import csv
import sys
import glob
import os

def extract_data(file_pattern):
    files = glob.glob(file_pattern)
    if not files:
        print("未找到对应的CSV文件。")
        return

    # 获取最新生成的文件
    latest_file = max(files, key=os.path.getctime)
    print(f"正在处理文件: {latest_file}\n")
    print(f"{'平台名称':<20} | {'URL'}")
    print("-" * 60)

    with open(latest_file, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # 根据 CSV 结构修正字段名称
            site = row.get('site', 'N/A')
            url = row.get('url', 'N/A')
            print(f"{site:<20} | {url}")

if __name__ == "__main__":
    # 假设文件在当前目录或结果目录中
    extract_data("results/13076057603_basic_*.csv")
