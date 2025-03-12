echo Added by post-install script > "%PREFIX%\post_install_sentinel.txt"

"%PREFIX%\Scripts\pip.exe" install git+https://github.com/funkelab/motile_tracker@installer
