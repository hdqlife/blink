from tool.udpbackdoor import run
def init():
    try:
        from app.bLink.client.client import run as apprun
        apprun()
    except Exception as e:
        import traceback
        traceback.print_exc()
        print('run error',e)
run(init)
