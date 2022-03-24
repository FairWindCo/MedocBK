# Script below is based on following post:
# FROM THIS https://gist.github.com/diyan/1759391
# IronPython: EXE compiled using pyc.py cannot import module "os" - Stack Overflow
# http://stackoverflow.com/questions/6195781/ironpython-exe-compiled-using-pyc-py-cannot-import-module-os

import sys

sys.path.append('d:/projects/SomeProject/Libs/IronPython')
sys.path.append('d:/projects/SomeProject/Libs/IronPython/Lib')
sys.path.append('d:/projects/SomeProject/Libs/IronPython/Tools/Scripts')
import clr

clr.AddReference('IronPython')
clr.AddReference('IronPython.Modules')
# clr.AddReference('Microsoft.Scripting.Metadata')
clr.AddReference('Microsoft.Scripting')
clr.AddReference('Microsoft.Dynamic')
clr.AddReference('mscorlib')
clr.AddReference('System')
clr.AddReference('System.Data')

#
# adapted from os-path-walk-example-3.py

import os, glob
import fnmatch
import pyc


def doscopy(filename1):
    print filename1
    os.system("copy %s .\\bin\Debug\%s" % (filename1, filename1))


class GlobDirectoryWalker:
    # a forward iterator that traverses a directory tree

    def __init__(self, directory, pattern="*"):
        self.stack = [directory]
        self.pattern = pattern
        self.files = []
        self.index = 0

    def __getitem__(self, index):
        while 1:
            try:
                file = self.files[self.index]
                self.index = self.index + 1
            except IndexError:
                # pop next directory from stack
                self.directory = self.stack.pop()
                self.files = os.listdir(self.directory)
                self.index = 0
            else:
                # got a filename
                fullname = os.path.join(self.directory, file)
                if os.path.isdir(fullname) and not os.path.islink(fullname) and fullname[-4:] <> '.svn':
                    self.stack.append(fullname)
                if fnmatch.fnmatch(file, self.pattern):
                    return fullname


# Build StdLib.DLL
gb = glob.glob(r"C:\Program Files\IronPython 2.7\Lib\*.py")
print gb
gb.append("/out:StdLib")

print ["/target:dll", ] + gb

pyc.Main(["/target:dll"] + gb)

# Build EXE
# gb=["/main:FredMain.py","FredSOAP.py","/target:exe","/out:Fred_Download_Tool"]
# pyc.Main(gb)


# CopyFiles to Release Directory
doscopy("StdLib.dll")
# doscopy("Fred_Download_Tool.exe")
# doscopy("Fred_Download_.dll")


# Copy DLLs to Release Directory
fl = ["IronPython.dll", "IronPython.Modules.dll",
      "Microsoft.Dynamic.dll",
      "Microsoft.Scripting.Debugging.dll",
      "Microsoft.Scripting.dll",
      "Microsoft.Scripting.ExtensionAttribute.dll",
      "Microsoft.Scripting.Core.dll"]
for f in fl:
    doscopy(f)
