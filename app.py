import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import requests

# --- 1. 页面配置 ---
st.set_page_config(page_title="Upside | Gemini", page_icon="✨", layout="wide")

# --- 2. 调试功能：显示 Key 尾号 (排查错误的显微镜) ---
try:
    # 获取密钥
    api_key = st.secrets["google_ai"]["api_key"]
    # 显示后四位，确认是否为新 Key
    key_tail = api_key[-4:]
    if key_tail == "fkUY":
        st.success(f"✅ 密钥配置正确！正在使用新 Key (尾号: {key_tail})")
    else:
        st.error(f"❌ 密钥未更新！当前使用的是旧 Key (尾号: {key_tail})，请去 Streamlit Cloud 更新 Secrets！")
except Exception as e:
    st.error(f"❌ 无法读取密钥，请检查 Secrets 配置。错误: {str(e)}")

# --- 3. 核心函数 ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        df = conn.read(worksheet="Sheet1", ttl=0)
        if not df.empty:
             df['date'] = df['date'].astype(str)
        return df
    except:
        return pd.DataFrame(columns=['date', 'spending', 'income', 'sleep', 'study', 'weight', 'diary', 'change', 'price', 'ai_comment'])

def save_data(df):
    conn.update(worksheet="Sheet1", data=df)

def get_ai_comment(spending, sleep, study, weight, diary):
    # 使用 Gemini 1.5 Flash (因为你的新 Key 肯定支持这个)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    prompt_text = f"""
    你是一个毒舌但专业的“个人上市系统”AI董秘。
    请根据今日数据点评：消费{spending}元, 睡眠{sleep}小时, 学习{study}小时, 体重{weight}kg, 日记:{diary}。
    要求：风格犀利，类似《华尔街之狼》，100字以内。
    """
    
    payload = {"contents": [{"parts": [{"text": prompt_text}]}]}
    headers = {'Content-Type': 'application/json'}
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"AI 报错 (状态码 {response.status_code}): {response.text}"
    except Exception as e:
        return f"网络请求失败: {str(e)}"

def calculate_new_price(last_price, spending, sleep, study):
    change_pct = 0.0
    if study > 0: change_pct += (study * 0.5)
    if sleep < 6: change_pct -= 2.0
    elif sleep >= 7.5: change_pct += 0.5
    if spending > 500: change_pct -= 0.5
    elif spending == 0: change_pct += 0.2
    return last_price * (1 + change_pct / 100), change_pct

# --- 4. 业务逻辑 ---
df = load_data()

# 初始化空表
if df.empty:
    current_price = 100.0
    current_change = 0.0
    total_study = 0.0
    latest_comment = "系统初始化..."
    init_row = pd.DataFrame([{
        'date': datetime.now().strftime("%Y-%m-%d %H:%M"),
        'spending': 0, 'income': 0, 'sleep': 7.0, 'study': 0.0,
        'weight': 70.5, 'diary': 'Init', 'change': 0.0, 'price': 100.0, 
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

# --- 5. 界面显示 ---
# 侧边栏
with st.sidebar:
    st.header("🎮 控制台")
    c1, c2 = st.columns(2)
    with c1: in_spend = st.number_input("支出", 0, step=10)
    with c2: in_income = st.number_input("收入", 0, step=100)
    in_sleep = st.slider("睡眠", 0.0, 12.0, 7.0)
    in_weight = st.number_input("体重", value=70.5, step=0.1)
    in_study = st.slider("学习", 0.0, 12.0, 2.0)
    in_diary = st.text_input("日记", placeholder="今日关键事件...")
    
    if st.button("🚀 归档并生成研报", type="primary", use_container_width=True):
        with st.spinner("Gemini 正在思考..."):
            new_price, pct = calculate_new_price(current_price, in_spend, in_sleep, in_study)
            ai_reply = get_ai_comment(in_spend, in_sleep, in_study, in_weight, in_diary)
            
            new_row = {
                'date': datetime.now().strftime("%Y-%m-%d %H:%M"),
                'spending': in_spend, 'income': in_income, 'sleep': in_sleep,
                'study': in_study, 'weight': in_weight, 'diary': in_diary,
                'change': pct, 'price': new_price, 'ai_comment': ai_reply
            }
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            save_data(df)
        st.rerun()

# 主界面
st.markdown(f"## ✨ Upside | Gemini")
c1, c2, c3 = st.columns(3)
with c1: st.metric("💰 净资产", f"¥ {300000 + df['income'].sum() - df['spending'].sum():,.0f}")
with c2: st.metric("股价", f"¥ {current_price:.2f}", f"{current_change:+.1f}%")
with c3: st.metric("🏃‍♀️ 体重", f"{df.iloc[-1]['weight']} kg")

st.markdown("### 📈 市值走势")
st.line_chart(df, x='date', y='price')

st.info(f"🤖 **Gemini 董秘点评**：\n\n{latest_comment}")