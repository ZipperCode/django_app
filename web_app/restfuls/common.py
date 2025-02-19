import os
import uuid

from web_app import settings


def upload_images(request) -> str:
    uploaded_files = request.FILES.getlist("files[]")  # 获取上传的文件列表
    file_paths = []  # 用于存储文件路径列表
    for file in uploaded_files:
        # 生成 UUID 文件名
        file_name = str(uuid.uuid4()) + "." + file.name.split(".")[-1]  # 保留原始文件扩展名
        file_path = os.path.join("upload/images/", file_name)  # 相对 media 目录的路径
        full_path = os.path.join(settings.MEDIA_ROOT, file_path)  # 文件的完整路径

        # 确保目录存在
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        # 保存文件
        with open(full_path, "wb") as f:
            for chunk in file.chunks():
                f.write(chunk)

        file_paths.append(file_path)  # 将相对路径添加到列表中
    return ",".join(file_paths)
