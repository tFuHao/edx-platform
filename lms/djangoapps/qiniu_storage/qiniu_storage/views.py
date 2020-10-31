from django.views.generic import View
from django.shortcuts import render

class QiniuView(View):
    def get(self, request):
        # hashkey验证码生成的秘钥，image_url验证码的图片地址
        hashkey = '132154651313131dfsdfdsfdsfds'

        return render(request, 'qiniu.html',
                      {
                          'hashkey': hashkey,
                      })

