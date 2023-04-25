del Win11*.iso
git submodule init
git submodule update
powershell -file "%CD%\external\Fido\Fido.ps1" -Win 11 -Ed Pro
ren Win11*.iso Win11.iso