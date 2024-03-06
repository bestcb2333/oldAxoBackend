import os
from urllib.request import urlopen
import json
from aliyunsdkcore.client import AcsClient
from aliyunsdkalidns.request.v20150109.DescribeSubDomainRecordsRequest import DescribeSubDomainRecordsRequest
from aliyunsdkalidns.request.v20150109.UpdateDomainRecordRequest import UpdateDomainRecordRequest
from aliyunsdkalidns.request.v20150109.AddDomainRecordRequest import AddDomainRecordRequest
from aliyunsdkalidns.request.v20150109.DeleteSubDomainRecordsRequest import DeleteSubDomainRecordsRequest

os.chdir(os.path.dirname(os.path.abspath(__file__)))
with open('data.json', 'r', encoding='utf-8') as file:
    mydata = json.load(file)

client = AcsClient(mydata['dns']['id'], mydata['dns']['key'], 'cn-hangzhou')

def update(domain, resource_record, record_type, record_value, update_domain=True):
    if update_domain:
        request = UpdateDomainRecordRequest()
        request.set_accept_format('json')
        request.set_RecordId(domain)
    else:
        request = AddDomainRecordRequest()
        request.set_accept_format('json')
        request.set_DomainName(domain)
    request.set_RR(resource_record)
    request.set_Type(record_type)
    request.set_Value(record_value)
    client.do_action_with_exception(request)

def main(domain, subdomain, is_ipv4=True):
    record_type = 'A' if is_ipv4 else 'AAAA'
    ip_api = 'https://ipv4.ddnspod.com' if is_ipv4 else 'https://ipv6.ddnspod.com/'
    request = DescribeSubDomainRecordsRequest()
    request.set_accept_format('json')
    request.set_DomainName(domain)
    request.set_SubDomain(subdomain + '.' + domain)
    request.set_Type(record_type)
    response_data = client.do_action_with_exception(request)
    domain_list = json.loads(response_data.decode('utf-8')) if isinstance(response_data, bytes) else {}
    with urlopen(ip_api) as url_response:
        ip = str(url_response.read(), encoding='utf-8')
    print('获取到', subdomain + '.' + domain, '域名的', record_type, '类型记录值：', ip, end='，')
    if domain_list['TotalCount'] == 0:
        update(domain, subdomain, record_type, ip, False)
        print("新建域名解析成功")
    elif domain_list['TotalCount'] == 1:
        if domain_list['DomainRecords']['Record'][0]['Value'].strip() != ip.strip():
            update(domain_list['DomainRecords']['Record'][0]['RecordId'], subdomain, record_type, ip)
            print("修改域名解析成功")
        else:
            print("记录值没变。")
    elif domain_list['TotalCount'] > 1:
        request = DeleteSubDomainRecordsRequest()
        request.set_accept_format('json')
        request.set_DomainName(domain)
        request.set_RR(subdomain)
        request.set_Type(record_type)
        client.do_action_with_exception(request)
        update(domain, subdomain, record_type, ip, False)
        print("修改域名解析成功")

if __name__ == '__main__':
    main('mcax.cn', '@')
    main('axtl.cn', '@')
