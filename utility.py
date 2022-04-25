import base64
import json
import os
import platform
import smtplib
import subprocess
import sys
from datetime import datetime
from zipfile import ZipFile

from rsa import PublicKey, encrypt


def send_request(message, url, csrf, proxy=None):
    import urllib2
    import urllib
    if proxy:
        handler = urllib2.ProxyHandler({'http': proxy, 'https': proxy})
        opener = urllib2.build_opener(handler)
        urllib2.install_opener(opener)

    post = urllib.quote(message)
    req = urllib2.Request(url, post)
    req.add_header('X-CSRFToken', csrf)
    req.add_header('Cookie', 'csrftoken={}'.format(csrf))
    try:
        response = urllib2.urlopen(req)
        return response.read()
    except urllib2.HTTPError as e:
        print 'WARNING', e.code, e.message, e.reason
    except urllib2.URLError as e_url:
        print 'WARNING', e_url


def get_request(url, proxy=None):
    import urllib2
    try:
        if proxy:
            handler = urllib2.ProxyHandler({'http': proxy, 'https': proxy})
            opener = urllib2.build_opener(handler)
            urllib2.install_opener(opener)

        req = urllib2.Request(url)
        try:
            response = urllib2.urlopen(req)
            text = response.read()
        except urllib2.HTTPError as e:
            print 'WARNING', e.code, e.message, e.reason
            text = {}
        except urllib2.URLError as e_url:
            print 'WARNING', e_url
            text = '{}'
        obj_dict = json.loads(text)
    except Exception as e:
        print 'WARNING', e
        obj_dict = '{}'
    return obj_dict.get('csrf', None)


def load_key(key_path):
    try:
        f = open(key_path, 'rb')
        try:
            key = f.read()
            return PublicKey.load_pkcs1(key)
        finally:
            f.close()
    except Exception as e:
        print "ERROR", e
        sys.exit(-2)


def encrypt_info_dict(info, config=None, use_platform_host=True):
    if config is None:
        config = {}
    PUBLIC_KEY_FILE = config.get('public_key', None)
    if PUBLIC_KEY_FILE and os.path.exists(PUBLIC_KEY_FILE) and os.path.isfile(PUBLIC_KEY_FILE):
        public_key = load_key(PUBLIC_KEY_FILE)
        host = platform.node() if use_platform_host else info.get('host', '')
        key = base64.b64encode(encrypt(host + datetime.now().strftime("%d%m%y%H%M%S"), pub_key=public_key))
        info['key'] = key
        print info
        mes = json.dumps(info)
        return mes
    return None


def get_config(config_file='config.json', exit_on_error=True):
    config = {}
    try:
        json_data = open(config_file).read()
        config = json.loads(json_data)
    except Exception as e:
        if exit_on_error:
            print "ERROR", e
            sys.exit(-1)
        else:
            print "WARNING", e
    return config


def send_info_request(info, config=None, use_platform_host=True, debug_out=False,
                      url_default='http://127.0.0.1:8000/host_info_update'):
    if config is None:
        config = {}
    url_token = config.get('token_url', 'http://127.0.0.1:8000/token')
    url_special = config.get('special_url', url_default)
    proxy = config.get('proxy', None)
    if debug_out:
        print "Try Get CSRF Tolken"
    csrf = get_request(url_token, proxy=proxy)
    if debug_out:
        print csrf
    mes = encrypt_info_dict(info, config, use_platform_host)
    if debug_out:
        print "Try Send"
    res = send_request(mes, url_special, csrf, proxy=proxy)
    if debug_out:
        print res
    return res


def send_report_error(message, config):
    SEND_REPORT_MAIL = config.get('send_report_mail', True)
    SEND_REPORT_WEB = config.get('send_report_web', True)
    if SEND_REPORT_MAIL:
        send_mail(message, config)
    if SEND_REPORT_WEB:
        log_message(message, config, True)


def send_mail(message, config):
    SMTP_SERVER = config.get('server', '127.0.0.1')
    SMTP_PORT = config.get('port', 25)
    FROM_MAIL = config.get('from_mail', '')
    TO_MAIL = config.get('to_mail', "bspd@erc.ua")
    try:
        smtp = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        smtp.sendmail(FROM_MAIL, TO_MAIL, message)
    except Exception as e:
        print "WARNING", e


def get_full_paths(db_paths):
    result = []
    if isinstance(db_paths, str):
        db_paths = [db_paths]
    for db_path in db_paths:
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


def archive_file_rar(path_to_archive, dst_path, winrar_path, path_list):
    exec_rar = 0
    for file_path in path_to_archive:
        exec_rar += (1 if subprocess.call(
            [winrar_path, 'a', '-dh', dst_path, file_path]) == 0 else 0)
    if exec_rar < len(path_list):
        send_report_error("NOT ALL FILE ARCHIVED")


def archive_file_zip(path_to_archive, dst_path, config):
    ZIP_COMPRESSION = config.get('zip_compression', 8)
    try:
        zipObj = ZipFile(dst_path, 'w', compression=ZIP_COMPRESSION, allowZip64=True)
        try:
            for file_path in path_to_archive:
                zipObj.write(file_path)
        finally:
            zipObj.close()
    except Exception as e:
        send_report_error("ZIP ERROR " + e.message)


def get_result_file_name(winrar_path, is_template=False, config=None):
    if config is None:
        config = {}
    host_name = platform.node()
    BKP_FORMAT = config.get('bkp_file_format', '{}zvit{}.rar')
    if not winrar_path:
        BKP_FORMAT = BKP_FORMAT.replace('.rar', '.zip')
    date_str = '[0-9]{6}\\' if is_template else datetime.now().strftime("%d%m%y")
    return BKP_FORMAT.format(host_name, date_str)


def get_result_path(winrar_path, config):
    TMP_BKP = config.get('db_path', '.')
    bkp_file_name = get_result_file_name(winrar_path, False)
    if os.path.exists(TMP_BKP) and os.path.isdir(TMP_BKP):
        s_path = os.path.join(TMP_BKP, bkp_file_name)
        print s_path
        return s_path
    return None


def log_message(message, config, state_error=False, debug_out=False):
    from time import ctime
    mes = {
        'message': message,
        'time': ctime(),
        'is_error': state_error,
    }
    return send_info_request(mes, config, use_platform_host=True, debug_out=debug_out,
                             url_default='http://127.0.0.1:8000/special')


def archive_file(path_to_archive, dst_path, winrar_path, path_lst):
    if path_to_archive:
        if winrar_path:
            archive_file_rar(path_to_archive, dst_path, winrar_path, path_lst)
        else:
            archive_file_zip(path_to_archive, dst_path)
    else:
        send_mail("NO DB FILE")
