# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
#& 'C:\Program Files\IronPython 3.4\ipyc.exe' /main:win_test.py /embed /platform:x86 /standalone /target:console

import clr
clr.AddReference("System.Windows.Forms")
from System.Windows.Forms import MessageBox, MessageBoxButtons, DialogResult

if __name__ == '__main__':
    r = MessageBox.Show("Hello World!", "Greetings", MessageBoxButtons.OKCancel)
    if  r == DialogResult.OK:
        print("YES")