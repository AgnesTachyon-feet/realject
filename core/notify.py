from winotify import Notification

def toast(title: str, msg: str):
    try:
        toast = Notification(app_id="D-Quests",
                             title=title,
                             msg=msg,
                             duration="short")
        toast.set_audio(sound=None, loop=False)
        toast.show()
    except Exception as e:
        print(f"[WinNotify Error] {e}")