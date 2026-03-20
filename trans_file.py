import streamlit as st
import os
import time

st.set_page_config(page_title="临时文件中转站", page_icon="📁", layout="centered")

st.title("📁 临时文件中转站 & 云剪贴板")
st.markdown("在这里上传文件或粘贴文本，其他人可以下载。**注意：文件最多保留 24 小时。**")

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
            file_mtime = os.path.getmtime(file_path)
            if current_time - file_mtime > 86400:
                os.remove(file_path)

# 每次刷新页面时，先执行一次清理任务
cleanup_old_files()

st.divider()

# ====================
# 第一部分：上传文件
# ====================
st.subheader("📤 功能 1：上传文件")
uploaded_file = st.file_uploader("选择你要暂存的文件")

if uploaded_file is not None:
    save_path = os.path.join(UPLOAD_DIR, uploaded_file.name)
    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.success(f"✅ 文件 `{uploaded_file.name}` 上传成功！请在下方列表查看。")

st.divider()

# ====================
# 第二部分：在线记事本 (新增功能)
# ====================
st.subheader("📝 功能 2：在线记事本 (云剪贴板)")
st.markdown("不想传文件？直接把文字粘贴在这里，生成 TXT 文本供下载。")

# 文本输入区
text_content = st.text_area("在此输入或粘贴文字：", height=150)

col1, col2 = st.columns([3, 1])
with col1:
    # 让用户自定义文件名
    txt_filename = st.text_input("给文本起个名字（无需加 .txt）：", value="未命名便签")
with col2:
    st.write("") # 占位对齐
    st.write("") # 占位对齐
    # 保存按钮
    if st.button("💾 保存为 TXT", use_container_width=True):
        if text_content.strip() == "":
            st.warning("⚠️ 内容不能为空哦！")
        else:
            # 确保文件名有 .txt 后缀
            safe_filename = txt_filename.strip() + ".txt"
            save_path = os.path.join(UPLOAD_DIR, safe_filename)
            
            # 将文本写入 txt 文件 (使用 utf-8 编码防止中文乱码)
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(text_content)
            
            st.success(f"✅ 文本已成功保存为 `{safe_filename}`！请在下方列表查看。")

st.divider()

# ====================
# 第三部分：下载文件
# ====================
st.subheader("📥 提取区：可下载的文件列表")

# 获取文件夹里的所有文件
available_files = os.listdir(UPLOAD_DIR)

if not available_files:
    st.info("当前没有可用的文件。")
else:
    # 遍历并生成每一个文件的下载按钮
    for filename in available_files:
        file_path = os.path.join(UPLOAD_DIR, filename)
        
        # 获取文件大小
        file_size_kb = os.path.getsize(file_path) / 1024
        
        # 使用多列排版，让界面更美观
        col_name, col_size, col_btn = st.columns([5, 2, 2])
        
        with col_name:
            st.write(f"📄 **{filename}**")
        with col_size:
            # 如果小于 1MB 就显示 KB，大于 1MB 就显示 MB
            if file_size_kb < 1024:
                st.write(f"{file_size_kb:.1f} KB")
            else:
                st.write(f"{(file_size_kb / 1024):.2f} MB")
        with col_btn:
            with open(file_path, "rb") as f:
                st.download_button(
                    label="点击下载",
                    data=f,
                    file_name=filename,
                    key=f"download_{filename}" # 给按钮一个唯一的 key
                )
