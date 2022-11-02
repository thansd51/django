import json
from django.db.models.aggregates import Count
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from django.core.paginator import Paginator
from django.http.response import JsonResponse, HttpResponse
import urllib.parse
from .forms import UserForm
import pandas as pd
from myapp03.models import Board, Comment, Forecast, Movie
from myapp03 import bigdataProcess

# Create your views here.

UPLOAD_DIR = 'C:/django/myProject03/upload/'

# 멜론 차트
def melon(request):
    datas = []
    bigdataProcess.melon_crawling(datas)
    return render(request, "bigdata/melon.html", {'datas':datas})

# 날씨 그래프
def weather(request):
    last_date = Forecast.objects.values('tmef').order_by('-tmef')[:1]
    weather = {}
    bigdataProcess.weather_crawling(last_date, weather)
    print('last_date query: ', str(last_date.query))

    for i in weather:
        for j in weather[i]:
            dto = Forecast(city=i, tmef=j[0], wf=j[1], tmn=j[2], tmx=j[3])
            dto.save()
    result = Forecast.objects.filter(city='부산')
    result1 = Forecast.objects.filter(city='부산').values('wf').annotate(dcount = Count('wf')).values('dcount', 'wf')
    print('result1 query: ', str(result1.query))
    df = pd.DataFrame(result1)

    image_dic = bigdataProcess.weather_make_chart(result, df.wf, df.dcount)
    return render(request, "bigdata/weather_chart.html", {'img_data':image_dic}) 

# 지도
def map(request):
    bigdataProcess.map()
    return render(request, "bigdata/map_view.html")

# 워드클라우드
def wordcloud(request):
    word_path = "C:/django/myProject03/data/"
    data = json.loads(open(word_path+'4차 산업혁명.json', 'r', encoding='utf-8').read())
    bigdataProcess.make_wordCloud(data)
    return render(request, "bigdata/wordchart.html", {'img_data': 'k_wordCloud.png'})

def movie(request):
    data = []
    bigdataProcess.movie_crawling(data)
    for i in data:
        dto = Movie(title=i[0], point=i[1], content=i[2])
        dto.save()
    dto = Movie.objects.all()
    return render(request, "bigdata/movie.html", {'dto': dto})

def graph(request):
    bigdataProcess.crawling()
    return render(request, "bigdata/graph.html", {'graph' : 'graph.png'})

def base(request):
    return render(request, 'base.html')

@login_required(login_url='/login/')
def write(request):
    return render(request,"board/insert.html")

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
        writer = request.user,
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

    boardCount = Board.objects.filter(
        Q(title__contains=word) |
        Q(writer__username__contains=word) |
        Q(content__contains=word)
        ).count()
    boardList = Board.objects.filter(
        Q(title__contains=word) |
        Q(writer__username__contains=word) |
        Q(content__contains=word)
    ).order_by('-id')

    pageSize = 3

    paginator = Paginator(boardList, pageSize)
    page_obj = paginator.get_page(page)

    rowNo = boardCount - (int(page)-1) * pageSize

    context = {
        'pageList':page_obj,
        'page':page,
        'rowNo':rowNo,
        'word':word,
        'boardCount':boardCount
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

def detail(request, board_id):
    dto = Board.objects.get(id=board_id)
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
        writer=request.user,
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
@login_required(login_url='/login/')
def comment(request):
    id = request.POST['id']
    board = get_object_or_404(Board, pk=id)
    dto = Comment(
        writer = request.user,
        content = request.POST['content'],
        board = board
        )
    dto.save()
    return redirect('/detail/'+id)

# sign up
def signup(request):
    if request.method == "POST": # 회원가입 insert
        form =UserForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)

            login(request, user)
            return redirect("/")
        else:
            print('signup POST unvalid')
    else: # 회원가입폼으로
        form = UserForm()

    return render(request, 'common/signup.html', {'form':form})
