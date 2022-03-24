# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
# 'C:\Program Files\IronPython 2.7\ipyc.exe' /main:test_sharp2.py  /embed /platform:x86 /standalone /target:winexe
# 'C:\Program Files\IronPython 2.7\ipyc.exe' /main:test_sharp2.py  /embed /platform:x86 /standalone /target:winexe
# & 'C:\Program Files\IronPython 3.4\ipyc.exe' /main:win_test.py /platform:x86 /standalone /target:exe
# & 'C:\Program Files\IronPython 2.7\ipyc.exe' /main:win_test.py /platform:x86 /embed /standalone /target:exe

#  & 'C:\Program Files\IronPython 2.7\ipyc.exe' /main:win_test.py /platform:x86 /embed /standalone /target:exe 'C:\Program Files\IronPython 2.7\L
# ib\subprocess.py' 'C:\Program Files\IronPython 2.7\Lib\os.py' 'C:\Program Files\IronPython 2.7\Lib\smtplib.py' 'C:\Program Files\IronPython 2.7\Lib\os.py'
#
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

def Main(args):
    json_data = open('config.json').read()
    config = json.loads(json_data)

    SMTP_SERVER = config['server']
    SMTP_PORT = config['port']
    FROM_MAIL = config['from_mail']
    TO_MAIL = config['to_mail']
    SERVICE = config['medoc_service']
    WINRAR = config['winrar_path']
    DB_FILE = config['db_file']
    TMP_BKP = config['db_path']
    BKP_FORMAT = config['bkp_file_format']
    BKP_PATH = config['bkp_path']
    SAFE_TIME = config['safe_time']
    SERVICE_REACTION = config['service_reaction']


    def send_mail(message):
        smtp = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        smtp.sendmail(FROM_MAIL, TO_MAIL, message)


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


    if os.path.exists(TMP_BKP) and os.path.isdir(TMP_BKP):
        # check service
        service = ServiceController(SERVICE)
        if service.Status == ServiceControllerStatus.Running:
            print "Try stop service"
            service.Stop()
            time.sleep(SERVICE_REACTION)
            service = ServiceController(SERVICE)
            print service.Status
        host_name = platform.node()
        date_str = datetime.now().strftime("%d%m%y")
        s_path = os.path.join(TMP_BKP, BKP_FORMAT.format(host_name, date_str))

        if service.Status != ServiceControllerStatus.Stopped:
            send_mail("Service {} is not stopped".format(SERVICE))
            sys.exit(-1)

        path_list = get_full_paths(DB_FILE)
        if path_list:
            exec_rar = 0
            for file_path in path_list:
                exec_rar += (1 if subprocess.call(
                    [WINRAR, 'a', '-dh', s_path, file_path]) == 0 else 0)
            if exec_rar < len(path_list):
                send_mail("NOT ALL FILE ARCHIVED")
        else:
            send_mail("NO DB FILE")
        try:
            service.Start()
            time.sleep(SERVICE_REACTION)
            service = ServiceController(SERVICE)
            if service.Status != ServiceControllerStatus.Running:
                send_mail("Service not started")

        except Exception:
            send_mail("Service not started")
        d_name = os.path.basename(s_path)
        file_copy = 0
        for path in BKP_PATH:
            d_path = os.path.join(path, d_name)
            try:
                shutil.copy(s_path, d_path)
                file_copy += 1
            except Exception:
                send_mail("Can`t copy to {}".format(d_path))
            days_before = (time.time() - SAFE_TIME * 86400)

            for f in os.listdir(path):
                file_path = os.path.join(path, f)
                if f.startswith(host_name) and os.stat(file_path).st_mtime < days_before:
                    os.remove(file_path)

        if file_copy > 0:
            os.remove(s_path)
    else:
        send_mail("NO TMP PATH")
        exit(-2)

if __name__ == "__main__":
    sys.path.insert(0, "Lib")
    Main(sys.argv[1:])