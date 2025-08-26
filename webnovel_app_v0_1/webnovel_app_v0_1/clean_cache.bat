@echo off
REM === Clean caches and logs ===
for /d /r %%d in (__pycache__) do if exist "%%d" rd /s /q "%%d"
if exist .venv\Scripts\python.exe (
    echo Venv exists. To remove venv completely, run: rmdir /s /q .venv
)
if exist app\app.log del /q app\app.log
echo Done.
