from collections import Counter

import jieba
from flask import Flask, redirect, render_template, url_for, request

import pymongo


client = pymongo.MongoClient(host='localhost',port=27017)
db = client.JianShu1
tab = db.user


app = Flask(__name__)


# 主页显示用户名
@app.route('/',methods=['GET','POST'])
def index():
    if request.method == 'GET':
        results = tab.find({})
        list = {}
        for result in results:
            a = result['nickname']
            b = result['slug']
            list[a] = b
        return render_template('ulogin.html',list=list)
    else:
        user_slug = request.form['uid']
        return redirect(url_for('userdetail', slug=user_slug))

# 传回用户id进行查询
@app.route('/userdetail')
def userdetail():
    slug = request.args.get('slug')
    results = tab.find({'slug':slug})
    dict1 =[]
    dict2 = set()
    dict3 = {}
    dict4 = set()
    dict5 = {}
    timedict1 = []
    nums1 = []
    timedict2 = []
    nums2 = []
    list3 = []
    # 统计各种动态次数
    for result in results:
        comment_note = len(result['comment_notes'][0]['comment_note'])  # 发表评论
        like_note = len(result['comment_notes'][1]['like_note'])  # 喜欢文章
        reward_note = len(result['comment_notes'][2]['reward_note'])  # 赞赏文章
        share_note = len(result['comment_notes'][3]['share_note'])  # 发表文章
        like_user = len(result['comment_notes'][4]['like_user'])  # 关注用户
        like_collection = len(result['comment_notes'][5]['like_collection'])  # 关注专题
        like_comment = len(result['comment_notes'][6]['like_comment'])  # 点赞评论
        like_notebook = len(result['comment_notes'][7]['like_notebook'])  # 关注文集
        dict1.append(comment_note)
        dict1.append(like_note)
        dict1.append(reward_note)
        dict1.append(share_note)
        dict1.append(like_user)
        dict1.append(like_collection)
        dict1.append(like_comment)
        dict1.append(like_notebook)

        list2 = result['comment_notes'][0]['comment_note']
        for i in list2:
            list3.append(i['comm_txt'])
        list3 = str(list3)


        # 查询当前用户的所有日期
        share_notes = result['comment_notes'][3]['share_note']
        for i in range(len(share_notes)):
            dict2.add(share_notes[i]['time'][:7]) #年月 去重
            dict4.add(share_notes[i]['time'][:10]) #年月日 去重

            # 统计每个月发文章次数
        for j in dict2:
            d = 0
            for sn in share_notes:
                if sn['time'][:7] == j:
                    d += 1
            dict3[j] = d

            # 统计每天发文章次数
        for j in dict4:
            c = 0
            for sn in share_notes:
                if sn['time'][:10] == j:
                    c += 1
            dict5[j] = c

    # 按日期进行排序
    res1 = sorted(dict3.items(), key=lambda x: x[0])
    for k in res1:
        timedict1.append(str(k[0]))
        nums1.append(k[1])

    # 按日期进行排序
    res2 = sorted(dict5.items(), key=lambda x: x[0])
    for v in res2:
        timedict2.append(str(v[0]))
        nums2.append(v[1])
    # print(dict3)
    # print(dict5)

    cut = jieba.cut(list3)
    cut1 = Counter(cut).most_common(50)


    return render_template('dtfl.html',dict1=dict1,timedict1=timedict1,nums1=nums1,timedict2=timedict2,nums2=nums2,cut=cut1)


if __name__ == '__main__':
    app.run()
