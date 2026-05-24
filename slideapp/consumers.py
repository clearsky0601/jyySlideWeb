# slideapp/consumers.py

from channels.generic.websocket import AsyncWebsocketConsumer
import json
import tempfile
import os
import shutil
from .src.converter import converter
from django.conf import settings
from .models import Slide
from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.shortcuts import get_object_or_404
from .models import Slide
import traceback

class SlideConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # 检查用户是否已登录
        if self.scope["user"] == AnonymousUser():
            await self.close()
        else:
            self.slide_id = self.scope['url_route']['kwargs'].get('slide_id')
            await self.accept()

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')

        if action == 'load':
            slide_data = await self.get_slide_content()
            await self.send(text_data=json.dumps({
                'action': 'load',
                'content': slide_data['content'],
                'version': slide_data['version']
            }))
        elif action == 'save':
            markdown_content = data['markdown']
            client_version = data.get('version', -1)
            result = await self.save_slide_content(markdown_content, client_version)

            if result['conflict']:
                await self.send(text_data=json.dumps({
                    'action': 'reload',
                    'content': result['content'],
                    'version': result['version'],
                    'reason': 'conflict'
                }))
            else:
                html_result = await self.convert_markdown_to_html(markdown_content)
                if isinstance(html_result, dict) and 'error' in html_result:
                    await self.send(text_data=json.dumps({
                        'action': 'error',
                        'message': html_result['error']
                    }))
                else:
                    await self.send(text_data=json.dumps({
                        'action': 'save_ok',
                        'version': result['version'],
                        'html': html_result
                    }))
        elif action == 'preview':
            markdown_content = data['markdown']
            result = await self.convert_markdown_to_html(markdown_content)
            if isinstance(result, dict) and 'error' in result:
                await self.send(text_data=json.dumps({
                    'action': 'error',
                    'message': result['error']
                }))
            else:
                await self.send(text_data=json.dumps({
                    'action': 'preview',
                    'html': result
                }))
        elif action == 'check_version':
            version = await self.get_slide_version()
            await self.send(text_data=json.dumps({
                'action': 'version_info',
                'version': version
            }))

    @sync_to_async
    def get_slide_content(self):
        slide = Slide.objects.get(id=self.slide_id)
        return {'content': slide.content, 'version': slide.version}

    @database_sync_to_async
    def get_slide_version(self):
        return Slide.objects.filter(id=self.slide_id).values_list('version', flat=True).first()

    @sync_to_async
    def save_slide_content(self, content, client_version):
        slide = Slide.objects.get(id=self.slide_id)
        if slide.version != client_version:
            return {'conflict': True, 'content': slide.content, 'version': slide.version}
        slide.content = content
        slide.version = slide.version + 1
        slide.title = slide.extract_title_from_content()
        slide.save()
        return {'conflict': False, 'version': slide.version}

    async def convert_markdown_to_html(self, markdown_content):
        try:
            # 创建临时目录
            with tempfile.TemporaryDirectory() as temp_dir:
                # 创建临时 Markdown 文件
                temp_md_file_path = os.path.join(temp_dir, 'temp.md')
                with open(temp_md_file_path, 'w', encoding='utf-8') as temp_md_file:
                    temp_md_file.write(markdown_content)

                # 调用转换器
                converter(temp_md_file_path)

                # 读取生成的 HTML 文件
                output_html_path = os.path.join(temp_dir, 'dist', 'index.html')
                with open(output_html_path, 'r', encoding='utf-8') as html_file:
                    html_content = html_file.read()

                # 修改静态文件路径
                html_content = html_content.replace('./static/', '/static/')
                html_content = html_content.replace('./img/', '/static/img/')

                # 复制生成的图片到静态文件目录
                source_img_dir = os.path.join(temp_dir, 'dist', 'img')
                dest_img_dir = os.path.join(settings.BASE_DIR, 'static', 'img')

                if os.path.exists(source_img_dir):
                    if not os.path.exists(dest_img_dir):
                        os.makedirs(dest_img_dir)
                    for filename in os.listdir(source_img_dir):
                        shutil.copy(os.path.join(source_img_dir, filename), dest_img_dir)

                return html_content
        except Exception as e:
            # 捕获异常，记录错误日志
            error_message = ''.join(traceback.format_exception_only(type(e), e))
            print(f"转换失败: {error_message}")

            # 将错误信息返回给调用者
            return {'error': error_message}


# 新增的 PublicSlideConsumer 类
class PublicSlideConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.slide_id = self.scope['url_route']['kwargs'].get('slide_id')
        slide = await sync_to_async(Slide.objects.get)(id=self.slide_id)
        if slide.lock:
            # 如果幻灯片是锁定的，拒绝连接
            await self.close()
        else:
            await self.accept()

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')

        if action == 'load':
            # 加载指定的幻灯片内容
            content = await self.get_slide_content()
            await self.send(text_data=json.dumps({
                'action': 'load',
                'content': content
            }))
        elif action == 'preview':
            # 仅生成预览，不保存
            markdown_content = data['markdown']
            result = await self.convert_markdown_to_html(markdown_content)
            if isinstance(result, dict) and 'error' in result:
                # 如果有错误，发送错误消息
                await self.send(text_data=json.dumps({
                    'action': 'error',
                    'message': result['error']
                }))
            else:
                await self.send(text_data=json.dumps({
                    'action': 'preview',
                    'html': result
                }))

    @sync_to_async
    def get_slide_content(self):
        slide = Slide.objects.get(id=self.slide_id)
        return slide.content

    async def convert_markdown_to_html(self, markdown_content):
        try:
            # 创建临时目录
            with tempfile.TemporaryDirectory() as temp_dir:
                # 创建临时 Markdown 文件
                temp_md_file_path = os.path.join(temp_dir, 'temp.md')
                with open(temp_md_file_path, 'w', encoding='utf-8') as temp_md_file:
                    temp_md_file.write(markdown_content)

                # 调用转换器
                converter(temp_md_file_path)

                # 读取生成的 HTML 文件
                output_html_path = os.path.join(temp_dir, 'dist', 'index.html')
                with open(output_html_path, 'r', encoding='utf-8') as html_file:
                    html_content = html_file.read()

                # 修改静态文件路径
                html_content = html_content.replace('./static/', '/static/')
                html_content = html_content.replace('./img/', '/static/img/')

                # 不复制生成的图片，因为公共编辑页面不允许上传图片

                return html_content
        except Exception as e:
            # 捕获异常，记录错误日志
            error_message = ''.join(traceback.format_exception_only(type(e), e))
            print(f"转换失败: {error_message}")

            # 将错误信息返回给调用者
            return {'error': error_message}