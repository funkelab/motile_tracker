set PATH=%PATH%;C:\ProgramData\scoop\shims

"%PREFIX%\Scripts\pip.exe" install "git+https://github.com/funkelab/motile_tracker@installer"

echo complete post-install > "%PREFIX%\post_install.done"

pause