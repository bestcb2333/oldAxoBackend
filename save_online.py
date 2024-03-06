import os
import json
import pymysql
import requests

os.chdir(os.path.dirname(os.path.abspath(__file__)))
with open('data.json', 'r', encoding='utf-8') as file:
    dat = json.load(file)

def get_ol(server):
    for key in server:
        online = 0
        try:
            data = requests.get(server[key]['url'], timeout=10).json()
            if server[key]['game'] == 'mc':
                online = data['players']['online']
            elif server[key]['game'] == 'dst':
                online = [me for me in data['GET'] if me['host'] == dat['dst']][0]['connected']
            else:
                online = len(data['players'])
        except Exception as e:
            print(f'An error occurred: {e}.')
        server[key] = online
    return server

def store_to_mysql(main, sc, mods, dst, tr):
    connection = pymysql.connect(**dat['sql']['root'], db="script")
    try:
        with connection.cursor() as cursor:
            cursor.execute(f'INSERT INTO online (main, sc, mods, dst, tr, timestamp) VALUES ({main}, {sc}, {mods}, {dst}, {tr}, NOW())')
            cursor.execute('DELETE FROM online WHERE timestamp < NOW() - INTERVAL 7 DAY')
        connection.commit()
    finally:
        connection.close()

mc_url = f"http://localhost:{dat['port']['flask']}/status?srv="
stored = {
    'main':  {'game': 'mc',  'url': mc_url + 'main'},
    'sc':    {'game': 'mc',  'url': mc_url + 'sc'},
    'mods':  {'game': 'mc',  'url': mc_url + 'mod'},
    'dst':   {'game': 'dst', 'url': dat['url']['dst']},
    'tr':    {'game': 'tr',  'url': f"https://{dat['ip']['win']}:{dat['port']['api']}/trinfo"}
}

store_to_mysql(**get_ol(stored))
