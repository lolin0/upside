import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import requests # 👈 换成了这个万能库
import json

# --- 1. 页面配置 ---
st.set_page_config(page_title="Upside | Gemini", page_icon="✨", layout="wide")

# --- 2. 核心逻辑 ---
# A. 连接 Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# B. 定义加载函数
def load_data():
    try:
        df = conn.read(worksheet="Sheet1", ttl=0)
        if not df.empty:
             df['date'] = df['date'].astype(str)
        return df
    except Exception:
        return pd.DataFrame(columns=['date', 'spending', 'income', 'sleep', 'study', 'weight', 'diary', 'change', 'price', 'ai_comment'])

def save_data(df):
    conn.update(worksheet="Sheet1", data=df)

# C. 【核心修改】使用 REST API 直接调用 Gemini (不依赖 SDK)
def get_ai_comment(spending, sleep, study, weight, diary):
    # 从 secrets 获取 Key
    api_key = st.secrets["google_ai"]["api_key"]
    
    # 构造请求 URL (使用 gemini-1.5-flash)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    # 构造提示词
    prompt_text = f"""
    你是一个严厉但幽默的“个人上市系统”AI董秘。根据今日数据进行犀利点评。
    数据：消费{spending}元, 睡眠{sleep}h, 学习{study}h, 体重{weight}kg, 日记:{diary}
    要求：风格像《华尔街之狼》投资人，毒舌但切中要害。100字以内。
    """
    
    # 构造请求体
    payload = {
        "contents": [{
            "parts": [{"text": prompt_text}]
        }]
    }
    
    try:
        # 发送 HTTP POST 请求
        response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'})
        
        # 解析结果
        if response.status_code == 200:
            result = response.json()
            # 提取 AI 回复的文本
            return result['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"AI 罢工了 (状态码: {response.status_code}, 错误: {response.text})"
            
    except Exception as e:
        return f"网络连接失败 ({str(e)})"

# 股价计算逻辑
def calculate_new_price(last_price, spending, sleep, study):
    change_pct = 0.0
    if study > 0: change_pct += (study * 0.5)
    if sleep < 6: change_pct -= 2.0
    elif sleep >= 7.5: change_pct += 0.5
    if spending > 500: change_pct -= 0.5
    elif spending == 0: change_pct += 0.2
    new_price = last_price * (1 + change_pct / 100)
    return new_price, change_pct

# --- 3. 执行逻辑 ---
df = load_data()

# 初始化逻辑
if df.empty:
    current_price = 100.0
    current_change = 0.0
    total_study = 0.0
    latest_comment = "系统初始化完成，等待首日数据..."
    init_row = pd.DataFrame([{
        'date': datetime.now().strftime("%Y-%m-%d %H:%M"),
        'spending': 0, 'income': 0, 'sleep': 7.0, 'study': 0.0,
        'weight': 70.5, 'diary': 'System Init', 'change': 0.0, 'price': 100.0, 
        'ai_comment': latest_comment
    }])
    df = pd.concat([df, init_row], ignore_index=True)
    save_data(df)
else:
    current_price = float(df.iloc[-1]['price'])
    current_change = float(df.iloc[-1]['change'])
    total_study = df['study'].sum()
    if 'ai_comment' in df.columns and pd.notna(df.iloc[-1]['ai_comment']):
        latest_comment = df.iloc[-1]['ai_comment']
    else:
        latest_comment = "暂无研报"

# --- 4. UI 界面 ---
st.markdown("""
<style>
    .stApp {background: #fff;} .block-container{padding-top:1.5rem;}
    section[data-testid="stSidebar"] {background: #f8f9fa; border-right:1px solid #eee;}
    .metric-card {border:1px solid #e5e7eb; border-radius:8px; padding:12px; display:flex; align-items:center;}
    .metric-icon-box {width:40px; height:40px; border-radius:6px; display:flex; justify-content:center; align-items:center; font-size:20px; margin-right:12px;}
    .main-header {display:flex; justify-content:space-between; align-items:center; margin-bottom:15px; border-bottom:1px solid #f3f4f6; padding-bottom:10px;}
    #MainMenu, footer, header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown('**资金部**')
    c1, c2 = st.columns(2)
    with c1: in_spend = st.number_input("支出", 0, step=10)
    with c2: in_income = st.number_input("收入", 0, step=100)
    st.markdown('**工程部**')
    in_sleep = st.slider("睡眠", 0.0, 12.0, 7.0)
    in_weight = st.number_input("体重", value=70.5, step=0.1)
    st.markdown('**研发部**')
    in_study = st.slider("学习投入", 0.0, 12.0, 2.0)
    st.markdown('**日记**')
    in_diary = st.text_input("diary", placeholder="今日关键事件...", label_visibility="collapsed")
    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button("🚀 归档并生成研报", use_container_width=True, type="primary"):
        with st.spinner("Gemini 正在分析..."):
            new_price, pct = calculate_new_price(current_price, in_spend, in_sleep, in_study)
            # 调用新的 REST API 函数
            ai_reply = get_ai_comment(in_spend, in_sleep, in_study, in_weight, in_diary)
            
            new_row = {
                'date': datetime.now().strftime("%Y-%m-%d %H:%M"),
                'spending': in_spend, 'income': in_income, 'sleep': in_sleep,
                'study': in_study, 'weight': in_weight, 'diary': in_diary,
                'change': pct, 'price': new_price, 'ai_comment': ai_reply
            }
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            save_data(df)
        st.success("发布成功！")
        st.rerun()

st.markdown(f"""
<div class="main-header">
    <div style="display:flex; align-items:center;"><span style="font-size:1.8rem; margin-right:10px;">✨</span><div><div style="font-size:1.4rem; font-weight:800; color:#111;">Upside | Gemini</div></div></div>
    <div style="text-align:right; background:{'#fee2e2' if current_change < 0 else '#dcfce7'}; padding:4px 10px; border-radius:6px;">
        <div style="color:{'#991b1b' if current_change < 0 else '#166534'}; font-size:0.7rem;">股价</div>
        <div style="font-size:1.1rem; font-weight:bold; color:{'#dc2626' if current_change < 0 else '#15803d'};">¥{current_price:.2f}</div>
    </div>
</div>
""", unsafe_allow_html=True)

c1, c2, c3 = st.columns(3)
total_asset = 300000 + df['income'].sum() - df['spending'].sum()
def card(i, b, t, v): return f"<div class='metric-card'><div class='metric-icon-box' style='background:{b}'>{i}</div><div><div style='color:#6b7280;font-size:0.75rem;font-weight:600'>{t}</div><div style='color:#111;font-size:1.3rem;font-weight:700'>{v}</div></div></div>"
with c1: st.markdown(card("💰", "#fef3c7", "净资产", f"¥ {total_asset:,.0f}"), unsafe_allow_html=True)
with c2: st.markdown(card("⏳", "#dbeafe", "研发时", f"{total_study:.1f} h"), unsafe_allow_html=True)
with c3: st.markdown(card("🏃‍♀️", "#f3e8ff", "身体分", f"{df.iloc[-1]['weight']} kg"), unsafe_allow_html=True)

st.markdown("##### 📈 市值走势")
if not df.empty:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['date'], y=df['price'], mode='lines+markers', line=dict(color='#ef4444', width=3, shape='spline'), fill='tozeroy', fillcolor='rgba(239,68,68,0.1)'))
    fig.update_layout(margin=dict(l=0,r=0,t=10,b=0), height=200, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#f3f4f6'))
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

st.markdown(f"""
<div style="background:#f0fdfa; border-left:4px solid #0d9488; padding:15px; border-radius:4px; display:flex; margin-top:10px;">
    <div style="font-size:1.8rem; margin-right:15px;">✨</div>
    <div><div style="font-weight:bold; color:#0f766e; font-size:0.9rem; margin-bottom:4px;">Gemini 董秘点评</div><div style="color:#374151; font-size:0.95rem; line-height:1.6;">{latest_comment}</div></div>
</div>
""", unsafe_allow_html=True)