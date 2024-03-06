import socket
import time
import subprocess

if __name__ == '__main__':
    last_ip = ''
    while True:
        current_ip = socket.gethostbyname('axtl.cn')
        print(f'之前的IP：{last_ip}，现在的IP：{current_ip}。')
        if current_ip != last_ip:
            subprocess.run(["nginx", "-s", "reload"])
            print('nginx已重启。')
        last_ip = current_ip
        time.sleep(300)
