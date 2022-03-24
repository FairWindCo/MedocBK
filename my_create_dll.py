import clr

import pyc

clr.AddReference('IronPython')
clr.AddReference('IronPython.Modules')
# clr.AddReference('Microsoft.Scripting.Metadata')
clr.AddReference('Microsoft.Scripting')
clr.AddReference('Microsoft.Dynamic')
clr.AddReference('mscorlib')
clr.AddReference('System')
clr.AddReference('System.Data')

import os


def get_full_paths(db_path):
    result = []
    if os.path.exists(db_path):
        if os.path.isfile(db_path):
            result.append(db_path)
        elif os.path.isdir(db_path):
            for (dirpath, dirnames, filenames) in os.walk(db_path):
                for filename in filenames:
                    spath = os.path.join(dirpath, filename)
                    if os.path.splitext(spath)[-1] == '.py':
                        print spath
                        result.append(spath)
    return result


gb = get_full_paths(r'C:\Program Files\IronPython 2.7\Lib')

gb.append("/out:StdLib")

print ["/target:dll", ] + gb

pyc.Main(["/target:dll"] + gb)
