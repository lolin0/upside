# --- 加载与计算 ---
df = load_data()

# 修复核心：如果表格是空的，必须手动创建第一行数据，并赋值给 df
if df.empty:
    current_price = 100.0
    current_change = 0.0
    total_study = 0.0
    latest_comment = "系统初始化完成，等待首日数据..."
    
    # === 漏掉的补丁开始 ===
    init_row = pd.DataFrame([{
        'date': datetime.now().strftime("%Y-%m-%d %H:%M"),
        'spending': 0, 'income': 0, 'sleep': 7.0, 'study': 0.0,
        'weight': 70.5, 'diary': 'System Init', 'change': 0.0, 'price': 100.0, 
        'ai_comment': latest_comment
    }])
    # 把这一行塞进 df 里，这样 df 就不为空了！
    df = pd.concat([df, init_row], ignore_index=True)
    # 顺便存回 Google Sheets，防止下次还空
    save_data(df)
    # === 漏掉的补丁结束 ===

else:
    current_price = float(df.iloc[-1]['price'])
    current_change = float(df.iloc[-1]['change'])
    total_study = df['study'].sum()
    # 安全获取 AI 点评，防止列不存在
    if 'ai_comment' in df.columns and pd.notna(df.iloc[-1]['ai_comment']):
        latest_comment = df.iloc[-1]['ai_comment']
    else:
        latest_comment = "暂无研报"