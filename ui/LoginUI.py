# coding: utf8
import io
import random
import tkinter
import socket
import urllib.error
from tkinter import Tk
from urllib.request import urlopen
from PIL import Image, ImageTk
from tkinter.ttk import Label,Button,Entry

# 将网络中获取的验证码图片使用弹窗显示
class LoginFrame:
    def __init__(self, url):
        self.url = url

        self.root = Tk()
        self.root.title("验证码")

        while True:
            try:
                image_bytes = urlopen(self.url).read()
                break
            except socket.timeout:
                print('获取验证码超时：%s\r\n重新获取.' % (self.url))
                continue
            except urllib.error.URLError as e:
                if isinstance(e.reason, socket.timeout):
                    print('获取验证码超时：%s\r\n重新获取.' % (self.url))
                    continue
        # internal data file
        data_stream = io.BytesIO(image_bytes)
        # open as a PIL image object
        self.pil_image = Image.open(data_stream)
        # convert PIL image object to Tkinter PhotoImage object
        self.tk_image = ImageTk.PhotoImage(self.pil_image)
        self.label = Label(self.root, image=self.tk_image, background='brown')
        self.label.pack(padx=5, pady=5)
        self.button = Button(self.root, text="刷新验证码", command=self.refreshImg)
        self.button.pack(padx=5, pady=5)

        randCodeLable = Label(self.root, text="验证码：")
        randCodeLable.pack(padx=5, pady=5)
        self.randCode = Entry(self.root)
        self.randCode.pack(padx=5, pady=5)

        self.loginButton = Button(self.root, text="登录", default=tkinter.ACTIVE)
        self.loginButton.pack(padx=5, pady=5)

    def refreshImg(self):
        url = self.url + "&" + str(random.random())
        while True:
            try:
                image_bytes = urlopen(url).read()
                data_stream = io.BytesIO(image_bytes)
                self.pil_image = Image.open(data_stream)
                self.tk_image = ImageTk.PhotoImage(self.pil_image)
                self.label.configure(image=self.tk_image)
                break
            except socket.timeout:
                print('获取验证码超时：%s\r\n重新获取.' % (self.url))
                continue
            except urllib.error.URLError as e:
                if isinstance(e.reason, socket.timeout):
                    print('获取验证码超时：%s\r\n重新获取.' % (self.url))
                    continue

    # 显示URL地址指定图片
    def show(self):
        w, h = self.pil_image.size

        # 窗体居中
        width = w + 100
        height = h + 160
        ws = self.root.winfo_screenwidth()
        hs = self.root.winfo_screenheight()
        x = int((ws / 2) - (width / 2))
        y = int((hs / 2) - (height / 2))
        self.root.geometry('{}x{}+{}+{}'.format(width, height, x, y))
        # 禁止窗体改变大小
        self.root.resizable(False, False)
        self.root.mainloop()


    def quit(self):
        self.root.destroy()