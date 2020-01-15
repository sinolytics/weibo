from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import permission_required
from django.conf import settings
import json
mg_wu = settings.MG_WU

def login_v(request):
    username = request.GET['username']
    password = request.GET['password']
    user = authenticate(request, username=username, password=password)
    if user is not None:
        login(request, user)
        return HttpResponse("ok")
    else:
        return HttpResponse("error")

def logout_v(request):
    logout(request)
    return HttpResponse("ok")

def no_login_v(request):
    from django.contrib.auth.hashers import make_password
    return HttpResponse("未登入" + make_password("admin"))


@login_required(login_url='/no_login/')
@permission_required('my.visit', raise_exception=True)
def auth_v(request):
    return HttpResponse("auth ok")

@login_required(login_url='/auth/login/')
def index(request):
    return render(request, "index.html")

def query_base(request):
    q = dict(request.GET.dict(), **request.POST.dict())
    print(json.dumps(q, indent=4, ensure_ascii=False))
    page = int(q.get('page', 1))
    pageSize = int(q.get('pageSize', 10))
    filters = json.loads(q.get('filter', "{}"))
    sort = json.loads(q.get('sort', "[]"))
    d = mg_wu.find(filters, {"_id": 0})
    if sort:
        d.sort(sort)
    if page > 0:
        d.skip((page - 1) * pageSize).limit(pageSize)
    return {
        'total': d.count(),
        'data': list(d)
    }

@permission_required('my.visit')
def get_weibo_user(request):
    try:
        data = {"code": 0, "data": query_base(request)}
    except Exception as e:
        data = {"code": 1, "msg": "%s" % e}
    return JsonResponse(data)

"""
前端
根据抓取的微博数据向配置文件添加更多信息。
与相关用户联系的员工将使用该系统，并添加信息以跟踪他们与谁联系以及协作方式。

最初会有三种不同的登录类别：管理员，Seeder，客户服务。最后两个应该分配给他们使用的品牌。

步骤1：使用抓取的微博配置文件创建配置文件。
步骤2：允许Seeder向个人资料添加更多信息，包括其他社交媒体帐户，对个人资料进行分类的“标签”以及新的协作。
步骤3：从品牌的25个配置文件中分配每个播种机，以开始联系。配置文件在分配之前应该能够被管理员过滤。例如，仅分配15w-25w关注者的个人资料。
步骤4：允许播种者将配置​​文件向下移动到管道中。因此，当他们选择与某人联系时，个人资料将移至“已联系”，而当他们开始进行协作时，其个人资料将移至“合作”。在协作中，请确保可以添加与协作相关的多个帖子。
步骤5：允许客户服务登录名搜索分配给协作的促销代码，并查看它们的有效日期。还允许他们添加客户使用代码时的销售数据。该销售应添加到与单个代码关联的数据以及包含该代码的配置文件中
"""