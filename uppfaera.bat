@echo off
cd /d "C:\Users\ArnarTS\liverpool-trip"
echo.
echo ==============================================
echo   StockBreak - Uppfaera gogn
echo ==============================================
echo.

echo [1/2] Saeki hlutabrefagogn...
python update_stocks.py

echo.
echo [2/2] Sendi a GitHub...
git add stocks_data.json
git commit -m "uppfaera gogn"
git push

echo.
echo ==============================================
echo   Lokid! Vefsidan er uppfaerd.
echo ==============================================
echo.
pause