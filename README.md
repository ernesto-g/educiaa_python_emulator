# Python emulator for EDU-CIAA

This program emulates an EDU-CIAA board running micropython.

##Supported classes in pyb module:
  - LED
  - Switch
  - UART
  - Pin
  - ADC
  - DAC
  - Timer
  - EEPROM
  - ExtInt


### Running the code from binaries

Download the proper installer from releases section: https://github.com/ernesto-g/educiaa_python_emulator/releases

#### Usage from command line

After installation, execute 'EmulatorLauncher' (unix) or 'EmulatorLauncher.exe' (windows) passing as argument the python script file to be emulated.

example:
```sh
$ cd /opt/educiaa_python_emulator
$ ./EmulatorLauncher /home/user/script.py
```

#### Usage from IDE
This emulator can be launched from educiaa-python-editor. Go to 'EDU-CIAA' menu and select 'Emulator'. Current script will be executed.


### Running the code from source

##### Linux
The following packages are required:
  - git
  - python-gtk2
  

##### Windows
The following programs are required:
  - git bash
  - python-2.7
  - pygtk-all-in-one-2.24.2.win32-py2.7
  - pywin32-219.win32-py2.7

##### OSX
The following packages are required:
  - git
  
Open a terminal and write:

```sh
$ git clone https://github.com/ernesto-g/educiaa_python_emulator.git
$ cd educiaa_python_emulator
$ python EmulatorLauncher.py script.py
```
Where 'script.py' is the python script to be emulated.


##Developer

### Creating Windows Executable

```sh
$ cd PyInstaller-3.1
$ python pyinstaller.py --clean --noconsole --ico ../icons/icon.ico ../EmulatorLauncher.py
```
Executable file EmulatorLauncher.exe will be found in EmulatorLauncher/dist/EmulatorLauncher directory.
Copy files in PyInstaller-3.1/extraFiles to PyInstaller-3.1/EmulatorLauncher/dist/EmulatorLauncher

### Creating Linux Executable

```sh
$ cd PyInstaller-3.1
$ python pyinstaller.py --clean --noconsole --ico ../icons/icon.ico ../EmulatorLauncher.py
```
Executable file EmulatorLauncher will be found in EmulatorLauncher/dist/EmulatorLauncher directory.
Copy files in PyInstaller-3.1/extraFiles to PyInstaller-3.1/EmulatorLauncher/dist/EmulatorLauncher
