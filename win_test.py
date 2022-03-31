#  & 'C:\Program Files\IronPython 2.7\ipyc.exe' /main:win_test.py /platform:x86 /embed /standalone /target:exe
import clr

clr.AddReference("System.ServiceProcess")
clr.AddReference("IronPython")
clr.AddReference("StdLib")

from System.ServiceProcess import ServiceController, ServiceControllerStatus
import subprocess
import smtplib
import json
import sys
import os
import time
import platform
import shutil
from datetime import datetime
from zipfile import ZipFile
from rsa import encrypt, PublicKey
import base64
import re
import urllib



def Main(args):
    json_data = open('config.json').read()
    config = json.loads(json_data)

    WINRAR = config.get('winrar_path', None)
    DB_FILE = config['db_file']

    BKP_PATH = config.get('bkp_path', [])
    SAFE_TIME = config.get('safe_time', 0)
    REMOVE_OLD_FILE = config.get('remove_old_file', True)

    if config.get('ignore_service', False):
        SERVICE = None
    else:
        SERVICE = config.get('medoc_service', None)
    SERVICE_REACTION = config.get('service_reaction', 60)

    def load_key(key_path):
        f = open(key_path, 'rb')
        try:
            key = f.read()
            return PublicKey.load_pkcs1(key)
        finally:
            f.close()

    def encrypt_message(message, state_error=False):
        PUBLIC_KEY_FILE = config.get('public_key', None)
        if PUBLIC_KEY_FILE and os.path.exists(PUBLIC_KEY_FILE) and os.path.isfile(PUBLIC_KEY_FILE):
            public_key = load_key(PUBLIC_KEY_FILE)
            host = platform.node()
            key = base64.b64encode(encrypt(host + datetime.now().strftime("%d%m%y%H%M%S"), pub_key=public_key))
            mes = json.dumps({
                'host': host,
                'message': message,
                'time': time.ctime(),
                'is_error': state_error,
                'key': key
            })
            return mes
        return None

    def send_mail(message):
        SMTP_SERVER = config.get('server', '127.0.0.1')
        SMTP_PORT = config.get('port', 25)
        FROM_MAIL = config.get('from_mail', '')
        TO_MAIL = config.get('to_mail', "bspd@erc.ua")
        try:
            smtp = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            smtp.sendmail(FROM_MAIL, TO_MAIL, message)
        except Exception:
            pass

    def get_full_paths(db_path):
        result = []
        if os.path.exists(db_path):
            if os.path.isfile(db_path):
                result.append(db_path)
            elif os.path.isdir(db_path):
                for (dirpath, dirnames, filenames) in os.walk(db_path):
                    for filename in filenames:
                        spath = os.path.join(dirpath, filename)
                        print spath
                        result.append(spath)
        return result

    def archive_file_rar(path_to_archive, dst_path, winrar_path):
        exec_rar = 0
        for file_path in path_to_archive:
            exec_rar += (1 if subprocess.call(
                [winrar_path, 'a', '-dh', dst_path, file_path]) == 0 else 0)
        if exec_rar < len(path_list):
            send_mail("NOT ALL FILE ARCHIVED")

    def archive_file_zip(path_to_archive, dst_path):
        ZIP_COMPRESSION = config.get('zip_compression', 8)
        try:
            zipObj = ZipFile(dst_path, 'w', compression=ZIP_COMPRESSION, allowZip64=True)
            try:
                for file_path in path_to_archive:
                    zipObj.write(file_path)
            finally:
                zipObj.close()
        except Exception as e:
            send_mail("ZIP ERROR " + e.message)

    def stop_service(service_name, service_wait_time=60):
        if service_name:
            service = ServiceController(service_name)
            if service.Status == ServiceControllerStatus.Running:
                print "Try stop service"
                service.Stop()
                time.sleep(service_wait_time)
                service = ServiceController(service_name)
                print service.Status
            if service.Status != ServiceControllerStatus.Stopped:
                send_mail("Service {} is not stopped".format(service_name))
                sys.exit(-1)

    def start_service(service_name, service_wait_time=60):
        if service_name:
            try:
                service = ServiceController(service_name)
                service.Start()
                time.sleep(service_wait_time)
                service = ServiceController(service_name)
                if service.Status != ServiceControllerStatus.Running:
                    send_mail("Service not started")
            except Exception:
                send_mail("Service not started")

    def archive_file(path_to_archive, dst_path, winrar_path):
        if path_to_archive:
            if winrar_path:
                archive_file_rar(path_to_archive, dst_path, winrar_path)
            else:
                archive_file_zip(path_to_archive, dst_path)
        else:
            send_mail("NO DB FILE")

    def get_result_file_name(winrar_path, is_template=False):
        host_name = platform.node()
        BKP_FORMAT = config.get('bkp_file_format', '{}zvit{}.rar')
        if not winrar_path:
            BKP_FORMAT = BKP_FORMAT.replace('.rar', '.zip')
        date_str = '[0-9]{6}\\' if is_template else datetime.now().strftime("%d%m%y")
        return BKP_FORMAT.format(host_name, date_str)

    def get_result_path(winrar_path):
        TMP_BKP = config.get('db_path', '.')
        bkp_file_name = get_result_file_name(winrar_path, False)
        if os.path.exists(TMP_BKP) and os.path.isdir(TMP_BKP):
            s_path = os.path.join(TMP_BKP, bkp_file_name)
            print s_path
            return s_path
        return None

    def send_request(message, url, csrf):
        import urllib2
        post = urllib.quote(message)
        req = urllib2.Request(url, post)
        req.add_header('X-CSRFToken', csrf)
        req.add_header('Cookie', 'csrftoken={}'.format(csrf))
        response = urllib2.urlopen(req)
        return response.read()

    def get_request(url):
        import urllib2
        req = urllib2.Request(url)
        response = urllib2.urlopen(req)
        text = response.read()
        obj_dict = json.loads(text)
        return obj_dict.get('csrf', None)

    def log_message(message):
        url_token = config.get('token_url', 'http://127.0.0.1:8000/token')
        url_special = config.get('special_url', 'http://127.0.0.1:8000/special')
        csrf = get_request(url_token)
        mes = encrypt_message(message)
        send_request(mes, url_special, csrf)

    log_message("START")
    s_path = get_result_path(WINRAR)
    if s_path:
        stop_service(SERVICE, SERVICE_REACTION)
        path_list = get_full_paths(DB_FILE)
        archive_file(path_list, s_path, WINRAR)
        start_service(SERVICE, SERVICE_REACTION)

        d_name = os.path.basename(s_path)
        template = re.compile(get_result_file_name(WINRAR, True))
        file_copy = 0
        for path in BKP_PATH:
            d_path = os.path.join(path, d_name)
            try:
                shutil.copy(s_path, d_path)
                file_copy += 1
            except Exception:
                send_mail("Can`t copy to {}".format(d_path))
            days_before = (time.time() - SAFE_TIME * 86400)

            if REMOVE_OLD_FILE:
                for f in os.listdir(path):
                    file_path = os.path.join(path, f)
                    if template.match(f) and os.stat(file_path).st_mtime < days_before:
                        os.remove(file_path)

        if file_copy > 0:
            os.remove(s_path)

        log_message("WELL DONE")
    else:
        send_mail("NO TMP PATH")
        exit(-2)


if __name__ == "__main__":
    Main(sys.argv[1:])
