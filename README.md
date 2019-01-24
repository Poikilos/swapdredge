# swapdredge
Dig through a dd image of a linux swap partition, such as a dd file recovered by testdisk.
This is an advanced tool for searching large files. You may not get data that can be cleanly copied & pasted if you are searching a disk or partition image file, as the file would also contain structural data (metadata) interrupting file contents, and often fragmentation.

## Installation
* Installation and usage require the "Add to system path" option to be checked while installing python from python.org in order for python command to be used without specifying the install directory.
* You may have to have administrator priveleges (on Windows: right-click Windows menu, click Administrator Command Prompt) for install to work. In a terminal, type `pip install https://github.com/poikilos/mgep/zipball/master`
  (or on Windows Command Prompt, you may have to do:
  `python -m pip install https://github.com/poikilos/mgep/zipball/master`)


## Usage
You can type the command for usage: `python swapdredge/command_line.py`

### Examples:
* Here's how you could look for your missing kivy install script in your swap file, after doing an offline recovery of your swap partition using testdisk (which by default saves the image as image.dd):
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

* Here's how you could look for your system setup script on linux:
```bash
python $HOME/git/swapdredge/swapdredge/command_line.py image.dd --find "rpm -iv rpmfusion-nonfree-release-28.noarch.rpm"
```
sample output:
```
config: {'preview_show_before': 512, 'find': 'rpm -iv rpmfusion-nonfree-release-28.noarch.rpm', 'preview_show_after': 512}
paths: ['image.dd']
image.dd progress: [found at: 3784202030[3784202030]--------]
0DWexitAgpg --keyserver pgp.mit.edu --recv-keys 09eab3f2!�5K9V�!export�,▒O�+-�9V1 2K9V�5K9V�▒J9V5K9V01dnf -y install meld9VV0���S9VpH9Vs; declare -f) | /usr/bin/which --tty-only --read-alias --read-functions --show-tilde --show-doteArpm -iv rpmfusion-nonfree-release-28.noarch.rpm !`1K9V�3K9Vdircolor!]K9V !�7K9V��I9V!dnf history list --tty-!#1547080232�-functio!5K9V�7K9V1LS_COLORS=rs=0:di=38;5;33:ln=38;5;51:mh=00:pi=40;38;5;11:so=38;5;13:do=38;5;5:bd=48;5;232;38;5;11:cd=48;5;232;38;5;3:or=48;5;232;38;5;9:mi=01;05;37;41:su=48;5;196;38;5;15:sg=48;5;11;38;5;16:ca=48;5;196;38;5;226:tw=48;5;10;38;5;16:ow=48;5;10;38;5;21:st=48;5;21;38;5;15:ex=38;5;40:*.tar=38;5;9:*.tgz=38;5;
########################################]
len(results): 1
results: [3784202030]
```
where 3784202030 is the location of the byte where value of 'find' occurs (`rpm -iv rpmfusion-nonfree-release-28.noarch.rpm` in this case).
Next, you could do (where value after start is byte location, such as 3784202030 from above minus bytes from expected start of file to that location such as 800; and where value after length is how many bytes you want to display, 4KB in this case [3*1024 bytes]):
```bash
python $HOME/git/swapdredge/swapdredge/command_line.py image.dd --dump --start 3784201230 --length 4096
```
