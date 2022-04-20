# & 'C:\Program Files\IronPython 2.7\ipyc.exe' /main:win_test.py utility.py /platform:x86 /embed /standalone /target:exe
import clr

clr.AddReference("System.ServiceProcess")
clr.AddReference("IronPython")
clr.AddReference("StdLib")

from System.ServiceProcess import ServiceController, ServiceControllerStatus
import sys
import os
import time
import shutil
import re
from utility import send_report_error, log_message, get_result_path, get_config, get_full_paths, get_result_file_name, \
    archive_file


def stop_service(service_name, service_wait_time=60):
    if service_name:
        try:
            service = ServiceController(service_name)
            if service.Status == ServiceControllerStatus.Running:
                print "Try stop service"
                service.Stop()
                time.sleep(service_wait_time)
                service = ServiceController(service_name)
                print service.Status
            if service.Status != ServiceControllerStatus.Stopped:
                send_report_error("Service {} is not stopped".format(service_name))
                sys.exit(-1)
        except Exception:
            send_report_error("Service {} is not found".format(service_name))
            sys.exit(-1)


def start_service(service_name, service_wait_time=60):
    if service_name:
        try:
            service = ServiceController(service_name)
            service.Start()
            time.sleep(service_wait_time)
            service = ServiceController(service_name)
            if service.Status != ServiceControllerStatus.Running:
                send_report_error("Service not started")
        except Exception:
            send_report_error("Service not started")


def Main(args):
    config = get_config()

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

    log_message("START BACKUP", config)
    s_path = get_result_path(WINRAR, config)
    if s_path:
        stop_service(SERVICE, SERVICE_REACTION)
        path_list = get_full_paths(DB_FILE)
        archive_file(path_list, s_path, WINRAR, path_list)
        start_service(SERVICE, SERVICE_REACTION)

        d_name = os.path.basename(s_path)
        template = re.compile(get_result_file_name(WINRAR, True))
        file_copy = 0
        days_before = (time.time() - SAFE_TIME * 86400)
        for path in BKP_PATH:
            d_path = os.path.join(path, d_name)
            try:
                shutil.copy(s_path, d_path)
                file_copy += 1
            except Exception:
                send_report_error("Can`t copy to {}".format(d_path), config)

            if REMOVE_OLD_FILE:
                for f in os.listdir(path):
                    file_path = os.path.join(path, f)
                    if template.match(f) and os.stat(file_path).st_mtime < days_before:
                        os.remove(file_path)

        if file_copy > 0:
            os.remove(s_path)

        log_message("WELL DONE", config)
    else:
        send_report_error("NO TMP PATH", config)
        sys.exit(-2)


if __name__ == "__main__":
    Main(sys.argv[1:])
