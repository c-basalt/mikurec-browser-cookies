#!/usr/bin/env python3
import subprocess
import traceback

import wx

from extractor import auto_extract_cookies
from wpf_config import get_path_and_proc, set_cookies


class BoxSizerPanel(wx.Panel):
    def __init__(self, *args, resize_callback=None, border=10, **kwargs):
        super().__init__(*args, **kwargs)
        self.panel_sizer = wx.BoxSizer(wx.VERTICAL)
        self.resize_callback = resize_callback or getattr(self.GetParent(), 'refresh', None)
        self.border = border

    def add_to_panel(self, widget, refresh=True):
        self.panel_sizer.Add(widget, 0, wx.ALL | wx.ALIGN_LEFT, self.border)
        if refresh:
            self.refresh()

    def clear_widgets(self, remove_type=None, refresh=True):
        for child in self.GetChildren():
            if remove_type is None or isinstance(child, remove_type):
                child.Destroy()
        if refresh:
            self.refresh()

    def refresh(self, propagate=True):
        self.panel_sizer.Layout()
        self.SetSizerAndFit(self.panel_sizer)
        if self.resize_callback and propagate:
            self.resize_callback()


class MessageDialogCN(wx.MessageDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.SetOKCancelLabels('确定', '取消')

    @classmethod
    def msg_box(cls, *args, **kwargs):
        with cls(*args, **kwargs) as dialog:
            return dialog.ShowModal()


class ProfilePanel(BoxSizerPanel):
    def __init__(self, uid, uname, cookie_str, *args, **kwargs):
        super().__init__(*args, border=3, **kwargs)
        self.cookie_str = cookie_str

        self.profile_label = wx.StaticText(self, label=f'{uname} ({uid})')
        self.add_to_panel(self.profile_label)

        clipboard_btn = wx.Button(self, label='复制cookies到剪贴板')
        clipboard_btn.Bind(wx.EVT_BUTTON, self._on_select_copy)
        self.add_to_panel(clipboard_btn, refresh=False)

        send_btn = wx.Button(self, label='自动添加cookies到录播姬（需重启录播姬）')
        send_btn.Bind(wx.EVT_BUTTON, self._on_select_send)
        self.add_to_panel(send_btn, refresh=False)

        self.info_text = wx.StaticText(self, label='')
        self.add_to_panel(self.info_text)

    def clear_text(self, refresh=True):
        self.info_text.SetLabelText('')
        self.clear_widgets(wx.TextCtrl, refresh=refresh)

    def set_info_text(self, text, refresh=True):
        self.info_text.SetLabelText(text)
        if refresh:
            self.refresh()

    def _on_select_copy(self, event):
        for profile in self.GetParent().GetChildren():
            profile.clear_text()

        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(wx.TextDataObject(self.cookie_str))
            wx.TheClipboard.Close()
            self.set_info_text('已复制cookies到剪贴板', refresh=False)
        else:
            self.set_info_text('无法访问剪贴板，请手动复制cookies', refresh=False)
            text = wx.TextCtrl(self, value=self.cookie_str, style=wx.TE_READONLY | wx.TE_MULTILINE, size=(-1, -1))
            self.add_to_panel(text, refresh=False)

        self.refresh()

    def _on_select_send(self, event):
        for profile in self.GetParent().GetChildren():
            profile.clear_text()
        try:
            path, proc = get_path_and_proc()
        except Exception:
            self.set_info_text('录播姬检测失败')
            MessageDialogCN.msg_box(
                None, f'录播姬检测失败：\n{traceback.format_exc()}', caption='错误', style=wx.ICON_ERROR)
            traceback.print_exc()
            return
        if not path:
            if MessageDialogCN.msg_box(
                None, '未找到录播姬，需手动提供工作目录（录播姬启动时选择的文件夹）',
                caption='未找到录播姬', style=wx.OK | wx.CANCEL
            ) == wx.ID_CANCEL:
                self.set_info_text('未找到录播姬')
                return
            with wx.FileDialog(
                None, "打开工作目录", wildcard="工作目录配置文件|config.json", style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST
            ) as fileDialog:
                if fileDialog.ShowModal() == wx.ID_CANCEL:
                    self.set_info_text('未找到录播姬')
                    return
                path = fileDialog.GetPath()
        while True:
            MessageDialogCN.msg_box(None, '自动添加cookies需WPF版录播姬退出后才能有效，请确保退出录播姬后继续',
                                    caption='请确认录播姬已退出')
            if not proc or not proc.is_running():
                break
        try:
            backup_fn = set_cookies(path, self.cookie_str)
            self.set_info_text(f'cookies设置完成, 旧配置已备份至 {backup_fn}')
        except Exception:
            self.set_info_text('cookies设置失败')
            MessageDialogCN.msg_box(
                None, f'cookies设置失败：\n{traceback.format_exc()}', caption='错误', style=wx.ICON_ERROR)
            traceback.print_exc()
            return
        if not proc:
            MessageDialogCN.msg_box(None, '设置完成，请启动录播姬，进入高级设置检查cookies是否生效', caption='cookies设置完成')
        else:
            if MessageDialogCN.msg_box(
                None, '设置完成，请启动录播姬，进入高级设置检查cookies是否生效。点击确定启动录播姬',
                caption='cookies设置完成', style=wx.OK | wx.CANCEL
            ) == wx.ID_OK:
                try:
                    subprocess.Popen(["start", proc.exe()], shell=True,
                                     creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP)
                except Exception:
                    MessageDialogCN.msg_box(
                        None, f'启动失败，请手动启动录播姬：\n{traceback.format_exc()}', caption='错误', style=wx.ICON_ERROR)
                    traceback.print_exc()


DISCLAIMER = """建议使用小号
如因在录播姬中使用自己的账号，导致账号现在或未来被站点限制、
风控等一切后果由用户自行承担，软件开发者不承担任何责任
Using a sub-account is recommended.
User shall be responsible for all consequences
of using their own account in recorder(s),
including by not limited to, being posed restrictions by website.
Developer shall not be liable for any damages or liabilities."""


class MainFrame(wx.Frame):
    def __init__(self):
        super().__init__(parent=None, title='浏览器cookies提取器')
        self.panel = panel = wx.Panel(self)
        self.main_sizer = v_sizer = wx.BoxSizer(wx.VERTICAL)

        warning_label = wx.StaticText(self.panel, label=DISCLAIMER)
        v_sizer.Add(warning_label, 0, wx.ALL | wx.ALIGN_LEFT, 10)

        self.fetch_btn = wx.Button(panel, label='读取硬盘以获取浏览器cookies')
        self.fetch_btn.Bind(wx.EVT_BUTTON, self._load_cookies)
        v_sizer.Add(self.fetch_btn, 0, wx.ALL | wx.ALIGN_LEFT, 10)

        line = wx.StaticLine(panel)
        v_sizer.Add(line)

        self.profiles_panel = BoxSizerPanel(panel, resize_callback=self._resize_window)
        v_sizer.Add(self.profiles_panel, 0, wx.ALL | wx.ALIGN_LEFT, 10)

        self.add_profile_label('较新chromium内核的浏览器的cookies无法在浏览器打开时读取\n需关闭浏览器或改用手工提取')

        panel.SetSizerAndFit(v_sizer)
        self._resize_window()
        self.Show()

    def _resize_window(self):
        x, y = self.main_sizer.ComputeFittingWindowSize(self)
        self.SetSize((x+60, y+40))

    def add_profile_label(self, text):
        label = wx.StaticText(self.profiles_panel, label=text)
        self.profiles_panel.add_to_panel(label)

    def _load_cookies(self, event):
        try:
            errors, cookies = auto_extract_cookies()
            for error_trace_msg in errors['misc']:
                MessageDialogCN.msg_box(
                    None, f'读取cookies时出现以下错误：\n{error_trace_msg}', caption='错误', style=wx.ICON_ERROR)
            self.profiles_panel.clear_widgets(refresh=False)
            if not cookies:
                self.add_profile_label('读取cookies失败，未从常见浏览器找到B站cookies')
            if 'chrome read permission error' in errors['known']:
                args = '\n    '.join(errors['known']['chrome read permission error'])
                self.add_profile_label(f'chromium内核浏览器打开时会占用cookies文件，无法读取以下的浏览器的cookies：\n    {args}')
                if 'edge' in errors['known']['chrome read permission error']:
                    self.add_profile_label('Edge关闭后会驻留后台\n启动CMD输入 taskkill /F /IM msedge.exe 并回车可结束所有后台Edge进程')
            for uid, (uname, cookie_str) in cookies.items():
                profile = ProfilePanel(uid, uname, cookie_str, self.profiles_panel)
                self.profiles_panel.add_to_panel(profile, refresh=False)
            self.profiles_panel.refresh()
        except Exception:
            MessageDialogCN.msg_box(
                None, f'读取cookies失败：\n{traceback.format_exc()}', caption='错误', style=wx.ICON_ERROR)
            traceback.print_exc()


if __name__ == '__main__':
    app = wx.App()
    frame = MainFrame()
    app.MainLoop()
