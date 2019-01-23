# swapdredge
Dig through a dd image of a linux swap partition, such as a dd file recovered by testdisk.


## Installation
* Installation and usage require the "Add to system path" option to be checked while installing python from python.org in order for python command to be used without specifying the install directory.
* You may have to have administrator priveleges (on Windows: right-click Windows menu, click Administrator Command Prompt) for install to work. In a terminal, type `pip install https://github.com/poikilos/mgep/zipball/master`
  (or on Windows Command Prompt, you may have to do:
  `python -m pip install https://github.com/poikilos/mgep/zipball/master`)


## Usage
You can type the command for usage: `python swapdredge/command_line.py`

### Examples:
Here's how you could look for your missing kivy install script in your swap file, after doing an offline recovery of your swap partition using testdisk (which by default saves the image as image.dd):
```bash
# requires testdisk
# assumes you have already done: testdisk /dev/sda2
# and chosen to recover the swap file to image.dd in current directory
python $HOME/git/swapdredge/swapdredge/command_line.py image.dd --find "install kivy"
```
or on windows:
```batch
python %USERPROFILE%/Documents/GitHub/swapdredge/swapdredge/command_line.py image.dd --find "install kivy"
```
