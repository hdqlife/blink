#cp -r /run/media/mmcblk0p1/client/ptvsd /run/media/mmcblk0p1/client/lib/python3.7/site-packages/
kills=$(pidof python3)
if [ $kills ];then \
    kill -9 $(pidof python3)
fi
if [ $1 ];then \
    if [ $1 == bac ];then \
        /run/media/mmcblk0p1/client/lib/python3.7/python3 -m app.bLink.client.common.bac
    elif [ $1 == debug ];then \
        /run/media/mmcblk0p1/client/lib/python3.7/python3 -m log.ptvsdrun debug
    else
        echo bac
    fi
else /run/media/mmcblk0p1/client/lib/python3.7/python3 -m log.ptvsdrun
fi

