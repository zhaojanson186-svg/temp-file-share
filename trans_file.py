import streamlit as st
import os
import time

st.set_page_config(page_title="临时文件中转站", page_icon="📁")

st.title("📁 临时文件中转站")
st.markdown("在这里上传文件，其他人可以下载。**注意：文件最多保留 24 小时，且服务器休眠时可能会提前清空。**")

# 定义存储文件的文件夹名称
UPLOAD_DIR = "temp_uploads"

# 如果文件夹不存在，则自动创建一个
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

def cleanup_old_files():
    """清理超过 24 小时（86400秒）的文件"""
    current_time = time.time()
    for filename in os.listdir(UPLOAD_DIR):
        file_path = os.path.join(UPLOAD_DIR, filename)
        if os.path.isfile(file_path):
            # 获取文件的最后修改时间
            file_mtime = os.path.getmtime(file_path)
            # 86400 秒 = 24 小时
            if current_time - file_mtime > 86400:
                os.remove(file_path)

# 每次刷新页面时，先执行一次清理任务
cleanup_old_files()

st.divider()

# ====================
# 第一部分：上传文件
# ====================
st.subheader("📤 第一步：上传文件")
uploaded_file = st.file_uploader("选择你要暂存的文件", help="单次上传限制通常为 200MB 以内")

if uploaded_file is not None:
    # 拼接保存路径
    save_path = os.path.join(UPLOAD_DIR, uploaded_file.name)
    
    # 将上传的字节流写入服务器的本地文件夹中
    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    st.success(f"✅ 文件 `{uploaded_file.name}` 上传成功！现在其他人可以下载它了。")

st.divider()

# ====================
# 第二部分：下载文件
# ====================
st.subheader("📥 第二步：可下载的文件列表")

# 获取文件夹里的所有文件
available_files = os.listdir(UPLOAD_DIR)

if not available_files:
    st.info("当前没有可用的文件。")
else:
    # 遍历并生成每一个文件的下载按钮
    for filename in available_files:
        file_path = os.path.join(UPLOAD_DIR, filename)
        
        # 获取文件大小，做个简单的格式化
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"📄 **{filename}** ({file_size_mb:.2f} MB)")
        with col2:
            # 打开文件供下载
            with open(file_path, "rb") as f:
                st.download_button(
                    label="点击下载",
                    data=f,
                    file_name=filename,
                    key=filename # 给按钮一个唯一的 key 防止报错
                )