import streamlit as st
import os
import time
import json
import io
import qrcode
from datetime import datetime
from PIL import Image

# Google Drive 官方库
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

# 第三方组件：真实的图片粘贴功能
from streamlit_paste_button import paste_image_button

# ====================
# 1. 核心配置与授权
# ====================
st.set_page_config(page_title="云端永久中转站", page_icon="☁️", layout="centered")

ACCESS_CODE = "8888" 
MY_APP_URL = "https://你的专属网址.streamlit.app" 

def get_gdrive_service():
    """获取 Google Drive 服务"""
    try:
        raw_token = st.secrets["GCP_TOKEN"]
        token_dict = json.loads(raw_token, strict=False)
        creds = Credentials.from_authorized_user_info(token_dict)
        return build('drive', 'v3', credentials=creds)
    except Exception as e:
        st.error(f"网盘授权失败，请检查 Secrets 配置: {e}")
        return None

# ====================
# 2. 侧边栏：扫码功能
# ====================
with st.sidebar:
    st.title("📱 手机同步")
    current_url = st.text_input("当前网址", value=MY_APP_URL)
    if current_url:
        qr = qrcode.make(current_url)
        st.image(qr.get_image(), use_column_width=True)
    st.caption("扫码后输入提取码，实现跨设备传图传文件。")

# ====================
# 3. 安全拦截
# ====================
st.title("☁️ 永久云端中转站")
user_pwd = st.text_input("🔑 请输入提取码：", type="password")

if user_pwd != ACCESS_CODE:
    if user_pwd: st.error("提取码错误！")
    else: st.info("请输入提取码解锁功能。")
    st.stop()

# ====================
# 4. 云端操作函数
# ====================
drive_service = get_gdrive_service()
FOLDER_ID = st.sidebar.text_input("📁 Google Drive 目录 ID", placeholder="填入你要存放的文件夹ID")

def upload_to_drive(file_bytes, file_name, mime_type='application/octet-stream'):
    """将数据上传到 Google Drive"""
    if not FOLDER_ID:
        st.warning("请在侧边栏填入 Google Drive 文件夹 ID！")
        return None
    
    file_metadata = {'name': file_name, 'parents': [FOLDER_ID]}
    media = MediaFileUpload(file_bytes, mimetype=mime_type, resumable=True)
    try:
        file = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        return file.get('id')
    except Exception as e:
        st.error(f"上传失败: {e}")
        return None

def list_drive_files():
    """列出网盘中的文件"""
    if not FOLDER_ID: return []
    query = f"'{FOLDER_ID}' in parents and trashed = false"
    try:
        results = drive_service.files().list(q=query, fields="files(id, name, size, mimeType, createdTime)").execute()
        return results.get('files', [])
    except Exception as e:
        st.error(f"获取文件列表失败: {e}")
        return []

# ====================
# 5. 上传与粘贴区域
# ====================
st.subheader("📤 快速上传 / 粘贴图片")

col_up, col_paste = st.columns(2)

with col_up:
    st.markdown("**文件上传**")
    uploaded_file = st.file_uploader("选择文件", label_visibility="collapsed")
    if uploaded_file:
        with st.spinner("同步至云端..."):
            temp_path = f"temp_{uploaded_file.name}"
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            fid = upload_to_drive(temp_path, uploaded_file.name)
            if fid: 
                st.toast(f"✅ {uploaded_file.name} 已入库")
                os.remove(temp_path)

with col_paste:
    st.markdown("**粘贴图片 (Ctrl+V)**")
    
    # 使用真实的第三方组件拦截剪贴板
    paste_result = paste_image_button(
        label="📋 点击此处，然后按 Ctrl+V 粘贴",
        text_color="#000000",
        background_color="#f0f2f6"
    )
    
    if paste_result.image_data is not None:
        with st.spinner("图片处理中..."):
            img_name = f"Pasted_{datetime.now().strftime('%m%d_%H%M%S')}.png"
            temp_img_path = f"temp_{img_name}"
            
            # paste_result.image_data 是一个标准的 PIL 图像对象，直接保存
            paste_result.image_data.save(temp_img_path, format="PNG")
            
            fid = upload_to_drive(temp_img_path, img_name, 'image/png')
            if fid:
                st.image(paste_result.image_data, caption="已上传至云端", width=150)
                st.toast("✅ 图片已同步至网盘")
                os.remove(temp_img_path)

# ====================
# 6. 云端提取区
# ====================
st.divider()
st.subheader("📥 云端提取列表 (最近上传)")

if drive_service and FOLDER_ID:
    files = list_drive_files()
    if not files:
        st.info("网盘文件夹中暂无内容。")
    else:
        for f in sorted(files, key=lambda x: x['createdTime'], reverse=True):
            with st.container(border=True):
                c_name, c_act = st.columns([7, 3])
                with c_name:
                    st.write(f"📄 **{f['name']}**")
                    size_mb = int(f.get('size', 0)) / (1024*1024)
                    st.caption(f"大小: {size_mb:.2f} MB | 类型: {f['mimeType']}")
                
                with c_act:
                    try:
                        request = drive_service.files().get_media(fileId=f['id'])
                        fh = io.BytesIO()
                        downloader = MediaIoBaseDownload(fh, request)
                        done = False
                        while done is False:
                            status, done = downloader.next_chunk()
                        
                        st.download_button(
                            label="下载",
                            data=fh.getvalue(),
                            file_name=f['name'],
                            key=f"dl_{f['id']}",
                            use_container_width=True
                        )
                        
                        if st.button("删除", key=f"del_{f['id']}", use_container_width=True):
                            drive_service.files().delete(fileId=f['id']).execute()
                            st.rerun()
                    except Exception as e:
                        st.error("此文件无法提供下载（可能是权限或格式受限）")
else:
    st.warning("💡 请在侧边栏配置 Google Drive 文件夹 ID 以开启永久存储。")

st.divider()
st.caption("注：本工具直接与你的 Google Drive 通讯，文件永久保存，除非你手动删除。")
