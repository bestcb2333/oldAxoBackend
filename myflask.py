import os
import io
import json
import uuid
from flask import Flask, send_file, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from PIL import Image, ImageDraw, ImageFont
import requests
from mcstatus import JavaServer
from mcrcon import MCRcon
from flask_cors import CORS

os.chdir(os.path.dirname(os.path.abspath(__file__)))
with open('data.json', 'r', encoding='utf-8') as data_file, open('info.json', 'r', encoding='utf-8') as info_file:
    dat, infor = json.load(data_file), json.load(info_file)
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024
limiter = Limiter(get_remote_address, app=app, storage_uri=f"redis://localhost:{dat['port']['redis']}")
CORS(app, resources={r'/*': {'origins': '*'}})

@app.route('/bedrock_online')
def bedrock_online():
    with open('data.json', 'r', encoding='utf-8') as data_file, open('info.json', 'r', encoding='utf-8') as info_file:
        dat, infor = json.load(data_file), json.load(info_file)
    try:
        data = requests.get("http://127.0.0.1:8000/status?srv=main", timeout=10).json()
    except Exception:
        data = {"players": {"online": "服务器离线"}, "version": {"name": "服务器离线"}}
    img = Image.new('RGB', (300, 100), color='#28abce')
    d = ImageDraw.Draw(img)
    d_font = ImageFont.truetype(dat['font']['mc'], 15)
    d.text((10, 70), f"  在线玩家: {data['players']['online']}    版本: {infor['ver']['mainbe']}", fill=(255, 255, 255), font=d_font)
    d.text((10, 10), "点我启动游戏添加服务器", fill=(255, 255, 255), font=ImageFont.truetype(dat['font']['mc'], 25))
    d.rectangle((0, 0, 300, 100), outline=(17, 102, 126), width=5)
    buffer = io.BytesIO()
    img.save(buffer, 'PNG')
    buffer.seek(0)
    return send_file(buffer, mimetype="image/jpeg", download_name='online_players.png')

@app.route('/status')
def get_status():
    srv = request.args.get('srv', default='main')
    try: 
        status = JavaServer.lookup(f"{dat['ip']['win']}:{dat['port'][srv]['query']}").status().__dict__
        del status['motd']
        return jsonify(status)
    except Exception as e:
        return {'An error occurred: ': str(e)}

@app.route('/rcon')
@limiter.limit('1 per second')
def send_rcon():
    cmd = request.args.get('cmd', default='')
    srv = request.args.get('srv', default='main')
    pwd = request.args.get('pwd', default='')
    cmd = cmd[1:] if cmd.startswith('/') else cmd
    try:
        if cmd.split()[0] in dat['cmd']['user'] or cmd.split()[0] in dat['cmd']['op'] and pwd == dat['pwd']['api']:
            with MCRcon(dat['ip']['win'], dat['pwd']['rcon'], dat['port'][srv]['rcon']) as mcr:
                return mcr.command(cmd)
        else:
            return f"命令{cmd}尚未接入，或者你没有权限。可用命令：{', '.join(dat['cmd']['user'])}，需要密码：{', '.join(dat['cmd']['op'])}", 400
    except Exception as e:
        return f'An error occurred: {str(e)}', 400

@app.route('/serverInfoList')
def send_info():
    with open('info.json', 'r', encoding='utf-8') as info_file:
        infor = json.load(info_file)
    return jsonify(infor)

@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files['image'] if 'image' in request.files else None
    fill_method = request.form.get('fill_method', default='compress')
    if file and file.filename and file.filename.rsplit('.', 1)[-1].lower() in {'png', 'jpg', 'jpeg'}:
        filename = str(uuid.uuid4()) + '.png'
        if fill_method == 'compress':
            Image.open(file.stream).resize((128, 128)).save(os.path.join('/home/img/', filename))
        else:
            original = Image.open(file.stream)
            paste_point = int((max(original.size) - original.size[0])/2), int((max(original.size) - original.size[1])/2)
            canvas = Image.new('RGBA', (max(original.size), max(original.size)), (255, 255, 255, 0))
            canvas.paste(original, paste_point)
            canvas.resize((128, 128)).save(os.path.join('/home/img/', filename))
        return jsonify({'url': f'https://api.mcax.cn/img/{filename}'}), 200
    else:
        return jsonify({'error': 'Invalid file type'}), 400
