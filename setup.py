from cx_Freeze import setup, Executable
import os
import sys

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

company_name = 'MahadevDevolper'
product_name = 'Tube Downloader'
#python setup.py bdist_msi
import os.path
PYTHON_INSTALL_DIR = os.path.dirname(os.path.dirname(os.__file__))
print(f"PYTHON_INSTALL_DIR==> {PYTHON_INSTALL_DIR}")
os.environ['TCL_LIBRARY'] = os.path.join(PYTHON_INSTALL_DIR, 'tcl', 'tcl8.6')
os.environ['TK_LIBRARY'] = os.path.join(PYTHON_INSTALL_DIR, 'tcl', 'tk8.6') 

shortcut_table = [
    ("DesktopShortcut",        # Shortcut
     "DesktopFolder",          # Directory_
     "Tube Downloader",     # Name
     "TARGETDIR",              # Component_
     "[TARGETDIR]you_download.exe",   # Target
     None,                     # Arguments
     "This is used to Download Youtube Videos",                     # Description
     None,                     # Hotkey
     None,                     # Icon
     None,                     # IconIndex
     None,                     # ShowCmd
     'TARGETDIR'               # WkDir
     ),

    ("StartupShortcut",        # Shortcut
     "StartupFolder",          # Directory_
     "Tube Downloader",     # Name
     "TARGETDIR",              # Component_
     "[TARGETDIR]you_download.exe",   # Target
     None,                     # Arguments
     None,                     # Description
     None,                     # Hotkey
     None,                     # Icon
     None,                     # IconIndex
     None,                     # ShowCmd
     'TARGETDIR'               # WkDir
     ),


    ]

directory_table = [
    (
        "ProgramMenuFolder",
        "TARGETDIR",
        ".",
    ),
]

msi_data = {
    "Shortcut": shortcut_table,
    "Directory": directory_table,
}

target=Executable(
    script="you_download.py",
    base="Win32GUI",
    icon="youtube.ico",
    shortcut_name="Tube Downloader",
    shortcut_dir="ProgramMenuFolder",  
    copyright="Copyright (C) 2024 MahadevDevolper",
    )

bdist_msi_options = {
    'data': msi_data,
    'upgrade_code': '{66620F4A-DC3A-11E2-B341-112219E9B01E}',
    'add_to_path': True,
    "install_icon" : "youtube.ico",
    'initial_target_dir': r'[ProgramFilesFolder]\%s\%s' % (company_name, product_name),
    }

build_exe_options = {
    'include_files': [resource_path('data'), resource_path('tk86t.dll'), resource_path('tcl86t.dll'), resource_path('d11.txt'), resource_path('d22.txt')],
    "packages": ["os", "win32api", "win32ui", "win32con", "win32gui"]
    }


setup(name=product_name, 
      version="12.4.0",
      author=company_name,
      author_email='mahadevadityamukhiya@gmail.com',
      description="YouTube Video Downloader Made by Aditya Mukhiya",
      url='https://mahadevadity8080.pythonanywhere.com/',
      executables=[target],
      options={
          'bdist_msi': bdist_msi_options,
          'build_exe': build_exe_options})

