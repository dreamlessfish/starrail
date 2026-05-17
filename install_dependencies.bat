@echo off
chcp 65001 >nul
echo ========================================
echo 安装Python依赖库
echo ========================================
echo.

cd /d H:\

echo 正在安装依赖库...
pip install -r requirements.txt

echo.
echo ========================================
echo 安装完成！
echo ========================================
pause


