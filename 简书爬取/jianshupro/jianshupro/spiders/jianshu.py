import datetime
import re

import scrapy
from scrapy import Request
from fake_useragent import UserAgent

from jianshupro.items import JianshuproItem


class JianshuSpider(scrapy.Spider):
    name = 'jianshu'
    allowed_domains = ['jianshu.com']
    start_urls = ['http://www.jianshu.com/']
    base_headers = {'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6,zh-TW;q=0.4',
                    'Host': 'www.jianshu.com',
                    'Accept-Encoding': 'gzip, deflate, sdch',
                    'X-Requested-With': 'XMLHttpRequest',
                    'Accept': 'text/html, */*; q=0.01',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36',
                    'Connection': 'keep-alive',
                    'Referer': 'http://www.jianshu.com'}
    # 只加载列表模块
    ajax_headers = dict(base_headers, **{"X-PJAX": "true", 'User-Agent': UserAgent().random})
    timeline_data = {}
    def start_requests(self):
        yield Request('http://www.jianshu.com/recommendations/users?page=1&per_page=200',
                      headers=self.base_headers)

    def parse(self, response):
        user_id_list = response.xpath('//div[@class="row"]/div/div/a/@href').extract()
        for user_id in user_id_list:
            # 判断得到的字符串是否是所要的格式
            if '/users/' not in user_id:
                continue
            user = user_id.split('/')[-1]
            # user ='5660f7663c80'
            self.timeline_data = [
                {'comment_note': []},  # '发表评论'
                {'like_note': []},  # '喜欢文章'
                {'reward_note': []},  # '赞赏文章'
                {'share_note': []},  # '发表文章'
                {'like_user': []},  # '关注用户'
                {'like_collection': []},  # '关注专题'
                {'like_comment': []},  # '点赞评论'
                {'like_notebook': []},  # '关注文集'
            ]
            yield Request(url=f'http://www.jianshu.com/u/{user}',callback=self.parse_seeduser,headers=self.base_headers,meta={'slug': user})

            self.page = 1
            # yield Request(url=f'https://www.jianshu.com/users/{user}/followers?page={self.page}',callback=self.parse_followers,headers=self.base_headers,meta={'slug': user,'page':self.page})







    def parse_seeduser(self,response):
        self.item = JianshuproItem()
        slug = response.meta['slug']# 标识
        div_main_top = response.xpath('//div[@class="main-top"]')#得到个人个人详情界面的主要详情头
        nickname = div_main_top.xpath('.//div[@class="title"]/a/text()').extract_first()# 昵称
        head_pic = div_main_top.xpath('.//a[@class="avatar"]/img/@src').extract_first()  # 头像
        gender_tmp = div_main_top.xpath('.//div[@class="title"]/i/@class').extract_first()# 是否认证性别
        all_nums_first = div_main_top.xpath('.//div[@class="meta-block"]/a/p/text()').extract()#得到关注粉丝文章数
        following_num = all_nums_first[0]#关注
        followers_num = all_nums_first[1]#粉丝
        articles_num = all_nums_first[2]#文章
        all_nums_second = div_main_top.xpath('.//div[@class="info"]/ul/li/div[@class="meta-block"]/p/text()').extract()#得到字数收获喜欢总资产数
        words_num = all_nums_second[0]#字数
        be_liked_num = all_nums_second[1]#收获喜欢

        # 判断是否认证男女未认证则为No
        if gender_tmp:
            gender = gender_tmp.split('-')[-1]
        else:
            gender = 'No'
        self.item['nickname'] = nickname
        self.item['slug'] = slug
        self.item['head_pic'] = head_pic
        self.item['gender'] = gender
        self.item['following_num'] = int(following_num)
        self.item['followers_num'] = int(followers_num)
        self.item['articles_num'] = int(articles_num)
        self.item['words_num'] = int(words_num)
        self.item['be_liked_num'] = int(be_liked_num)
        yield Request(url=f'https://www.jianshu.com/users/{slug}/timeline?', callback=self.parse_schedule,
                      headers=self.base_headers, meta={'slug': slug,'page': self.page})
        # yield self.item

        # print(self.item)
        pass

    def parse_followers(self,response):
        self.item = JianshuproItem()
        div_list_main = response.xpath('//div[@id="list-container"]/ul[@class="user-list"]/li')

        for div in div_list_main:
            nickname = div.xpath('.//div/a/text()').extract_first()
            # print(nickname)
            slug = div.xpath('.//div/a/@href').extract_first()
            slug=slug.split('/')[-1]
            head_pic = div.xpath('.//a[@class="avatar"]/img/@src').extract_first()
            gender_tmp = div.xpath('.//div/i/@class').extract_first()
            if gender_tmp:
                gender = gender_tmp.split('-')[-1]
            else:
                gender = 'No'
            all_nums_first = div.xpath('.//div/div/span/text()').extract()

            following_num = all_nums_first[0].split()[1]
            # print(following_num)
            followers_num = all_nums_first[1].split()[1]
            articles_num = all_nums_first[2].split()[1]
            all_nums_second = div.xpath('.//div/div[2]/text()').extract()
            all_nums_second=all_nums_second[0].split()
            words_num = all_nums_second[1]
            be_liked_num = all_nums_second[3]
            self.item['nickname'] = nickname
            self.item['slug'] = slug
            self.item['head_pic'] = head_pic
            self.item['gender'] = gender
            self.item['following_num'] = int(following_num)
            self.item['followers_num'] = int(followers_num)
            self.item['articles_num'] = int(articles_num)
            self.item['words_num'] = int(words_num)
            self.item['be_liked_num'] = int(be_liked_num)
            yield self.item
            # print(words_num,be_liked_num)
        # print(response.text)

    def parse_schedule(self, response):

        slug = response.meta['slug']

        # print(f'解析当前作者动态信息，作者标识：{slug}')
        # 获取所有文章项目
        li = response.xpath('//ul[@class="note-list"]/li')
        if li:
        # 遍历所有文章区域
            for it in li:
                # 获取li元素id属性值
                # xid=it.xpath('./@id').extract_first()
                # print(f'动态id:{xid}')
                # 判断当前动态项是喜欢文章
                if it.xpath('.//span[@data-type="like_note"]'):
                    # 喜欢文章
                    xtime = self.extract_time(it, "like_note")
                    # 喜欢文章的id
                    href_id = it.xpath('.//a[@class="title"]/@href').extract()[0].split('/')[-1]
                    href_name = it.xpath('.//a[@class="title"]/text()').extract_first()
                    self.timeline_data[1]['like_note'].append({'time':xtime,'book_id':href_id,'book_name':href_name})
                    # print(f'喜欢文章url:{xhref},时间:{xtime}')
                elif it.xpath('.//span[@data-type="share_note"]'):
                    # 发表文章
                    xtime = self.extract_time(it, "share_note")
                    href_id = it.xpath('.//a[@class="title"]/@href').extract()[0].split('/')[-1]
                    href_name = it.xpath('.//a[@class="title"]/text()').extract_first()

                    self.timeline_data[3]['share_note'].append({'time':xtime,'book_id':href_id,'book_name':href_name})

                elif it.xpath('.//span[@data-type="comment_note"]'):
                    # 发表评论
                    xtime = self.extract_time(it, "comment_note")
                    #  评论文字
                    comm_txt1 = it.xpath('.//div[@class="content"]/p/a/text()').extract_first()
                    if comm_txt1:
                        comm_txt4 = it.xpath('.//div[@class="content"]/p').extract_first()
                        comm_txt3 =  re.sub('<img.*?height="20">','',comm_txt4,re.S)
                        comm_txt2 = re.findall('.*?</a>(.*?)</p>',comm_txt3,re.S)
                        # print(comm_txt2)
                        comm_txt = comm_txt1 + comm_txt2[0]
                    else:
                        comm_txt = it.xpath('.//div[@class="content"]/p/text()').extract_first()


                    # print(comm_txt.strip())
                    # 对应文章的url
                    arti_slug = it.xpath('.//blockquote/a/@href').extract()[0].split('/')[-1]
                    arti_name = it.xpath('.//blockquote/a/text()').extract_first()

                    self.timeline_data[0]['comment_note'].append({'time':xtime,'book_id':arti_slug,'book_name':arti_name,'comm_txt':comm_txt.strip()})
                    # print(f'发表评论,文章url:{arti_slug},comm_txt:{comm_txt.strip()},时间:{xtime}')
                    # print(f'comm_txt:{comm_txt1}')
                elif it.xpath('.//span[@data-type="reward_note"]'):
                    # 赞赏文章
                    xtime = self.extract_time(it, "reward_note")
                    # 赞文章id
                    href_id = it.xpath('.//a[@class="title"]/@href').extract()[0].split('/')[-1]
                    href_name = it.xpath('.//a[@class="title"]/text()').extract_first()
                    self.timeline_data[2]['reward_note'].append({'time':xtime, 'book_id':href_id,'book_name':href_name})
                elif it.xpath('.//span[@data-type="like_user"]'):
                    # 关注用户
                    xtime = self.extract_time(it, "like_user")
                    # 赞文章id
                    href_id = it.xpath('.//a[@class="title"]/@href').extract()[0].split('/')[-1]
                    href_name = it.xpath('.//a[@class="title"]/text()').extract_first()
                    self.timeline_data[4]['like_user'].append({'time':xtime,'href_name':href_name,'href_id':href_id})
                elif it.xpath('.//span[@data-type="like_collection"]'):
                    # 关注专题
                    xtime = self.extract_time(it,"like_collection")

                    collection_id = it.xpath('.//a[@class="title"]/@href').extract_first()
                    collection_name = it.xpath('.//a[@class="title"]/text()').extract_first()
                    special_id = it.xpath('.//a[@class="creater"]/@href').extract()[0].split('/')[-1]
                    special_name = it.xpath('.//a[@class="creater"]/text()').extract_first()
                    all_nums = it.xpath('.//div[@class="info"]/p').extract_first()
                    nums = re.findall('.*?编，(\d+) 篇文章，(\d+).*?',all_nums,re.S)
                    articles_num = int(nums[0][0])
                    be_liked_num = int(nums[0][1])
                    # print(nums)
                    # print(articles_num)
                    # print(all_nums)

                    self.timeline_data[5]['like_collection'].append({'time':xtime,'collection_name':collection_name,'collection_id':collection_id,'editorname':special_name,'editorid':special_id,'articles_num': articles_num, 'likes': be_liked_num})
                elif it.xpath('.//span[@data-type="like_comment"]'):
                    # 点赞评论
                    xtime = self.extract_time(it,"like_comment")

                    href_id = it.xpath('.//blockquote/div/a/@href').extract()[0].split('/')[-1]
                    href_name = it.xpath('.//blockquote/div/a/text()').extract_first()
                    book_id = it.xpath('.//blockquote/div/span/a/@href').extract()[0].split('/')[-1]
                    book_name = it.xpath('.//blockquote/div/span/a/text()').extract_first()
                    comment = it.xpath('.//p[class="comment"]/text()').extract_first()
                    self.timeline_data[6]['like_comment'].append({'time':xtime,'href_id':href_id,'href_name':href_name,'book_id':book_id,'book_name':book_name,'comment':comment})

                elif it.xpath('.//span[@data-type="like_notebook"]'):
                    # 关注文集
                    xtime = self.extract_time(it,"like_notebook")

                    anthology_id = it.xpath('.//a[@class="title"]/@href').extract()[0].split('/')[-1]
                    anthology_name = it.xpath('.//a[@class="title"]/text()').extract_first()

                    special_id = it.xpath('.//a[@class="creater"]/@href').extract()[0].split('/')[-1]
                    special_name = it.xpath('.//a[@class="creater"]/text()').extract_first()

                    all_nums = it.xpath('.//div[@class="info"]/p').extract_first()
                    nums = re.findall('.*?编，(\d+) 篇文章，(\d+).*?',all_nums,re.S)
                    articles_num = int(nums[0][0])
                    be_liked_num = int(nums[0][1])

                    self.timeline_data[7]['like_notebook'].append({'time':xtime,'anthology_name':anthology_name,'anthology_id':anthology_id,'editorname':special_name,'editorid':special_id,'articles_num': articles_num, 'likes': be_liked_num})
            # 获取下一页max_id取值
            tid = li[-1].xpath('./@id').extract_first()
            tid = int(tid.split('-')[-1])
            # print(self.timeline_data)
            xurl = f'https://www.jianshu.com/users/{slug}/timeline?max_id={tid - 1}&page={self.page}'
            self.page += 1
            # 提交下一个分页请求
            yield Request(url=xurl, callback=self.parse_schedule,
                          headers=self.base_headers, meta={'slug': slug})
        else:
            self.item['comment_notes'] = self.timeline_data
            print(self.item)
            yield self.item


    def extract_time(self, it,itname):
        # print(f'提取时间:{it}')
        xtime = it.xpath(f'.//span[@data-type="{itname}"]/@data-datetime').extract_first()
        xtime = xtime.split('+')[0].replace('T', ' ')
        # xtime = datetime.datetime.strptime(xtime, "%Y-%m-%d %H:%M:%S")
        return xtime


