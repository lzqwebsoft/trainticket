# coding: utf8
import io
import random
from PIL import Image, ImageTk
import tkinter as tk
from urllib.request import urlopen

# 将网络中获取的验证码图片使用弹窗显示
class LoginFrame:
    def __init__(self, url):
        self.url = url

        self.root = tk.Tk()
        self.root.title("验证码")

        image_bytes = urlopen(self.url).read()
        # internal data file
        data_stream = io.BytesIO(image_bytes)
        # open as a PIL image object
        self.pil_image = Image.open(data_stream)
        # convert PIL image object to Tkinter PhotoImage object
        self.tk_image = ImageTk.PhotoImage(self.pil_image)
        self.label = tk.Label(self.root, image=self.tk_image, bg='brown')
        self.label.pack(padx=5, pady=5)
        self.button = tk.Button(self.root, text ="刷新验证码", command = self.refreshImg)
        self.button.pack(padx=5, pady=5)

        randCodeLable = tk.Label(self.root, text="验证码：")
        randCodeLable.pack(padx=5, pady=5)
        self.randCode = tk.Entry(self.root)
        self.randCode.pack(padx=5, pady=5)

        self.loginButton = tk.Button(self.root, text ="登录", default=tk.ACTIVE)
        self.loginButton.pack(padx=5, pady=5)

    def refreshImg(self):
        url = self.url + "&" + str(random.random())
        image_bytes = urlopen(url).read()
        data_stream = io.BytesIO(image_bytes)
        self.pil_image = Image.open(data_stream)
        self.tk_image = ImageTk.PhotoImage(self.pil_image)
        self.label.configure(image = self.tk_image)

    # 显示URL地址指定图片
    def show(self):
        w, h = self.pil_image.size

        # 窗体居中
        width = w + 100
        height = h + 160
        ws = self.root.winfo_screenwidth()
        hs = self.root.winfo_screenheight()
        x = int((ws/2) - (width/2) )
        y = int((hs/2) - (height/2) )
        self.root.geometry('{}x{}+{}+{}'.format(width, height, x, y))
        # 禁止窗体改变大小
        self.root.resizable(False, False)
        self.root.mainloop()

    def quit(self):
        self.root.destroy()