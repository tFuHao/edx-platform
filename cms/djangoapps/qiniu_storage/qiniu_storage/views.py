import os
import re
import time

import requests
from qiniu import Auth, put_file, put_data, etag, BucketManager, urlsafe_base64_encode, PersistentFop
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from . import settings

access_key = getattr(settings, "QINIU_ACCESS_KEY", None)
secret_key = getattr(settings, "QINIU_SECRET_KEY", None)
prefix_url = getattr(settings, "PREFIX_URL", None)
domain_name = getattr(settings, "QINIU_BUCKET_DOMAIN", None)
q = Auth(access_key, secret_key)  # access_key和secret_key来自settings里
bucket_name = getattr(settings, "QINIU_BUCKET_NAME", None)
pipeline_name = getattr(settings, "QINIU_PIPELINE_NAME", None)
token = q.upload_token(bucket_name)
bucket = BucketManager(q)


class QiniuTokenView(APIView):
    def get(self, request):
        return Response({"uptoken": token})


# 上传文件
class QiniuUpFileView(APIView):
    def post(self, request):
        file = request.FILES.get("videofile", None)
        # oldfilepath = request.POST.get("oldfilepath", None)
        millis = str(int(round(time.time() * 1000)))  # 通过把秒转换毫秒的方法获得13位的时间戳

        file_name = millis + '/' + file.name
        # bucket = BucketManager(q)
        r = None
        if file is not None:
            ret, info = put_data(token, file_name, file)
            # ret, info = put_data(QiniuTool().get_uptoken(request), file_name, file)
            print(ret, info)
            if info.status_code == 200:
                r = UploadQinui(file_name)

            # if oldfilepath is not None:
            #     (filepath, tempfilename) = os.path.split(oldfilepath)
            #     (filename, extension) = os.path.splitext(tempfilename)
            #     print(filepath, tempfilename, filename, extension)
            #     if extension == '.m3u8':
            #         DelTS(oldfilepath)
            #
            #     url = prefix_url + domain_name + '/'
            #     _path = oldfilepath.replace(url, '').strip()
            #     mp4_path = filepath + '/' + filename + '.mp4'
            #     _mp4_path = mp4_path.replace(url, '').strip()
            #     bucket.delete(bucket_name, _path)  # 删除m3u8文件
            #     bucket.delete(bucket_name, _mp4_path)  # 删除mp4文件
        return Response({"url": r})


# 删除文件
class DelFileView(APIView):
    def post(self, request):
        file = request.POST.get("path", None)
        # url = prefix_url + domain_name + '/'
        # if file is not None:
        #     (filename, extension) = os.path.splitext(file)
        #     print(filename, extension)
        #     if extension == '.m3u8':
        #         DelTS(file)
        #     bucket.delete(bucket_name, file.replace(url, '').strip())
        #     _path = filename + '.mp4'
        #     bucket.delete(bucket_name, _path.replace(url, '').strip())
        DelFile(file)
        return Response()


# 删除旧文件
class DelOldFileView(APIView):
    def post(self, request):
        filePath = request.POST.get("oldfilepath", None)
        # url = prefix_url + domain_name + '/'
        # if filePath is not None:
        #     (filepath, tempfilename) = os.path.split(filePath)
        #     (filename, extension) = os.path.splitext(tempfilename)
        #     print(filepath, tempfilename, filename, extension)
        #     if extension == '.m3u8':
        #         DelTS(filePath)
        #
        #     _path = filePath.replace(url, '').strip()
        #     mp4_path = filepath + '/' + filename + '.mp4'
        #     _mp4_path = mp4_path.replace(url, '').strip()
        #     bucket.delete(bucket_name, _path)  # 删除m3u8文件
        #     bucket.delete(bucket_name, _mp4_path)  # 删除mp4文件
        DelFile(filePath)
        return Response()


def DelFile(path):
    if path is not None:
        (filename, extension) = os.path.splitext(path)
        url = prefix_url + domain_name + '/'
        print(filename, extension)
        if extension == '.m3u8':
            DelTS(path)
        bucket.delete(bucket_name, path.replace(url, '').strip())
        _path = filename + '.mp4'
        bucket.delete(bucket_name, _path.replace(url, '').strip())


# 通过m3u8文件删除切片文件
def DelTS(url):
    r = requests.get(url=url).content.decode()

    ret_list = r.split("\n")
    # bucket = BucketManager(QiniuTool().q)
    for i in ret_list:
        if i and i[0] == "/":
            bucket.delete(bucket_name, i[1:])


# 切片
def UploadQinui(file_name):
    key = str(file_name)
    (filepath, tempfilename) = os.path.split(key)
    (filename, extension) = os.path.splitext(tempfilename)

    pattern = urlsafe_base64_encode('{0}/{1}_$(count).ts'.format(filepath, filename))
    # 设置转码参数（以视频转码为例）
    fops = 'avthumb/m3u8/noDomain/1/pattern/{0}'.format(pattern)

    saved_name = '{0}/{1}.m3u8'.format(filepath, filename)

    # 通过添加'|saveas'参数，指定处理后的文件保存的bucket和key，不指定默认保存在当前空间，bucket_saved为目标bucket，bucket_saved为目标key
    saveas_key = urlsafe_base64_encode('{0}:{1}'.format(bucket_name, saved_name))

    fops = fops + '|saveas/' + saveas_key

    pfop = PersistentFop(q, bucket_name, pipeline_name)
    ops = []
    ops.append(fops)
    ret, info = pfop.execute(key, ops, 1)
    print('----------------')
    print(ret, info)
    # if info.status_code == 200:
    #     bucket.delete(bucket_name, file_name)
    # print(info.status_code)

    base_url = prefix_url + domain_name + '/' + saved_name
    return base_url


@api_view(['POST'])
def upload_file(request):
    print(request.FILES.get("videofile", None))
    file = request.FILES.get("videofile", None)
    return Response({"url": file})

#
# @api_view(['POST'])
# def post_from_qiniu(request, format=None):
#     origin_authorization = request.META.get('HTTP_AUTHORIZATION', None)
#     access_key = re.split(r'\W', origin_authorization)[1]
#     request.data["file_url"] = "http://media.xxx.com/" + request.data["file_key"]
#     request.data["file_size"] = request.data["file_size"]
#     serializer = QiniuFilesSerializer(data=request.data)
#     if access_key == Qiniu().access_key and serializer.is_valid():
#         serializer.save()  # 把信息存储到qiniu_storage模型里
#         instance = serializer.save()
#         data = file_info_format(request.data)
#         # 使用序列化就能存入本地
#         data["id"] = instance.pk
#         return Response(data)
#     return Response({"success": False, "message": u"请求不合格"})
