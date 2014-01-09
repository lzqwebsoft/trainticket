# About It
This application is uses to access the specified website for booking the train ticket, for the first time, you must set your registered username and password at [12306.cn](http://www.12306.cn/mormhweb/) in config.ini file.

Which uses python 3.3.2 to development, so if you want development by youself, you must deploy a development environment like this:

* First, Click [HERE](http://www.python.org/getit) to download python 3.3.2 and install it.

* Second, Download and install the related expansion pack: [Python Imaging Library(PIL)](http://www.lfd.uci.edu/~gohlke/pythonlibs/#pil).It is used to generate captcha image in the Tk. **Note**: *In python3 Pillow is a replacement for PIL.*

* Last, Optionally. If you want to run it without requiring a Python installation. Maybe you can install [cx_Freeze](http://cx-freeze.sourceforge.net/) for freezing Python scripts into executable Windows programs. Well you can use the command as given below for converts:
```shell
$ python setup.py build
```
