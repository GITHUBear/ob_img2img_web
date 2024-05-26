import streamlit as st
from oceanbase import ObImgVec
from PIL import Image
import os
import tempfile
import time
import logging
from towhee import ops,pipe,AutoPipes,AutoConfig,DataCollection

# embedding model
logging.log(logging.INFO, "init embedding model....")
img_pipe = AutoPipes.pipeline('text_image_embedding')
logging.log(logging.INFO, "init embedding model finished.")
# system
server_img_store_path = os.getenv("SERVER_IMG_STORE_PATH", "./img")
# oceanbase
def get_max_imgid():
    global server_img_store_path
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp'}
    max_number = 0

    for item in os.listdir(server_img_store_path):
        full_path = os.path.join(server_img_store_path, item)
        if os.path.isfile(full_path):
            filename, extension = os.path.splitext(item)
            if extension.lower() in image_extensions:
                try:
                    number = int(filename)
                    if number > max_number:
                        max_number = number
                except ValueError:
                    continue
    return max_number

first_embedding = True
ob_host = "oceanbase" # change to localhost for local test
ob_port = 2881
ob_database = "test"
ob_user = "root@test"
ob_password = ""
connection_str = f"mysql+pymysql://{ob_user}:{ob_password}@{ob_host}:{ob_port}/{ob_database}?charset=utf8mb4"
obvec = ObImgVec(connection_str, "img2img", get_max_imgid())

def img_embedding(path):
    return img_pipe(path).get()[0]

def process_image(image_path, target_path):
    global first_embedding
    vec = img_embedding(image_path)
    if first_embedding:
        embedding_dim = len(vec.tolist())
        obvec.ob_create_img2img(embedding_dim)
        first_embedding = False
    obvec.ob_insert_img2img(vec, target_path)

# 伪造一个相似图片搜索的函数
def find_similar_images(image_path, num_results):
    query_vec = img_embedding(image_path)
    res = obvec.ob_ann_search("<~>", query_vec, num_results)
    result_paths = [r.path for r in res]
    return result_paths

# 设置应用的布局为宽模式
st.set_page_config(layout="wide")

if 'files_uploaded_tab1' not in st.session_state:
    st.session_state.files_uploaded_tab1 = False
if 'file_uploaded_tab2' not in st.session_state:
    st.session_state.file_uploaded_tab2 = False

def on_file_uploaded_tab1():
    st.session_state.files_uploaded_tab1 = True
    st.session_state.file_uploaded_tab2 = False

def on_file_uploaded_tab2():
    st.session_state.file_uploaded_tab2 = True
    st.session_state.files_uploaded_tab1 = False

# 创建两个功能标签页
tab1, tab2 = st.tabs(["图片处理", "相似图片搜索"])

with tab1:
    st.header("图片处理")
    
    # 文件导入组件
    uploaded_files = st.file_uploader("选择图片文件或拖拽图片到这里", 
                                      accept_multiple_files=True, 
                                      type=['png', 'jpg', 'jpeg'],
                                      on_change=on_file_uploaded_tab1)
    
    if uploaded_files and st.session_state.files_uploaded_tab1:
        # 初始化进度条
        progress_bar = st.progress(0)

        for index, uploaded_file in enumerate(uploaded_files, start=1):
            suffix = os.path.splitext(uploaded_file.name)[-1]
            target_path = os.path.join(server_img_store_path, f"{obvec.get_imgid()}{suffix}")
            with open(target_path, "wb") as f:
                f.write(uploaded_file.getvalue())
            process_image(target_path, target_path)
            
            # 更新进度条
            progress_bar.progress(index / len(uploaded_files))

        st.success("所有图片已处理完成!")

with tab2:
    st.header("相似图片搜索")
    
    # 文件导入组件
    uploaded_file = st.file_uploader("选择一个图片文件", 
                                     type=['png', 'jpg', 'jpeg'], 
                                     key="uploader2",
                                     on_change=on_file_uploaded_tab2)
    
    # 1到10的slide组件
    num_results = st.slider("选择相似图片的数量", 1, 10, value=5)
    
    # 当文件被上传时执行
    if uploaded_file and st.session_state.file_uploaded_tab2:
        # 将上传的文件保存到临时目录
        with tempfile.NamedTemporaryFile(delete=True, suffix=os.path.splitext(uploaded_file.name)[-1]) as tmpfile:
            tmpfile.write(uploaded_file.getvalue())
            image_path = tmpfile.name
            st.write("原图:")
            st.image(image_path, width=300) # 展示原图
        
            # 搜索相似图片
            similar_images = find_similar_images(image_path, num_results)
        
            # 展示找到的相似图片
            st.write("相似图片:")
            for similar_image in similar_images:
                st.image(similar_image, width=300)