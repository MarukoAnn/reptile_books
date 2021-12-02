import multiprocessing
import os
import re
import time
import urllib.request
from bs4 import BeautifulSoup


# 获取页面信息
def get_pages(url):
    soup = ''

    try:
        # 创建请求日志文件夹
        if 'Log' not in os.listdir('.'):
            os.makedirs(r".\Log")

        # 请求当前章节页面，parmas为请求参数
        request = urllib.request.Request(url)
        response = urllib.request.urlopen(request)
        content = response.read()
        # 转换编码
        data = content.decode('gbk')
        # soup 转换
        soup = BeautifulSoup(data, 'html.parser')

    except Exception as e:
        print(url+"请求错误")
        with open(r".\Log\req_error.txt", 'a', encoding='utf-8') as f:
            f.write(url + "请求错误\n")
        f.close()
    return soup

# 下载每个章节
def get_chart_text(url, title, num):
    soup = get_pages(url)
    # 获取章节名称
    subtitle = soup.select('#chaptername')[0].text
    # 判断是否有感言
    if re.search(r".*?章", subtitle) is None:
        return

    # 获取章节文本
    content = soup.select("#txt")[0].text
    # 按照指定格式替换章节内容，运用正则
    content = re.sub(r'\(.*?\)', '', content)
    content = re.sub(r'\r\n', '', content)
    content = re.sub(r'\n+', '\n', content)
    content = re.sub(r'<.*?>+', '', content)

    try:
        with open(r'.\%s \%s %s.text' %(title, num, subtitle), 'w', encoding='utf-8') as f:
            f.write(subtitle + content)
        f.close()
        print(num, subtitle, '下载成功')
    except Exception as e:
        print(subtitle, '下载失败', url)
        error_path = '.\Error\%s'%(title)

        # 创建错误文件
        try:
            os.makedirs(error_path)
        except Exception as e:
            pass
        # 写入错误文件
        with open("%s\error_url.txt" % (error_path), 'a', encoding='utf-8') as f:
            f.write(subtitle + "下载失败" + url + '\n')

        f.close()
    return

# 下载一本书
def thred_getOneBook(indexUrl):
    soup = get_pages(indexUrl)
    # 获取书名
    title = soup.select(".book-text")[0].select('h1')[0].text

    # 根据书名字创建文件夹
    if title not in os.listdir('.'):
        os.makedirs(r".\%s" % title)
        print(title, "文件创建成功------------------")

    # 加载次进程下载开始得时间
    print("下载 %s 得PID：%s..." % (title, os.getpid()))
    start = time.time()

    # 获取这本书所有得章节
    charts_url = []
    # 提取出书得每个章节不变得url
    indexUrl = re.sub(r'index.html', '', indexUrl)

    charts = soup.select(".cf li a")
    print(charts)
    for i in charts:
        print(indexUrl + i.attrs['href'])
        charts_url.append(indexUrl + i.attrs['href'])
    # 去重
    charts_url = list(set(charts_url))

    print('目录列表： %s' % charts_url )

    # 创建下载这本书得进程
    p = multiprocessing.Pool()
    # 自己在下载得文件上加上编号，防止有得文章有上、中、下 三卷导致有三个第一章
    num = 1

    for i in charts_url:
        p.apply_async(get_chart_text, args=(i, title, num))
        num += 1

    print("等待 %s 所有得章节被加载..." % (title))
    p.close()
    p.join()
    end = time.time()
    print("下载 %s 完成，运行时间 %0.2f s." % (title, (end - start)))
    print("开始生成 %s ...." % title)
    # 合成一本书
    sort_allCharts(r".", "%s.text" % title)
    return

# 下载多本书
def process_getAllBook(base):
    # 输入你要下载书得首页地址
    print("主程序得PID： %s" % os.getpid())

    book_list_url = []

    print("-----------开始下载---------------------")
    p = []
    for i in book_list_url:
        p.append(multiprocessing.Process(target=thred_getOneBook, args=(i,)))
    print("等待所有得主进程加载完成........")
    for i in p:
        i.start()
    for i in p:
        i.join()
    print("---------------------全部下载完成-------------------------------")
    return


# 合成一本书
def sort_allCharts(path, filename):
    lists = os.listdir(path)
    # 对文件排序
    # lists.sort(key=lambda i:int(re.match(r'(\d+)', i).group()))
    # 删除旧的书
    if os.path.exists(filename):
        os.remove(filename)
        print("旧的书 %s 已被删除" % filename)

    # 创建新书
    with open(r'.\%s' % (filename), 'a', encoding="utf-8") as f:
        for i in lists:
            with open(r"%s \ %s" % (path, i), 'r', encoding='utf-8') as temp:
                f.writelines(temp.readlines())
            temp.close()
    f.close()
    print("新的书 %s 已经被创建在当前目录 %s" % (filename, os.path.abspath(filename)))
    return


if __name__ == '__main__':
    thred_getOneBook('https://www.yxlmdl.net/book/4355/')