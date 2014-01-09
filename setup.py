# coding = utf-8
from cx_Freeze import setup, Executable

build_exe_options = {
    'compressed': True,
    'packages':['ui', 'core', 'common'],
}
setup(
    name="trainticket",
    version='0.2.0',
    description='风险版',
    options={'build_exe': build_exe_options},
    executables=[Executable("access12306.py", icon='logo.ico')])