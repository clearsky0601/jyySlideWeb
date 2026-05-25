import os
import json
import tempfile
import traceback
import uuid

from django.conf import settings
from django.db import transaction
from django.db.models import Max
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .models import Slide, SlideCategory
from .src.converter import converter

@login_required
def upload_image(request):
    if request.method == 'POST':
        image = request.FILES.get('image')
        if image and image.content_type.startswith('image/'):
            # 生成唯一的文件名，防止冲突
            ext = os.path.splitext(image.name)[1]
            filename = uuid.uuid4().hex + ext
            filepath = os.path.join(settings.MEDIA_ROOT, 'uploads', filename)

            # 确保上传目录存在
            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            # 保存文件
            with open(filepath, 'wb+') as destination:
                for chunk in image.chunks():
                    destination.write(chunk)

            # 返回图片的访问 URL
            url = settings.MEDIA_URL + 'uploads/' + filename
            return JsonResponse({'url': url})
        else:
            return JsonResponse({'error': '无效的文件'}, status=400)
    else:
        return JsonResponse({'error': '不支持的请求方法'}, status=405)





# slideapp/views.py
SORT_OPTIONS = {
    'manual': ('sort_order', '-updated_at', '-id'),
    'updated_desc': ('-updated_at', '-id'),
    'updated_asc': ('updated_at', 'id'),
    'created_desc': ('-created_at', '-id'),
    'created_asc': ('created_at', 'id'),
}


def get_sort(request):
    sort = request.GET.get('sort', 'manual')
    if sort not in SORT_OPTIONS:
        sort = 'manual'
    return sort


def get_slide_categories():
    return (
        SlideCategory.objects
        .order_by('position', 'name')
    )


@login_required
def index(request):
    sort = get_sort(request)
    slide_ordering = SORT_OPTIONS[sort]
    categories = list(get_slide_categories())
    uncategorized_slides = list(
        Slide.objects.filter(category_ref__isnull=True).order_by(*slide_ordering)
    )
    category_sections = [
        {
            'id': category.id,
            'name': category.name,
            'slides': list(category.slides.all().order_by(*slide_ordering)),
        }
        for category in categories
    ]
    total_slides = Slide.objects.count()
    return render(request, 'index.html', {
        'category_sections': category_sections,
        'uncategorized_slides': uncategorized_slides,
        'total_slides': total_slides,
        'total_categories': len(categories),
        'sort': sort,
        'sort_options': SORT_OPTIONS,
    })

@login_required
def create_slide(request):
    # 获取当前文件所在的目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # 默认内容文件的路径
    default_content_path = os.path.join(current_dir, 'default_content.md')

    # 读取默认内容
    with open(default_content_path, 'r', encoding='utf-8') as f:
        default_content = f.read()

    # 创建新的幻灯片，并设置默认内容
    next_order = (Slide.objects.filter(category_ref__isnull=True).aggregate(Max('sort_order'))['sort_order__max'] or 0) + 1
    slide = Slide.objects.create(
        title='未命名',
        content=default_content,
        lock=True,
        sort_order=next_order,
    )

    return redirect('edit_slide', slide_id=slide.id)

@login_required
def edit_slide(request, slide_id):
    slide = Slide.objects.get(id=slide_id)
    return render(request, 'edit_slide.html', {'slide': slide})

@login_required
def delete_slide(request, slide_id):
    slide = get_object_or_404(Slide, id=slide_id)
    slide.delete()
    return JsonResponse({'status': 'success'})

@login_required
@require_POST
def toggle_lock(request, slide_id):
    slide = get_object_or_404(Slide, id=slide_id)
    # 切换锁定状态
    slide.lock = not slide.lock
    slide.save()
    return JsonResponse({'status': 'success', 'lock': slide.lock})


@login_required
@require_POST
def update_category(request, slide_id):
    slide = get_object_or_404(Slide, id=slide_id)
    category = request.POST.get('category', '').strip()
    slide.category = category[:100]
    slide.save(update_fields=['category', 'updated_at'])
    next_url = request.POST.get('next')
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        return redirect(next_url)
    return redirect('index')


@login_required
@require_POST
def create_category(request):
    name = request.POST.get('name', '').strip()[:100]
    if not name:
        return JsonResponse({'error': '分类名称不能为空'}, status=400)

    position = (SlideCategory.objects.aggregate(Max('position'))['position__max'] or 0) + 1
    category, created = SlideCategory.objects.get_or_create(
        name=name,
        defaults={'position': position},
    )
    return JsonResponse({
        'status': 'success',
        'created': created,
        'category': {'id': category.id, 'name': category.name},
    })


@login_required
@require_POST
def rename_category(request, category_id):
    category = get_object_or_404(SlideCategory, id=category_id)
    name = request.POST.get('name', '').strip()[:100]
    if not name:
        return JsonResponse({'error': '分类名称不能为空'}, status=400)
    if SlideCategory.objects.exclude(id=category.id).filter(name=name).exists():
        return JsonResponse({'error': '这个分类名已经存在'}, status=400)

    category.name = name
    category.save(update_fields=['name', 'updated_at'])
    Slide.objects.filter(category_ref=category).update(category=name)
    return JsonResponse({'status': 'success', 'name': category.name})


@login_required
@require_POST
def delete_category(request, category_id):
    category = get_object_or_404(SlideCategory, id=category_id)
    action = request.POST.get('action')

    if action not in ('uncategorize', 'delete_slides'):
        return JsonResponse({'error': '无效的删除方式'}, status=400)

    with transaction.atomic():
        slide_count = category.slides.count()
        if action == 'uncategorize':
            next_order = (Slide.objects.filter(category_ref__isnull=True).aggregate(Max('sort_order'))['sort_order__max'] or 0) + 1
            for offset, slide in enumerate(category.slides.order_by('sort_order', '-updated_at', '-id')):
                slide.category_ref = None
                slide.category = ''
                slide.sort_order = next_order + offset
                slide.save(update_fields=['category_ref', 'category', 'sort_order', 'updated_at'])
        else:
            category.slides.all().delete()

        category.delete()

    return JsonResponse({'status': 'success', 'slide_count': slide_count})


@login_required
@require_POST
def reorder_slides(request):
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return JsonResponse({'error': '无效的排序数据'}, status=400)

    category_id = payload.get('category_id')
    slide_ids = payload.get('slide_ids')
    if not isinstance(slide_ids, list):
        return JsonResponse({'error': 'slide_ids 必须是数组'}, status=400)

    category = None
    if category_id not in (None, '', 'uncategorized'):
        category = get_object_or_404(SlideCategory, id=category_id)

    clean_ids = []
    for slide_id in slide_ids:
        try:
            clean_ids.append(int(slide_id))
        except (TypeError, ValueError):
            return JsonResponse({'error': 'slide id 无效'}, status=400)

    with transaction.atomic():
        slides = {slide.id: slide for slide in Slide.objects.filter(id__in=clean_ids)}
        for position, slide_id in enumerate(clean_ids):
            slide = slides.get(slide_id)
            if not slide:
                continue
            slide.category_ref = category
            slide.category = category.name if category else ''
            slide.sort_order = position
            slide.save(update_fields=['category_ref', 'category', 'sort_order', 'updated_at'])

    return JsonResponse({'status': 'success'})


def public_slides(request):
    sort = get_sort(request)
    slide_ordering = SORT_OPTIONS[sort]
    categories = list(SlideCategory.objects.filter(slides__lock=False).distinct().order_by('position', 'name'))
    uncategorized_slides = list(
        Slide.objects.filter(lock=False, category_ref__isnull=True).order_by(*slide_ordering)
    )
    category_sections = [
        {
            'id': category.id,
            'name': category.name,
            'slides': list(category.slides.filter(lock=False).order_by(*slide_ordering)),
        }
        for category in categories
    ]
    total_slides = Slide.objects.filter(lock=False).count()
    return render(request, 'public_slides.html', {
        'category_sections': category_sections,
        'uncategorized_slides': uncategorized_slides,
        'total_slides': total_slides,
        'total_categories': len(categories),
        'sort': sort,
        'sort_options': SORT_OPTIONS,
    })

def public_edit_slide(request, slide_id):
    slide = get_object_or_404(Slide, id=slide_id, lock=False)

    # 转换Markdown为HTML
    slide_html = convert_markdown_to_html(slide.content)

    return render(request, 'public_edit_slide.html', {'slide': slide, 'slide_html': slide_html})


def convert_markdown_to_html(markdown_content):
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_md_file_path = os.path.join(temp_dir, 'temp.md')
            with open(temp_md_file_path, 'w', encoding='utf-8') as temp_md_file:
                temp_md_file.write(markdown_content)

            # 调用转换器
            converter(temp_md_file_path)

            output_html_path = os.path.join(temp_dir, 'dist', 'index.html')
            with open(output_html_path, 'r', encoding='utf-8') as html_file:
                html_content = html_file.read()

            html_content = html_content.replace('./static/', '/static/')
            html_content = html_content.replace('./img/', '/static/img/')

            return html_content
    except Exception as e:
        error_message = ''.join(traceback.format_exception_only(type(e), e))
        print(f"转换失败: {error_message}")
        return f"<p>转换失败: {error_message}</p>"
