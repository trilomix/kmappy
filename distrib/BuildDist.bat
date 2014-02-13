rd /s /q build
rd /s /q dist
python setup.py py2exe
copy ..\wxwin.ico dist\wxwin.ico
pause
