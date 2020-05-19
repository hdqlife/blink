kill -9 $(pidof python3)
if [ $1 ];then \
    if [ $1 == clear ];then \
        rm -r aca213cfac04
        /run/media/mmcblk0p1/client/lib/python3.7/python3 app/bLink/client/client.py
    elif [ $1 == debug ];then \
        /run/media/mmcblk0p1/client/lib/python3.7/python3 test.py
    elif [ $1 == testlib ];then \
        /run/media/mmcblk0p1/client/lib/python3.7/python3 app/bLink/client/lib/moutbus/test.py testlib
    elif [ $1 == back ];then \
        /run/media/mmcblk0p1/client/lib/python3.7/python3 app/bLink/client/back.py bli
    else
        echo clear,debug testlib back
    fi
else 
    /run/media/mmcblk0p1/client/lib/python3.7/python3 -m app.bLink.client.back bli log & 
fi