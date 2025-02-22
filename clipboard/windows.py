from __future__ import annotations

import subprocess
import os
import sys
import ctypes
import ctypes.wintypes as w

from locale import getdefaultlocale


class Clipboard():
    def __init__(self, file_urls=None):
        pass

    def push_pixel_to_clipboard(self, path):
        script = (
            "Add-Type -Assembly System.Windows.Forms; "
            "Add-Type -Assembly System.Drawing; "
            f"$image = [Drawing.Image]::FromFile('{path}'); "
            "$imageStream = New-Object System.IO.MemoryStream; "
            "$image.Save($imageStream, [System.Drawing.Imaging.ImageFormat]::Png); "
            "$dataObj = New-Object System.Windows.Forms.DataObject('Bitmap', $image); "
            "$dataObj.SetData('PNG', $imageStream); "
            "[System.Windows.Forms.Clipboard]::SetDataObject($dataObj, $true); "
        )

        self.execute_powershell(script)

    def push_to_clipboard(self, paths):
        join_s = ""

        for path in paths:
            join_s += f", '{path}'"

        script = (
            f"$filelist = {join_s};"
            "$col = New-Object Collections.Specialized.StringCollection; "
            "foreach($file in $filelist){$col.add($file)}; "
            "Add-Type -Assembly System.Windows.Forms; "
            "[System.Windows.Forms.Clipboard]::SetFileDropList($col); "
        )

        self.execute_powershell(script)

    def pull(self, force_unicode):
        """faster c type pull"""
        self.file_urls = []

        self.CF_HDROP = 15

        u32 = ctypes.windll.user32
        k32 = ctypes.windll.kernel32
        s32 = ctypes.windll.shell32

        self.OpenClipboard = u32.OpenClipboard
        self.OpenClipboard.argtypes = w.HWND,
        self.OpenClipboard.restype = w.BOOL

        self.GetClipboardData = u32.GetClipboardData
        self.GetClipboardData.argtypes = w.UINT,
        self.GetClipboardData.restype = w.HANDLE

        self.SetClipboardData = u32.SetClipboardData

        self.CloseClipboard = u32.CloseClipboard
        self.CloseClipboard.argtypes = None
        self.CloseClipboard.restype = w.BOOL

        self.DragQueryFile = s32.DragQueryFile
        self.DragQueryFile.argtypes = [w.HANDLE, w.UINT, ctypes.c_void_p, w.UINT]

        # get
        try:
            if self.OpenClipboard(None):
                h_hdrop = self.GetClipboardData(self.CF_HDROP)

                if h_hdrop:
                    # expose force unicode to preferences(if enabled unicode beta setting)
                    FS_ENCODING = getdefaultlocale()[1] if not force_unicode else 'utf-8'
                    file_count = self.DragQueryFile(h_hdrop, -1, None, 0)

                    for index in range(file_count):
                        buf = ctypes.c_buffer(260)
                        self.DragQueryFile(h_hdrop, index, buf, ctypes.sizeof(buf))
                        self.file_urls.append(buf.value.decode(FS_ENCODING))
        except UnicodeError:
            self.CloseClipboard()
            self.pull_files_from_clipboard()
        return self.file_urls

    def pull_files_from_clipboard(self):
        script = (
            "Add-Type -AssemblyName System.Windows.Forms; "
            "$files = Get-Clipboard -Format FileDropList; "
            "if ($files) { $files.fullname }"
        )

        popen, stdout, stderr = self.execute_powershell(script)

        self.file_urls = stdout.split('\n')
        self.file_urls[:] = [file for file in self.file_urls if file != '']

        return self.file_urls

    def get_args(self, script):
        powershell_args = [
            os.path.join(
                os.getenv("SystemRoot"),
                "System32",
                "WindowsPowerShell",
                "v1.0",
                "powershell.exe",
            ),
            "-NoProfile",
            "-NoLogo",
            "-NonInteractive",
            "-WindowStyle",
            "Hidden",
        ]
        script = (
                "$OutputEncoding = "
                "[System.Console]::OutputEncoding = "
                "[System.Console]::InputEncoding = "
                "[System.Text.Encoding]::UTF8; "
                + "$PSDefaultParameterValues['*:Encoding'] = 'utf8'; "
                + script
        )
        args = powershell_args + ["& { " + script + " }"]
        return args

    def execute_powershell(self, script):
        parms = {
            'args': self.get_args(script),
            'encoding': 'utf-8',
            'stdout': subprocess.PIPE,
            'stderr': subprocess.PIPE,
        }
        popen = subprocess.Popen(**parms)
        stdout, stderr = popen.communicate()
        return popen, stdout, stderr
