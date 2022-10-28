import math
from django.http.response import JsonResponse, HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from django.core.paginator import Paginator
import urllib.parse

from myapp02.models import Comment
from myapp02.models import Board

# Create your views here.
UPLOAD_DIR = 'C:/django/myProject02/upload/'

def base(request):
    return render(request, 'base.html')

def write(request):
    return render(request, 'board/insert.html')

@csrf_exempt
def insert(request):
    fname=''
    fsize=0

    if 'file' in request.FILES:
        file = request.FILES['file']
        fname = file.name
        fsize = file.size
        
        fp = open('%s%s' %(UPLOAD_DIR, fname), 'wb')
        
        for chunk in file.chunks():
            fp.write(chunk)
        fp.close()

    dto = Board(
        writer = request.POST['writer'],
        title = request.POST['title'],
        content = request.POST['content'],
        filename = fname,
        filesize = fsize
        ) 
    dto.save()
    return redirect('/list/')

def list(request):
    page = request.GET.get('page', 1)
    word = request.GET.get('word', '')
    field = request.GET.get('field', 'title')

    pageSize = 5
    blockPage = 3
    currentPage = int(page)

    start = (currentPage-1)*pageSize
    startPage = math.floor((currentPage-1)/blockPage)*blockPage+1
    endPage = startPage+blockPage-1

    if field == 'title':
        boardList = Board.objects.filter(Q(title__contains=word)).order_by('-id')[start:start+pageSize]
        boardCount = Board.objects.filter(Q(title__contains=word)).count()
    elif field == 'writer':
        boardList = Board.objects.filter(Q(writer__contains=word)).order_by('-id')[start:start+pageSize]
        boardCount = Board.objects.filter(Q(writer__contains=word)).count()
    elif field == 'content':
        boardList = Board.objects.filter(Q(content__contains=word)).order_by('-id')[start:start+pageSize]
        boardCount = Board.objects.filter(Q(content__contains=word)).count()
    elif field == 'all':
        boardList = Board.objects.filter(Q(writer__contains=word)|Q(title__contains=word)|Q(content__contains=word)).order_by('-id')[start:start+pageSize]
        boardCount = Board.objects.filter(Q(title__contains=word)|Q(writer__contains=word)|Q(content__contains=word)).count()
    else:
        boardList = Board.objects.all().order_by('-id')
        boardCount = Board.objects.all().count()

    totPage = math.ceil(boardCount/pageSize)
    
    if endPage > totPage:
        endPage = totPage

    context = { 'boardList' : boardList, 
                'currentPage' : currentPage, 
                'startPage' : startPage, 
                'blockPage' : blockPage, 
                'endPage' : endPage, 
                'totPage' : totPage,
                'boardCount' : boardCount,
                'field' : field,
                'word' : word,
                'range' : range(startPage, endPage+1)
                }
    return render(request, 'board/list.html', context)

def download_count(request):
    id = request.GET['id']

    dto = Board.objects.get(id=id)
    dto.down_up()
    dto.save()
    count=dto.down
    return JsonResponse({'id':id, 'count':count})

def download(request):
    id = request.GET['id']
    dto = Board.objects.get(id=id)
    path = UPLOAD_DIR+dto.filename

    filename = urllib.parse.quote(dto.filename)
    print('filename: ', filename)
    with open(path, 'rb') as file:
        response = HttpResponse(file.read(), content_type='application/octet-stream')
        response['Content-Disposition'] = "attachment;filename*=UTF-8''{0}".format(filename)
    return response

def list_page(request):
    page = request.GET.get('page', 1)
    word = request.GET.get('word', '')

    boardCount = Board.objects.filter(Q(writer__contains=word)|Q(title__contains=word)|Q(content__contains=word)).count()

    boardList = Board.objects.filter(Q(writer__contains=word)|Q(title__contains=word)|Q(content__contains=word)).order_by('-id')

    pageSize = 5

    # 페이징처리
    paginator = Paginator(boardList, pageSize) # import
    page_obj = paginator.get_page(page)
    print('boardCount : ', boardCount)

    rowNo = boardCount-(int(page)-1)*pageSize
    
    context ={'page_list':page_obj, 
             'page':page,
             'rowNo':rowNo, 
             'word':word, 
             'boardCount':boardCount}
    return render(request, 'board/list_page.html', context)

def detail(request, board_id):
    dto = Board.objects.get(id=board_id)
    dto.hit_up()
    dto.save()
    context = {'dto':dto}
    return render(request, 'board/detail.html', context)

def detail_id(request):
    id = request.GET['id']
    dto = Board.objects.get(id=id)
    dto.hit_up()
    dto.save()
    context = {'dto':dto}
    return render(request, 'board/detail.html', context)

def update_form(request, board_id):
    dto = Board.objects.get(id=board_id)
    return render(request, 'board/update.html', {'dto':dto})

@csrf_exempt
def update(request):
    id = request.POST['id']
    dto = Board.objects.get(id=id)
    fname = dto.filename
    fsize = dto.filesize

    if 'file' in request.FILES:
        file = request.FILES['file']
        fname = file.name
        fsize = file.size

        fp = open('%s%s' %(UPLOAD_DIR, fname), 'wb')

        for chunk in file.chunks():
            fp.write(chunk)
        fp.close()
    
    update_dto = Board(id=request.POST['id'],
        writer=request.POST['writer'],
        title = request.POST['title'],
        content = request.POST['content'],
        filename = fname,
        filesize = fsize
        )
    update_dto.save()
    return redirect('/list')

def delete(request, board_id):
    dto = Board.objects.get(id=board_id)
    dto.delete()
    return redirect('/list')

@csrf_exempt
def comment(request):
    id = request.POST['id']
    dto = Comment(
        board_id = id,
        writer = 'aa',
        content = request.POST['content']
        )
    dto.save()
    return redirect('/detail/'+id)
