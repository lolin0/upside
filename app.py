import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
from datetime import datetime

# --- 1. 页面配置 ---
st.set_page_config(
    page_title="Upside | Lolin's Dashboard",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. 核心逻辑 (后端大脑) ---
DATA_FILE = 'upside_data.csv'

def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    else:
        # 初始化
        init_data = {
            'date': [datetime.now().strftime("%Y-%m-%d %H:%M")],
            'spending': [0],
            'income': [0],
            'sleep': [7.0],
            'study': [0.0],
            'weight': [70.5],
            'diary': ['IPO 启动日'],
            'change': [0.0],
            'price': [100.00]
        }
        df = pd.DataFrame(init_data)
        df.to_csv(DATA_FILE, index=False)
        return df

# 重新计算逻辑 (和之前一样)
def calculate_new_price(last_price, spending, sleep, study):
    change_pct = 0.0
    if study > 0: change_pct += (study * 0.5)
    if sleep < 6: change_pct -= 2.0
    elif sleep >= 7.5: change_pct += 0.5
    if spending > 500: change_pct -= 0.5
    elif spending == 0: change_pct += 0.2
    new_price = last_price * (1 + change_pct / 100)
    return new_price, change_pct

# 加载数据
df = load_data()
if not df.empty:
    current_price = df.iloc[-1]['price']
    current_change = df.iloc[-1]['change']
    total_study = df['study'].sum()
else:
    current_price = 100.0
    current_change = 0.0
    total_study = 0.0

# --- 3. CSS 样式 (保持极简) ---
st.markdown("""
<style>
    .stApp { background-color: #ffffff; }
    .block-container { padding-top: 1.5rem !important; padding-bottom: 2rem !important; }
    section[data-testid="stSidebar"] { background-color: #f8f9fa; border-right: 1px solid #efeebd; }
    div[data-testid="stVerticalBlock"] > div { gap: 0.5rem !important; }
    .sidebar-header { font-size: 0.85rem; font-weight: 700; color: #4b5563; margin-top: 10px; margin-bottom: 5px; text-transform: uppercase; }
    .metric-card { background-color: #ffffff; border: 1px solid #e5e7eb; border-radius: 8px; padding: 12px; box-shadow: 0 1px 2px rgba(0,0,0,0.05); display: flex; align-items: center; }
    .metric-icon-box { width: 40px; height: 40px; border-radius: 6px; display: flex; align-items: center; justify-content: center; font-size: 20px; margin-right: 12px; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    .main-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; padding-bottom: 10px; border-bottom: 1px solid #f3f4f6; }
</style>
""", unsafe_allow_html=True)

# --- 4. 侧边栏 (输入区) ---
with st.sidebar:
    st.markdown('<div class="sidebar-header">资金部</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1: in_spend = st.number_input("支出", value=0, step=10)
    with c2: in_income = st.number_input("收入", value=0, step=100)
        
    st.markdown('<div class="sidebar-header">工程部</div>', unsafe_allow_html=True)
    col_sleep_label, col_sleep_val = st.columns([3, 1])
    with col_sleep_label: st.write("睡眠 (h)")
    with col_sleep_val: st.caption("7.0")
    in_sleep = st.slider("sleep_slider", 0.0, 12.0, 7.0, label_visibility="collapsed")
    st.toggle("运动打卡", value=False)
    in_weight = st.number_input("体重 (kg)", value=70.5, step=0.1)

    st.markdown('<div class="sidebar-header">研发部</div>', unsafe_allow_html=True)
    col_study_label, col_study_val = st.columns([3, 1])
    with col_study_label: st.write("学习投入 (h)")
    with col_study_val: st.caption("2.0")
    in_study = st.slider("study_slider", 0.0, 12.0, 2.0, label_visibility="collapsed")

    st.markdown('<div class="sidebar-header">关键日记</div>', unsafe_allow_html=True)
    in_diary = st.text_input("diary", placeholder="一句话记录...", label_visibility="collapsed")
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚀 归档今日数据", use_container_width=True, type="primary"):
        new_price, pct = calculate_new_price(current_price, in_spend, in_sleep, in_study)
        new_row = {
            'date': datetime.now().strftime("%Y-%m-%d %H:%M"),
            'spending': in_spend, 'income': in_income, 'sleep': in_sleep,
            'study': in_study, 'weight': in_weight, 'diary': in_diary,
            'change': pct, 'price': new_price
        }
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        df.to_csv(DATA_FILE, index=False)
        st.success(f"已存档！今日股价 {new_price:.2f}")
        st.rerun()

# --- 5. 主界面 (展示区) ---
st.markdown(f"""
<div class="main-header">
    <div style="display: flex; align-items: center;">
        <span style="font-size: 1.8rem; margin-right: 10px;">🚀</span>
        <div><div style="font-size: 1.4rem; font-weight: 800; color: #111827;">Upside | Lo</div></div>
    </div>
    <div style="display: flex; gap: 15px; align-items: center;">
        <div style="text-align: right; background: #f3f4f6; padding: 4px 10px; border-radius: 6px;">
            <div style="color: #6b7280; font-size: 0.7rem;">倒计时</div>
            <div style="font-size: 1rem; font-weight: bold; color: #374151;">712 天</div>
        </div>
        <div style="text-align: right; background: {'#fee2e2' if current_change < 0 else '#dcfce7'}; padding: 4px 10px; border-radius: 6px;">
            <div style="color: {'#991b1b' if current_change < 0 else '#166534'}; font-size: 0.7rem;">股价</div>
            <div style="font-size: 1.1rem; font-weight: bold; color: {'#dc2626' if current_change < 0 else '#15803d'};">
                ¥{current_price:.2f}
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

c1, c2, c3 = st.columns(3)
def render_card(icon, bg_color, title, value):
    return f"""<div class="metric-card"><div class="metric-icon-box" style="background-color: {bg_color};">{icon}</div><div><div style="color: #6b7280; font-size: 0.75rem; font-weight: 600;">{title}</div><div style="color: #111827; font-size: 1.3rem; font-weight: 700;">{value}</div></div></div>"""
total_asset = 300000 + df['income'].sum() - df['spending'].sum()
with c1: st.markdown(render_card("💰", "#fef3c7", "净资产", f"¥ {total_asset:,.0f}"), unsafe_allow_html=True)
with c2: st.markdown(render_card("⏳", "#dbeafe", "研发时", f"{total_study:.1f} h"), unsafe_allow_html=True)
with c3: st.markdown(render_card("🏃‍♀️", "#f3e8ff", "身体分", f"{df.iloc[-1]['weight']} kg" if not df.empty else "0.0 kg"), unsafe_allow_html=True)

st.markdown("##### 📈 市值走势")
if not df.empty:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['date'], y=df['price'], mode='lines+markers',
        line=dict(color='#ef4444', width=3, shape='spline'),
        marker=dict(size=6, color='#ef4444', symbol='circle', line=dict(color='white', width=2)),
        fill='tozeroy', fillcolor='rgba(239, 68, 68, 0.1)'
    ))
    fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=200, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(showgrid=False, linecolor='#e5e7eb'), yaxis=dict(showgrid=True, gridcolor='#f3f4f6'))
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    # AI 董秘
    latest_diary = df.iloc[-1]['diary']
    st.markdown(f"""
    <div style="background-color: #f8fafc; border-left: 4px solid #5d5cde; padding: 10px; border-radius: 4px; display: flex; align-items: center; margin-top: 10px;">
        <div style="font-size: 1.5rem; margin-right: 10px;">🤖</div>
        <div style="color: #4b5563; font-size: 0.9rem; flex-grow: 1;"><b>最新 Log：</b>{latest_diary}</div>
    </div>
    """, unsafe_allow_html=True)

# --- 6. 数据管理后台 (新增删除功能) ---
st.markdown("---")
with st.expander("🗂️ 数据管理后台 (Data Admin)"):
    # 显示完整的表格
    st.dataframe(df, use_container_width=True)
    
    st.write("###### 🗑️ 删除记录")
    # 创建一个下拉菜单，让用户选择要删除的记录（显示日期和日记，方便辨认）
    # 我们把 index 放到选项里，确保唯一性
    delete_options = df.index.tolist()
    # 生成易读的标签： "Index 0 | 2024-01-20 | IPO 启动日"
    delete_labels = [f"ID {i} | {row['date']} | {row['diary']}" for i, row in df.iterrows()]
    
    selected_indices = st.multiselect(
        "选择要删除的记录 (支持多选):",
        options=delete_options,
        format_func=lambda x: delete_labels[x] # 显示易读的标签
    )
    
    if st.button("确认删除选中记录", type="secondary"):
        if selected_indices:
            # 执行删除
            df_new = df.drop(selected_indices).reset_index(drop=True)
            # 保存
            df_new.to_csv(DATA_FILE, index=False)
            st.success(f"已删除 {len(selected_indices)} 条记录！")
            st.rerun() # 刷新页面
        else:
            st.warning("请先选择要删除的记录。")