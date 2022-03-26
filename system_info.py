import clr
clr.AddReference("System.ServiceProcess")
clr.AddReference("IronPython")
clr.AddReference("StdLib")
clr.AddReference("System.Management")

from System.Management import ManagementObjectSearcher


if __name__ == "__main__":

    objects_names = ["Win32_OperatingSystem",
                     "Win32_ComputerSystem",
                     "Win32_DiskDrive",
                     "Win32_Processor",
                     # "Win32_ProgramGroup",
                     # "Win32_SystemDevices",
                     # "Win32_StartupCommand"
                     ]
    for name in objects_names:
        mos = ManagementObjectSearcher("select * from " + name)
        for mo in mos.Get():
            for prop in mo.Properties:
                print "{} \t\t\t {} \t\t\t\t\t {}".format(name, prop.Name, prop.Value)
