import json
import os
import argparse
import requests

os.chdir(os.path.dirname(os.path.abspath(__file__)))
with open('bbs.json', 'r', encoding='utf-8') as bbs, open('data.json', 'r', encoding='utf-8') as data:
    bbsjson = json.load(bbs)
    mydata = json.load(data)

parser = argparse.ArgumentParser()
parser.add_argument("group")

def get_cookie(my_account):
    return dict([l.split("=", 1) for l in my_account['cookie'].split("; ")])

for task in bbsjson[parser.parse_args().group]:
    account = bbsjson[task['account']]
    task['url'] += account['formhash'] if task['url'].endswith('hash=') else ''
    try:
        if 'form' in task:
            form_data = {**task['form'], 'formhash': account['formhash']}
            post_headers = {**mydata['agent'], 'Content-Type': 'application/x-www-form-urlencoded'}
            response = requests.post(task['url'], cookies=get_cookie(account), headers=post_headers, data=form_data, timeout=10)
        else:
            response = requests.get(task['url'], cookies=get_cookie(account), headers=mydata['agent'], timeout=10)
        print(task['taskname'], '已完成，状态码：', response.status_code)
    except Exception as e:
        print(task['taskname'], '请求异常：', e)
