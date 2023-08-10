import traceback

import wx
import wx.grid

from extractor import auto_extract_cookies


class MainFrame(wx.Frame):
    def __init__(self):
        super().__init__(parent=None, title='浏览器cookies提取器')
        self.panel = panel = wx.Panel(self)
        self.main_sizer = v_sizer = wx.BoxSizer(wx.VERTICAL)

        self.fetch_btn = wx.Button(panel, label='读取硬盘以获取浏览器cookies')
        self.fetch_btn.Bind(wx.EVT_BUTTON, self._load_cookies)
        v_sizer.Add(self.fetch_btn, 0, wx.ALL | wx.ALIGN_LEFT, 10)

        line = wx.StaticLine(panel)
        v_sizer.Add(line)

        self.profile_panel = wx.Panel(panel)
        self.profile_panel.SetAutoLayout(True)
        self.profile_sizer = wx.BoxSizer(wx.VERTICAL)
        self.profile_panel.SetSizerAndFit(self.profile_sizer)
        v_sizer.Add(self.profile_panel, 0, wx.ALL | wx.ALIGN_LEFT, 10)

        panel.SetSizerAndFit(v_sizer)
        self._resize_window()
        self.Show()

    def _resize_window(self):
        x, y = self.main_sizer.ComputeFittingWindowSize(self)
        self.SetSize((x+100, y+100))

    def _get_profile_handler(self, cookie_str):
        def _handler(event):
            for child in self.profile_panel.GetChildren():
                if isinstance(child, wx.TextCtrl):
                    child.Destroy()
                    self.profile_sizer.Layout()
                    self._resize_window()
            if wx.TheClipboard.Open():
                wx.TheClipboard.SetData(wx.TextDataObject(cookie_str))
                wx.TheClipboard.Close()
                dialog = wx.MessageDialog(None, '已复制cookies到剪贴板')
            else:
                dialog = wx.MessageDialog(None, '无法访问剪贴板，请手动复制cookies')
                text = wx.TextCtrl(
                    self.profile_panel, value=cookie_str,
                    style=wx.TE_READONLY | wx.TE_MULTILINE, size=(-1, -1))
                self._add_to_profile_panel(text)
            dialog.ShowModal()
        return _handler

    def _add_to_profile_panel(self, widget):
        self.profile_sizer.Add(widget, 0, wx.ALL | wx.ALIGN_LEFT, 10)
        self.profile_sizer.Layout()
        self.profile_panel.SetSizerAndFit(self.profile_sizer)
        self._resize_window()

    def _load_cookies(self, event):
        try:
            for child in self.profile_panel.GetChildren():
                child.Destroy()
            for uid, (uname, cookie_str) in auto_extract_cookies().items():
                profile_btn = wx.Button(self.profile_panel, label=f'{uname} ({uid})')
                profile_btn.Bind(wx.EVT_BUTTON, self._get_profile_handler(cookie_str))
                self._add_to_profile_panel(profile_btn)
        except Exception:
            alert = wx.MessageDialog(None, f'读取cookies失败：\n{traceback.format_exc()}', caption='错误')
            alert.ShowModal()
            traceback.print_exc()


if __name__ == '__main__':
    app = wx.App()
    frame = MainFrame()
    app.MainLoop()
