@echo off
chcp 65001 >NUL
SET PYTHONUNBUFFERED=TRUE
start cmd /k python\python.exe menu.py
