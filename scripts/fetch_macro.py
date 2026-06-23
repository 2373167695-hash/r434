"""
宏观数据自动采集脚本（修复版）
使用 AKShare 获取最新宏观经济指标
关键修复：数据格式适配 + 逐函数容错 + 不过度转换
"""
import json
import sys
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def safe_float(val):
    if val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def safe_date(raw):
    """将各种日期格式统一为 YYYY-MM"""
    s = str(raw).strip()
    m = __import__("re").match(r"(\d{4})[^\d]*(\d{1,2})", s)
    if m:
        return f"{m.group(1)}-{int(m.group(2)):02d}"
    return None


def fetch_usdcny_middle():
    """人民币对美元汇率中间价"""
    try:
        import akshare as ak
        df = ak.currency_boc_safe()
        if df is None or df.empty:
            return []
        
        result = []
        for _, row in df.tail(12).iterrows():
            d = safe_date(row.get("日期", ""))
            val = safe_float(row.get("美元", 0))
            if d and val and val > 0:
                # BOC data: 100USD = X RMB, so actual rate = X/100
                if val > 50:
                    val = round(val / 100, 4)
                result.append({"date": d, "value": val, "note": "中国银行牌价"})
        
        if result:
            print(f"  [USD/CNY] 获取到 {len(result)} 个数据点: {result[-1]['date']}={result[-1]['value']}")
        return result
    except Exception as e:
        print(f"  [USD/CNY] 失败: {e}")
        return []


def fetch_cpi():
    """CPI 居民消费价格指数"""
    try:
        import akshare as ak
        df = ak.macro_china_cpi_monthly()
        if df is None or df.empty:
            return []
        
        result = []
        cols = list(df.columns)
        val_col = None
        for c in cols:
            if "全国" in str(c) or "当月" in str(c):
                val_col = c
                break
        
        if not val_col and len(cols) > 1:
            val_col = cols[1]
        
        for _, row in df.tail(12).iterrows():
            d = safe_date(row.get("日期", row.get(cols[0], "")))
            val = safe_float(row.get(val_col, 0)) if val_col else None
            if d and val is not None:
                result.append({"date": d, "value": round(val, 1)})
        
        if result:
            print(f"  [CPI] {len(result)}个点: {result[-1]['date']}={result[-1]['value']}%")
        return result
    except Exception as e:
        print(f"  [CPI] 失败: {e}")
        return []


def fetch_ppi():
    """PPI 工业生产者出厂价格指数"""
    try:
        import akshare as ak
        df = ak.macro_china_ppi_yearly()
        if df is None or df.empty:
            return []
        
        result = []
        cols = list(df.columns)
        val_col = cols[1] if len(cols) > 1 else None
        
        for _, row in df.tail(12).iterrows():
            d = safe_date(row.get("日期", row.get(cols[0], "")))
            val = safe_float(row.get(val_col, 0)) if val_col else None
            if d and val is not None:
                result.append({"date": d, "value": round(val, 1)})
        
        if result:
            print(f"  [PPI] {len(result)}个点: {result[-1]['date']}={result[-1]['value']}%")
        return result
    except Exception as e:
        print(f"  [PPI] 失败: {e}")
        return []


def fetch_pmi():
    """制造业PMI"""
    try:
        import akshare as ak
        df = ak.macro_china_pmi()
        if df is None or df.empty:
            return []
        
        result = []
        cols = list(df.columns)
        val_col = None
        for c in cols:
            if "制造" in str(c) or "PMI" in str(c):
                val_col = c
                break
        
        for _, row in df.tail(12).iterrows():
            d = safe_date(row.get("日期", row.get(cols[0], "")))
            val = safe_float(row.get(val_col, 0)) if val_col else None
            if d and val is not None:
                result.append({"date": d, "value": round(val, 1)})
        
        if result:
            print(f"  [PMI] {len(result)}个点: {result[-1]['date']}={result[-1]['value']}")
        return result
    except Exception as e:
        print(f"  [PMI] 失败: {e}")
        return []


def fetch_m2():
    """M2货币供应量同比增速"""
    try:
        import akshare as ak
        df = ak.macro_china_money_supply()
        if df is None or df.empty:
            return []
        
        result = []
        cols = list(df.columns)
        
        # Find M2同比 column
        val_col = None
        for c in cols:
            cs = str(c)
            if "M2" in cs or "货币和准货币" in cs:
                if "同比" in cs or "增长" in cs:
                    val_col = c
                    break
        
        if not val_col:
            for c in cols:
                if "M2" in str(c):
                    val_col = c
                    break
        
        for _, row in df.tail(12).iterrows():
            d = safe_date(row.get("月份", row.get(cols[0], "")))
            val = safe_float(row.get(val_col, 0)) if val_col else None
            if d and val is not None:
                result.append({"date": d, "value": round(val, 1)})
        
        if result:
            print(f"  [M2] {len(result)}个点: {result[-1]['date']}={result[-1]['value']}%")
        return result
    except Exception as e:
        print(f"  [M2] 失败: {e}")
        return []


def fetch_trade():
    """贸易差额"""
    try:
        import akshare as ak
        df = ak.macro_china_trade_balance()
        if df is None or df.empty:
            return []
        
        result = []
        cols = list(df.columns)
        val_col = None
        for c in cols:
            cs = str(c)
            if "差额" in cs or "贸易差额" in cs:
                val_col = c
                break
        
        for _, row in df.tail(12).iterrows():
            d = safe_date(row.get("日期", row.get(cols[0], "")))
            val = safe_float(row.get(val_col, 0)) if val_col else None
            if d and val is not None:
                result.append({"date": d, "value": round(val, 1)})
        
        if result:
            print(f"  [贸易差额] {len(result)}个点: {result[-1]['date']}={result[-1]['value']}亿美元")
        return result
    except Exception as e:
        print(f"  [贸易差额] 失败: {e}")
        return []


def build_macro_data():
    today = datetime.now().strftime("%Y-%m-%d")
    indicators = []
    
    print("\n采集宏观指标...")
    
    usdcny = fetch_usdcny_middle()
    if usdcny:
        indicators.append({
            "name": "人民币对美元汇率(中间价)",
            "unit": "USD/CNY",
            "description": "中国银行公布的美元对人民币折算价月均值",
            "source": "中国银行/中国外汇交易中心",
            "data": usdcny
        })
    
    cpi = fetch_cpi()
    if cpi:
        indicators.append({
            "name": "居民消费价格指数 CPI",
            "unit": "%",
            "description": "反映居民消费品和服务价格变动情况（同比）",
            "source": "国家统计局",
            "data": cpi
        })
    
    ppi = fetch_ppi()
    if ppi:
        indicators.append({
            "name": "工业生产者出厂价格 PPI",
            "unit": "%",
            "description": "反映工业企业产品出厂价格变动情况（同比）",
            "source": "国家统计局",
            "data": ppi
        })
    
    pmi = fetch_pmi()
    if pmi:
        indicators.append({
            "name": "制造业PMI",
            "unit": "",
            "description": "PMI>50表示制造业扩张，<50表示收缩",
            "source": "国家统计局",
            "data": pmi
        })
    
    m2 = fetch_m2()
    if m2:
        indicators.append({
            "name": "M2货币供应量同比增速",
            "unit": "%",
            "description": "广义货币供应量同比增速，反映货币政策松紧程度",
            "source": "中国人民银行",
            "data": m2
        })
    
    trade = fetch_trade()
    if trade:
        indicators.append({
            "name": "货物贸易差额",
            "unit": "亿美元",
            "description": "月度出口额减进口额",
            "source": "海关总署",
            "data": trade
        })
    
    macro_data = {
        "update_date": today,
        "data_source": "中国人民银行、国家统计局、海关总署、中国外汇交易中心（数据由AKShare自动获取）",
        "dashboard": {
            "indicators": indicators
        }
    }
    
    return macro_data


def main():
    print("=" * 60)
    print(f"宏观数据自动采集 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)
    
    macro_data = build_macro_data()
    
    n = len(macro_data["dashboard"]["indicators"])
    pts = sum(len(ind["data"]) for ind in macro_data["dashboard"]["indicators"])
    print(f"\n采集完成: {n}项指标, {pts}个数据点")
    
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    output = DATA_DIR / "macro_data.json"
    with open(output, "w", encoding="utf-8") as f:
        json.dump(macro_data, f, ensure_ascii=False, indent=2)
    
    print(f"已保存: {output} ({output.stat().st_size}B)")
    
    if n < 3:
        print(f"\n警告: 仅获取 {n} 个指标，数据可能不完整。rebuild.js 将跳过质量不达标的数据。")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
