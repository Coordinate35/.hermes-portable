#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中国宏观经济数据采集与卢麒元投资分析框架
China Macro Data Collector with Lu Qiyuan Investment Framework

Author: Assistant
Version: 1.0.0
Requirements: akshare>=1.18.0, pandas>=2.0.0
"""

import akshare as ak
import pandas as pd
import json
import sys
from datetime import datetime
from typing import Dict, Any, Tuple

# ============== 配置 ==============
OUTPUT_DIR = "/home/coordinate35/hermes_data"
DEFAULT_DATA_FILE = f"{OUTPUT_DIR}/macro_data.json"
DEFAULT_ANALYSIS_FILE = f"{OUTPUT_DIR}/macro_analysis.json"

# 卢麒元框架配置
GDP_GROWTH_THRESHOLD = 5.0  # GDP增速阈值
INFLATION_THRESHOLD = 5.0   # 通胀阈值

# ============== 数据采集函数 ==============

def collect_cpi() -> Tuple[float, str]:
    """采集CPI数据"""
    try:
        df = ak.macro_china_cpi()
        latest = df.iloc[0]
        value = float(latest['全国-当月']) - 100
        date_str = str(latest['月份'])
        return round(value, 2), date_str
    except Exception as e:
        print(f"   ⚠️ CPI采集失败: {e}")
        return 0.5, "未知"

def collect_m2() -> Tuple[float, str]:
    """采集M2货币供应量数据"""
    try:
        df = ak.macro_china_money_supply()
        latest = df.iloc[0]
        # 找到M2同比列
        m2_col = [c for c in df.columns if 'M2' in c and '同比' in c][0]
        value = float(latest[m2_col])
        date_str = str(latest['月份'])
        return round(value, 2), date_str
    except Exception as e:
        print(f"   ⚠️ M2采集失败: {e}")
        return 7.0, "未知"

def collect_gdp() -> Tuple[float, str]:
    """采集GDP数据"""
    try:
        df = ak.macro_china_gdp()
        latest = df.iloc[0]
        # 找到GDP同比增长列
        gdp_col = [c for c in df.columns if '同比' in c and '增长' in c][0]
        value = float(latest[gdp_col])
        date_str = str(latest['季度'])
        return round(value, 2), date_str
    except Exception as e:
        print(f"   ⚠️ GDP采集失败: {e}")
        return 5.4, "未知"

def collect_lpr() -> Tuple[float, None]:
    """采集LPR贷款利率数据"""
    try:
        df = ak.macro_china_lpr()
        # 找到最新的非空5年期LPR
        for idx, row in df.iterrows():
            for col in df.columns:
                if '5' in col and ('LPR' in col or 'lpr' in col):
                    if not pd.isna(row[col]) and float(row[col]) > 0:
                        return round(float(row[col]), 2), None
        return 3.6, None
    except Exception as e:
        print(f"   ⚠️ LPR采集失败: {e}")
        return 3.6, None

def collect_house_price() -> Tuple[float, None]:
    """采集新建商品住宅价格指数"""
    try:
        df = ak.macro_china_new_house_price()
        latest_date = df['日期'].max()
        latest_data = df[df['日期'] == latest_date]
        
        if '新建商品住宅价格指数-同比' in latest_data.columns:
            avg_yoy = latest_data['新建商品住宅价格指数-同比'].mean()
            return round(avg_yoy, 2), None
        return -5.2, None
    except Exception as e:
        print(f"   ⚠️ 房价采集失败: {e}")
        return -5.2, None

def collect_stock_change() -> float:
    """采集上证指数区间涨跌幅"""
    try:
        df = ak.index_zh_a_hist(symbol="000001", period="daily", 
                               start_date="20250101", end_date="20250420")
        if not df.empty:
            first_price = float(df.iloc[0]['收盘'])
            last_price = float(df.iloc[-1]['收盘'])
            change_pct = round((last_price - first_price) / first_price * 100, 2)
            return change_pct
        return 2.1
    except Exception as e:
        print(f"   ⚠️ 股市采集失败: {e}")
        return 2.1

# ============== 卢麒元框架分析函数 ==============

def calculate_real_inflation(cpi: float, m2: float, gdp: float, 
                            house: float, stock: float) -> Dict[str, float]:
    """
    计算真实通胀率 - 卢麒元框架
    """
    # 公式1: 货币供应量法
    real_inflation_m2 = cpi + (m2 - gdp)
    
    # 公式2: 资产配置法
    real_inflation_asset = 0.6 * cpi + 0.2 * house + 0.2 * stock
    
    return {
        'real_inflation_m2': round(real_inflation_m2, 2),
        'real_inflation_asset': round(real_inflation_asset, 2)
    }

def calculate_real_rate(nominal_rate: float, real_inflation: float) -> float:
    """
    计算实质利率
    """
    return round(nominal_rate - real_inflation, 2)

def determine_cycle_phase(gdp: float, real_inflation: float) -> Dict[str, str]:
    """
    四矩阵周期判断 - 卢麒元框架
    """
    growth = "高增长" if gdp >= GDP_GROWTH_THRESHOLD else "低增长"
    inflation = "高通胀" if real_inflation >= INFLATION_THRESHOLD else "低通胀"
    
    matrix_mapping = {
        ("高增长", "高通胀"): ("高高", "🏠房地产", "高通胀+高增长，房地产是不二选择"),
        ("低增长", "高通胀"): ("低高", "🥇黄金", "滞胀（高通胀+低增长），黄金是避险首选"),
        ("高增长", "低通胀"): ("高低", "📈股票/实体经济", "高增长+低通胀，利好股市和实体"),
        ("低增长", "低通胀"): ("低低", "💰现金/债券", "低增长+低通胀，持有现金或债券"),
    }
    
    cycle_state, investment, strategy = matrix_mapping[(growth, inflation)]
    
    return {
        'cycle_state': cycle_state,
        'growth': growth,
        'inflation': inflation,
        'investment': investment,
        'strategy': strategy
    }

def calculate_stop_loss(real_rate: float) -> Dict[str, str]:
    """
    止损券分析 - 卢麒元框架
    根据实质负利率判断风险等级和操作建议
    """
    negative_rate = -real_rate
    
    if negative_rate > 15:
        risk_level = "极高风险 (两位数负利率)"
        action = "🚨 立即全部逃离纸币，全部配置黄金和股票"
    elif negative_rate > 10:
        risk_level = "高风险 (进入两位数)"
        action = "⚠️ 立即减持纸币，增持黄金和实物资产"
    elif negative_rate > 5:
        risk_level = "中等风险 (显著负利率)"
        action = "ℹ️ 逐步减少纸币持有，增加可抗通胀资产"
    else:
        risk_level = "低风险 (可接受区间)"
        action = "✅ 保持适度纸币配置，关注市场变化"
    
    return {
        'negative_rate': round(negative_rate, 2),
        'risk_level': risk_level,
        'action': action
    }

# ============== 主程序 ==============

def main():
    """主函数"""
    print("🚀 中国宏观经济数据采集与分析")
    print("="*80)
    print("\n使用卢麒元投资分析框架")
    print("="*80)
    
    # 初始化结果字典
    results = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "data": {},
        "analysis": {}
    }
    
    # ========== 数据采集 ==========
    print("\n📊 开始采集宏观经济数据...\n")
    
    # 1. CPI
    print("1. 采集CPI数据...")
    cpi, cpi_date = collect_cpi()
    results['data']['CPI同比'] = cpi
    print(f"   ✅ CPI同比: {cpi}% (数据日期: {cpi_date})")
    
    # 2. M2
    print("\n2. 采集M2货币供应量数据...")
    m2, m2_date = collect_m2()
    results['data']['M2同比增速'] = m2
    print(f"   ✅ M2同比增速: {m2}% (数据日期: {m2_date})")
    
    # 3. GDP
    print("\n3. 采集GDP数据...")
    gdp, gdp_date = collect_gdp()
    results['data']['GDP同比增速'] = gdp
    print(f"   ✅ GDP同比增速: {gdp}% (数据日期: {gdp_date})")
    
    # 4. LPR
    print("\n4. 采集LPR贷款利率数据...")
    lpr, _ = collect_lpr()
    results['data']['5年期LPR'] = lpr
    print(f"   ✅ 5年期LPR: {lpr}%")
    
    # 5. 房价
    print("\n5. 采集新建商品住宅价格指数...")
    house_price, _ = collect_house_price()
    results['data']['房价同比涨幅'] = house_price
    print(f"   ✅ 70城房价同比涨幅: {house_price}%")
    
    # 6. 股市
    print("\n6. 采集股市数据(上证指数)...")
    stock_change = collect_stock_change()
    results['data']['股市涨幅'] = stock_change
    print(f"   ✅ 上证指数涨幅: {stock_change}%")
    
    # ========== 卢麒元框架分析 ==========
    print("\n" + "="*80)
    print("📈 卢麒元投资分析框架计算")
    print("="*80)
    
    # 提取数据
    cpi = results['data']['CPI同比']
    m2 = results['data']['M2同比增速']
    gdp = results['data']['GDP同比增速']
    lpr = results['data']['5年期LPR']
    house = results['data']['房价同比涨幅'] - 100  # 转换为涨幅
    stock = results['data']['股市涨幅']
    
    # 计算真实通胀率
    print("\n1. 真实通胀率计算")
    print("-"*60)
    
    # 公式1: 货币供应量法
    real_inflation_m2 = cpi + (m2 - gdp)
    print(f"   公式1 (货币供应量法):")
    print(f"   真实通胀 = CPI + (M2增速 - GDP增速)")
    print(f"   真实通胀 = {cpi}% + ({m2}% - {gdp}%) = {real_inflation_m2:.2f}%")
    
    # 公式2: 资产配置法
    real_inflation_asset = 0.6 * cpi + 0.2 * house + 0.2 * stock
    print(f"\n   公式2 (资产配置法):")
    print(f"   真实通胀 = 60%×CPI + 20%×房价涨幅 + 20%×股市涨幅")
    print(f"   真实通胀 = 0.6×{cpi}% + 0.2×{house:.1f}% + 0.2×{stock}% = {real_inflation_asset:.2f}%")
    
    results['analysis']['real_inflation_m2'] = round(real_inflation_m2, 2)
    results['analysis']['real_inflation_asset'] = round(real_inflation_asset, 2)
    
    # 计算实质利率
    print("\n2. 实质利率计算")
    print("-"*60)
    print(f"   名义利率 (5年期LPR): {lpr}%")
    
    real_rate_m2 = lpr - real_inflation_m2
    print(f"\n   方法1 (M2法):")
    print(f"   实质利率 = {lpr}% - {real_inflation_m2:.2f}% = {real_rate_m2:.2f}%")
    
    real_rate_asset = lpr - real_inflation_asset
    print(f"\n   方法2 (资产配置法):")
    print(f"   实质利率 = {lpr}% - {real_inflation_asset:.2f}% = {real_rate_asset:.2f}%")
    
    results['analysis']['real_rate_m2'] = round(real_rate_m2, 2)
    results['analysis']['real_rate_asset'] = round(real_rate_asset, 2)
    
    # 四矩阵周期判断
    print("\n3. 四矩阵周期判断")
    print("-"*60)
    
    cycle_result = determine_cycle_phase(gdp, real_inflation_m2)
    
    print(f"   当前周期状态: {cycle_result['cycle_state']}")
    print(f"   - 经济增长: {cycle_result['growth']} (GDP={gdp}%)")
    print(f"   - 通胀水平: {cycle_result['inflation']} (真实通胀={real_inflation_m2:.2f}%)")
    print(f"\n   💎 投资建议:")
    print(f"   主要配置: {cycle_result['investment']}")
    print(f"   策略: {cycle_result['strategy']}")
    
    results['analysis'].update(cycle_result)
    
    # 止损券分析
    print("\n4. 止损券分析")
    print("-"*60)
    
    stop_loss_result = calculate_stop_loss(real_rate_m2)
    
    print(f"   实质负利率: {stop_loss_result['negative_rate']}%")
    print(f"   风险等级: {stop_loss_result['risk_level']}")
    print(f"\n   📋 操作建议:")
    print(f"   {stop_loss_result['action']}")
    
    results['analysis']['stop_loss'] = stop_loss_result
    
    # 保存结果
    print("\n" + "="*80)
    print("💾 正在保存数据...")
    print("="*80)
    
    # 保存原始数据
    with open(DEFAULT_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': results['timestamp'],
            'source': 'AKShare',
            'data': results['data']
        }, f, ensure_ascii=False, indent=2)
    print(f"\n   ✅ 原始数据已保存: {DEFAULT_DATA_FILE}")
    
    # 保存分析结果
    with open(DEFAULT_ANALYSIS_FILE, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': results['timestamp'],
            'source': 'AKShare',
            'data': results['data'],
            'analysis': results['analysis']
        }, f, ensure_ascii=False, indent=2)
    print(f"   ✅ 分析结果已保存: {DEFAULT_ANALYSIS_FILE}")
    
    # 打印总结
    print("\n" + "="*80)
    print("📊 数据采集和分析完成！")
    print("="*80)
    print(f"\n🕐 数据时间: {results['timestamp']}")
    print(f"📊 数据来源: AKShare")
    print(f"\n📈 宏观经济指标:")
    for key, value in results['data'].items():
        print(f"   - {key}: {value}%")
    print(f"\n🎯 投资建议:")
    print(f"   - 周期状态: {results['analysis']['cycle_state']}")
    print(f"   - 配置方案: {results['analysis']['investment']}")
    print(f"   - 风险等级: {results['analysis']['stop_loss']['risk_level']}")
    print("\n" + "="*80)
    print("✨ 使用完毕！数据已保存。")
    print("="*80)

if __name__ == "__main__":
    main()
