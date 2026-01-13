import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import requests

# --- 1. 页面配置 ---
st.set_page_config(page_title="Upside | Gemini", page_icon="✨", layout="wide")

# --- 2. 调试：显示 Key 状态 ---
try:
    api_key = st.secrets["google_ai"]["api_key"]
    if api_key.endswith("fkUY"):
        st.success(f"✅ 密钥配置正确！(尾号: {api_key[-4:]})")
    else:
        st.warning(f"⚠️ 密钥未更新 (尾号: {api_key[-4:]})，请检查 Secrets")
except:
    st.error("❌ 无法读取密钥")

# --- 3. 核心函数 ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        df = conn.read(worksheet="Sheet1", ttl=0)
        if not df.empty: df['date'] = df['date'].astype(str)
        return df
    except:
        return pd.DataFrame(columns=['date', 'spending', 'income', 'sleep', 'study', 'weight', 'diary', 'change', 'price', 'ai_comment'])

def save_data(df):
    conn.update(worksheet="Sheet1", data=df)

# === ✨ 核心改动：智能获取可用模型 ===
def get_ai_comment(spending, sleep, study, weight, diary):
    try:
        # 1. 先问 Google：你有哪些模型？
        list_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
        list_resp = requests.get(list_url)
        
        target_model = None
        
        if list_resp.status_code == 200:
            models = list_resp.json().get('models', [])
            # 自动寻找第一个名字里带 'gemini' 且支持生成的模型
            for m in models:
                if 'gemini' in m['name'] and 'generateContent' in m.get('supportedGenerationMethods', []):
                    target_model = m['name'] # 比如 'models/gemini-1.5-flash-001'
                    break
        
        # 如果没找到列表，就硬猜一个保底的
        if not target_model:
            target_model = "models/gemini-pro"

        # 2. 用找到的模型去生成点评
        url = f"https://generativelanguage.googleapis.com/v1beta/{target_model}:generateContent?key={api_key}"
        
        prompt_text = f"""
        你是一个毒舌但专业的“个人上市系统”AI董秘。
        请根据今日数据点评：消费{spending}元, 睡眠{sleep}小时, 学习{study}小时, 体重{weight}kg, 日记:{diary}。
        要求：风格犀利，类似《华尔街之狼》，100字以内。
        """
        
        response = requests.post(url, json={"contents": [{"parts": [{"text": prompt_text}]}]}, headers={'Content-Type': 'application/json'})
        
        if response.status_code == 200:
            result = response.json()
            comment = result['candidates'][0]['content']['parts'][0]['text']
            return f"✨(使用模型: {target_model})\n{comment}"
        else:
            return f"AI 生成失败 ({response.status_code}): {response.text}"
            
    except Exception as e:
        return f"网络/代码错误: {str(e)}"

def calculate_new_price(last_price, spending, sleep, study):
    change_pct = 0.0
    if study > 0: change_pct += (study * 0.5)
    if sleep < 6: change_pct -= 2.0
    elif sleep >= 7.5: change_pct += 0.5
    if spending > 500: change_pct -= 0.5
    elif spending == 0: change_pct += 0.2
    return last_price * (1 + change_pct / 100), change_pct

# --- 4. 业务逻辑与界面 ---
df = load_data()

if df.empty:
    # ... 初始化逻辑 ...
    current_price = 100.0; current_change = 0.0; latest_comment = "初始化..."
    init_row = pd.DataFrame([{'date': datetime.now().strftime("%Y-%m-%d %H:%M"), 'spending':0, 'income':0, 'sleep':7, 'study':0, 'weight':70.5, 'diary':'Init', 'change':0, 'price':100, 'ai_comment':latest_comment}])
    df = pd.concat([df, init_row], ignore_index=True); save_data(df)
else:
    current_price = float(df.iloc[-1]['price']); current_change = float(df.iloc[-1]['change'])
    latest_comment = df.iloc[-1].get('ai_comment', "暂无研报")

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
        with st.spinner("AI 正在挑选模型并思考..."):
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

st.markdown(f"## ✨ Upside | Gemini")
c1, c2, c3 = st.columns(3)
with c1: st.metric("💰 净资产", f"¥ {300000 + df['income'].sum() - df['spending'].sum():,.0f}")
with c2: st.metric("股价", f"¥ {current_price:.2f}", f"{current_change:+.1f}%")
with c3: st.metric("🏃‍♀️ 体重", f"{df.iloc[-1]['weight']} kg")

st.markdown("### 📈 市值走势")
st.line_chart(df, x='date', y='price')

# 显示最新的点评
st.info(f"🤖 **Gemini 董秘点评**：\n\n{latest_comment}")