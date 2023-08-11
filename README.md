# MikuRec Browser Cookies

自动为mikufans录播姬从浏览器提取cookies用于登录、完整弹幕录制、限定直播录制等

![检测cookies生效](https://raw.githubusercontent.com/c-basalt/mikurec-browser-cookies/main/%E8%AF%B4%E6%98%8E.png)

设置后请在[高级设置](https://rec.danmuji.org/user/settings/#高级设置)中检查cookies是否生效

## 下载和使用

### 下载运行打包版

从[Release](https://github.com/c-basalt/mikurec-browser-cookies/releases/)页面下载后双击运行即可

### 用本地Python环境执行

安装requirements.txt中的依赖后，运行main.py

```bash
python -m pip install -r requirements.txt
python main.py
```

## 手动提取cookies用于mikufans录播姬

关于怎么手动从浏览器提取cookies用于mikufans录播姬，可以参考如下教程

https://zmtblog.xdkd.ltd/2021/10/06/Get_bilibili_cookie/

找到后将`www=xxx; yyy=zzz`样式的字符串复制并填入[高级设置](https://rec.danmuji.org/user/settings/#高级设置)中的Cookie配置项中即可
