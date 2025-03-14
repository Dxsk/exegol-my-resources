# Customization of my exegol environment

Exegol allows customizing your environment through the `/opt/my-resources` folder.  
Here are the modifications and additions I've made for my usage.

Link to doc : [Exegol documentation](https://exegol.readthedocs.io/en/latest/exegol-image/my-resources.html/)

## Additions

- SpaceVim for nvim
   - Added SpaceVim configuration for nvim and alias from vim to nvim

- Python and requirements.txt
    - Added a [requirements.txt](setup/python3/requirements.txt) with several useful modules for scripts during CTF/pentest
    - Added a [smb_download.py](setup/python3/smb_downloads.py) script that allows downloading all files from an SMB server
    - Added history with variables {+$USER+}, {+ $TARGET +}, {+ $PASSWORD +} to easily find them in the exegol history
    - Added a function in zsh aliases to quickly launch the script

- Zsh
    - Added history for some commands that I found useful
    - Added an alias to quickly edit and load the `/opt/tools/Exegol-history/profile.sh` [Doc: Dynamic history commands](https://exegol.readthedocs.io/en/latest/getting-started/tips-and-tricks.html#dynamic-history-commands)