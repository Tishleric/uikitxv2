@echo off
echo =====================================================
echo Price Updater Profiling - Production Safe Version
echo =====================================================
echo.
echo This will profile the price updater to find the 14-second bottleneck.
echo NO PRODUCTION CODE WILL BE MODIFIED.
echo.

cd /d Z:\uikitxv2

echo Step 1: Capture Real Messages from Redis
echo ----------------------------------------
echo Make sure spot risk watcher is running!
echo This will capture 3 messages for testing.
echo.
pause

echo Capturing messages...
python tests\diagnostics\capture_redis_messages.py 3

echo.
echo Step 2: Profile Using Captured Messages (Offline)
echo -------------------------------------------------
echo This is completely safe - no live connections.
echo.
pause

python tests\diagnostics\profile_current_implementation.py --offline

echo.
echo Step 3: (Optional) Profile Live Messages  
echo ----------------------------------------
echo This will create a separate profiling instance.
echo It will NOT interfere with production.
echo.
echo Do you want to run live profiling? (Ctrl+C to skip)
pause

python tests\diagnostics\profile_current_implementation.py --live

echo.
echo =====================================================
echo Profiling Complete!
echo =====================================================
echo.
echo Check the results above to see which operation takes 14 seconds.
echo Profile details saved to: tests\diagnostics\profiles\
echo.
echo No production code was modified.
echo.
pause