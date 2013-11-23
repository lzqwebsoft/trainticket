# coding = utf-8
from cx_Freeze import setup, Executable

setup(
	name="trainticket",
	version = '0.1',
	description = '体验版',
	executables=[Executable("access12306.py", icon='logo.ico')])