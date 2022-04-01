import clr

clr.AddReference("System.ServiceProcess")
clr.AddReference("IronPython")
clr.AddReference("StdLib")
clr.AddReference("System.Management")

from System.Management import ManagementObjectSearcher
from System.ServiceProcess import ServiceController, ServiceControllerStatus
from Microsoft.Win32 import Registry
import re
from datetime import datetime
import platform
import json
import os
import base64
from System.Net import Dns
from System.Net.Sockets import AddressFamily
from rsa import encrypt, PublicKey
import argparse


def clear_name(name, ver):
    if name:
        if ver:
            # pattern = '[\\s]*[-]?[\\s]*' + ver
            pattern = r'[\s-]*' + ver + r'[.0-9\s]*'
            name = re.sub(pattern, '', name)
        name = name.replace('False', '').strip()
    return name


def form_soft(name, ver, install):
    # return clear_name(name, ver), ver, datetime.strptime(install, '%Y%m%d') if install else None
    return clear_name(name, ver), ver, install


def get_wmi_soft():
    mos = ManagementObjectSearcher("select Name, Version, InstallDate from Win32_Product")
    if mos:
        return [form_soft(mo['Name'], mo['Version'], mo['InstallDate']) for mo in mos.Get()]
    return []


def get_wmi_futures():
    try:
        mos = ManagementObjectSearcher("select Name from Win32_ServerFeature")
        if mos:
            return [mo['Name'] for mo in mos.Get()]
    except Exception:
        pass
    return []


def get_reg_key(current_user=False, is64=False):
    if is64:
        key = "SOFTWARE\\Wow6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall"
    else:
        key = "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall"
    if current_user:
        return Registry.LocalMachine.OpenSubKey(key)
    else:
        return Registry.LocalMachine.OpenSubKey(key)


def get_display_name(parent_key, current_name):
    key = parent_key.OpenSubKey(current_name)
    if key:
        name = key.GetValue("DisplayName")
        ver = key.GetValue("DisplayVersion")
        installed = key.GetValue("InstallDate")
        if name:
            name = clear_name(name, ver)
        else:
            default_val = key.GetValue('')
            name = default_val if default_val else current_name
        return name, ver, installed
    else:
        return current_name, None, None


def list_sub_keys(key):
    if key:
        return [get_display_name(key, k) for k in key.GetSubKeyNames()]
    else:
        return []


def listing_sub_keys(key):
    if key:
        return key.GetSubKeyNames()
    else:
        return []


def convert_to_dict(info_list, info_dict=None):
    if info_dict is None:
        info_dict = {}
    if info_list:
        for info in info_list:
            info_dict[info[0]] = info
    return info_dict


def get_installed_soft():
    paths1 = list_sub_keys(get_reg_key(False, False))
    paths2 = list_sub_keys(get_reg_key(True, False))
    paths3 = list_sub_keys(get_reg_key(False, True))
    paths4 = list_sub_keys(get_reg_key(True, True))
    soft = convert_to_dict(paths1, None)
    soft = convert_to_dict(paths2, soft)
    soft = convert_to_dict(paths3, soft)
    soft = convert_to_dict(paths4, soft)
    return soft


def get_services():
    services = ServiceController.GetServices()
    return [service.DisplayName for service in services
            if service.Status == ServiceControllerStatus.Running]


def get_system_info(log=False):
    objects_names = [
        "Win32_OperatingSystem",
        "Win32_ComputerSystem",
        "Win32_DiskDrive",
        "Win32_Processor",
    ]
    result = {}
    for name in objects_names:
        result[name] = {
            'infos': [],
            'count': 0
        }
        mos = ManagementObjectSearcher("select * from " + name)
        count = 0
        for mo in mos.Get():
            info = {}
            for prop in mo.Properties:
                if log:
                    print name, prop.Name, prop.Value
                info[prop.Name] = prop.Value
            result[name]['infos'].append(info)
            count += 1
        result[name]['count'] = count

    return result


def form_host_info_json(small_info=False):
    info = get_system_info()
    result = {
        'host': platform.node(),
    }
    if not small_info:
        result.update(
            {'SystemFamily': info['Win32_ComputerSystem']['infos'][0]['SystemFamily'],
             'Model': info['Win32_ComputerSystem']['infos'][0]['Model'],
             'Domain': info['Win32_ComputerSystem']['infos'][0]['Domain'],
             'sysname': info['Win32_OperatingSystem']['infos'][0]['Caption'],
             'Manufacturer': info['Win32_ComputerSystem']['infos'][0]['Manufacturer'],
             'TotalPhysicalMemory': str(info['Win32_ComputerSystem']['infos'][0]['TotalPhysicalMemory']),
             'NumberOfProcessors': int(info['Win32_ComputerSystem']['infos'][0]['NumberOfProcessors']),
             'Version': info['Win32_OperatingSystem']['infos'][0]['Version'],
             'BuildNumber': info['Win32_OperatingSystem']['infos'][0]['BuildNumber'],
             'InstallDate': info['Win32_OperatingSystem']['infos'][0]['InstallDate'],
             'OSArchitecture': info['Win32_OperatingSystem']['infos'][0]['OSArchitecture'],
             'hdd_count': info['Win32_DiskDrive']['count'],
             'cpu_count': info['Win32_Processor']['count'],
             'hdd_info': [],
             'cpu_info': []
             }
        )

    for hdd_info in info['Win32_DiskDrive']['infos']:
        result['hdd_info'].append({
            'model': hdd_info['Model'],
            'size': int(hdd_info['Size'])
        })
    for cpu_info in info['Win32_Processor']['infos']:
        result['cpu_info'].append({
            'model': cpu_info['Name'],
            'ThreadCount': int(cpu_info['ThreadCount']),
            'NumberOfCores': int(cpu_info['NumberOfCores']),
        })

    return result


def get_ip_list():
    host = Dns.GetHostEntry(Dns.GetHostName())
    return [ip.ToString() for ip in host.AddressList if ip.AddressFamily == AddressFamily.InterNetwork]


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
        print e.code, e.message, e.reason



def get_request(url, proxy=None):
    import urllib2
    if proxy:
        handler = urllib2.ProxyHandler({'http': proxy, 'https': proxy})
        opener = urllib2.build_opener(handler)
        urllib2.install_opener(opener)

    req = urllib2.Request(url)
    response = urllib2.urlopen(req)
    text = response.read()
    obj_dict = json.loads(text)
    return obj_dict.get('csrf', None)


def load_key(key_path):
    f = open(key_path, 'rb')
    try:
        key = f.read()
        return PublicKey.load_pkcs1(key)
    finally:
        f.close()


def encrypt_message(info, state_error=False, config=None):
    if config is None:
        config = {}
    PUBLIC_KEY_FILE = config.get('public_key', None)
    if PUBLIC_KEY_FILE and os.path.exists(PUBLIC_KEY_FILE) and os.path.isfile(PUBLIC_KEY_FILE):
        public_key = load_key(PUBLIC_KEY_FILE)
        host = platform.node()
        key = base64.b64encode(encrypt(host + datetime.now().strftime("%d%m%y%H%M%S"), pub_key=public_key))
        info['key'] = key
        print info
        mes = json.dumps(info)
        return mes
    return None


def get_config(config_file='config.json'):
    json_data = open(config_file).read()
    config = json.loads(json_data)
    return config


def log_message(info, config=None):
    if config is None:
        config = {}
    url_token = config.get('token_url', 'http://127.0.0.1:8000/token')
    url_special = config.get('special_url', 'http://127.0.0.1:8000/host_info_update')
    proxy = config.get('proxy', None)
    print "Try Get CSRF Tolken"
    csrf = get_request(url_token, proxy=proxy)
    print csrf
    mes = encrypt_message(info, False, config)
    print "Try Send"
    print send_request(mes, url_special, csrf, proxy=proxy)


if __name__ == "__main__":
    # for soft in get_wmi_soft():
    #     print soft

    # for ipy_path in get_installed_soft().values():
    #     print ipy_path

    # get_services()
    parser = argparse.ArgumentParser()
    parser.add_argument('--soft', dest='soft', action='store_true')
    parser.add_argument('-f', dest='save')
    parser.add_argument('-p', dest='echo', action='store_true')
    parser.add_argument('-s', dest='skip', action='store_true')

    arguments = parser.parse_args()
    info = form_host_info_json(arguments.soft)

    info['services'] = get_services()

    info['soft'] = [{
        'name': soft[0],
        'version': soft[1],
        'installed': soft[2]
    } for soft in get_wmi_soft()]

    info['ip'] = get_ip_list()
    info['futures'] = get_wmi_futures()
    config = get_config()

    if arguments.save:
        f = open(arguments.save, 'wt')
        try:
            f.write(json.dumps(info))
        finally:
            f.close()
    if not arguments.skip:
        log_message(info, config)
    if arguments.echo:
        print info
