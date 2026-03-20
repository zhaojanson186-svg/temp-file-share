import streamlit as st
import os
import time
import qrcode
from PIL import Image

# 页面基础配置
st.set_page_config(page_title="私密文件中转站", page_icon="🔒", layout="centered")

# ====================
# 核心配置区
# ====================
# 在这里设置你的专属提取码（默认设为 8888）
ACCESS_CODE = "8888" 
# 在这里填入你的 Streamlit Cloud 专属网址（用于生成二维码）
MY_APP_URL = "https://你的专属网址.streamlit.app" 


# ====================
# 侧边栏：手机扫码直达
# ====================
with st.sidebar:
    st.title("📱 手机扫码直达")
    st.markdown("用手机浏览器或微信扫一扫，跨设备互传文件。")
    
    # 允许用户在网页上动态修改要生成二维码的网址（防呆设计）
    current_url = st.text_input("当前网址 (可手动修改)", value=MY_APP_URL)
    
    if current_url:
        # 生成二维码图片
        qr = qrcode.make(current_url)
        # 在侧边栏显示二维码
        st.image(qr.get_image(), use_column_width=True)
    
    st.divider()
    st.markdown("💡 **提示**: 请确保当前网址与你浏览器地址栏一致。")

# ====================
# 提取码拦截逻辑
# ====================
st.title("🔒 私密云剪贴板 & 中转站")

# 密码输入框
user_pwd = st.text_input("🔑 请输入提取码以访问：", type="password")

# 如果密码不对，直接停止运行后面的代码
if user_pwd != ACCESS_CODE:
    if user_pwd: # 如果输入了密码但是不对
        st.error("提取码错误，请重试！")
    else:
        st.info("请输入提取码解锁功能。")
    st.stop() # 关键点：停止渲染后续的所有内容

# 如果代码能走到这里，说明提取码输入正确！
st.success("✅ 验证成功，欢迎使用！")
st.divider()


# ====================
# 文件清理机制
# ====================
UPLOAD_DIR = "temp_uploads"
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

cleanup_old_files()


# ====================
# 第一部分：上传文件
# ====================
st.subheader("📤 功能 1：上传文件")
uploaded_file = st.file_uploader("选择你要暂存的文件 (单次 200MB 以内)")

if uploaded_file is not None:
    save_path = os.path.join(UPLOAD_DIR, uploaded_file.name)
    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.success(f"✅ 文件 `{uploaded_file.name}` 上传成功！")


# ====================
# 第二部分：在线记事本
# ====================
st.subheader("📝 功能 2：在线记事本 (云剪贴板)")
text_content = st.text_area("在此输入或粘贴文字：", height=150)

col1, col2 = st.columns([3, 1])
with col1:
    txt_filename = st.text_input("给文本起个名字（无需加 .txt）：", value="未命名便签")
with col2:
    st.write("") 
    st.write("") 
    if st.button("💾 保存为 TXT", use_container_width=True):
        if text_content.strip() == "":
            st.warning("⚠️ 内容不能为空哦！")
        else:
            safe_filename = txt_filename.strip() + ".txt"
            save_path = os.path.join(UPLOAD_DIR, safe_filename)
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(text_content)
            st.success(f"✅ 文本已成功保存为 `{safe_filename}`！")

st.divider()

# ====================
# 第三部分：下载文件
# ====================
st.subheader("📥 提取区：可下载的文件列表")

available_files = os.listdir(UPLOAD_DIR)

if not available_files:
    st.info("当前没有可用的文件。")
else:
    for filename in available_files:
        file_path = os.path.join(UPLOAD_DIR, filename)
        file_size_kb = os.path.getsize(file_path) / 1024
        
        col_name, col_size, col_btn = st.columns([5, 2, 2])
        
        with col_name:
            st.write(f"📄 **{filename}**")
        with col_size:
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
                    key=f"download_{filename}" 
                )
