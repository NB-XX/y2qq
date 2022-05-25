import os
import time

g_update_path = "TempUpdateFiles"


def update_release():
    import shutil

    files = os.listdir(os.path.join(g_update_path))
    for filename in files:
        try:
            shutil.move(
                os.path.join(g_update_path, filename),
                os.path.join(g_update_path, "..", filename),
            )
        except Exception as e:
            pass
    shutil.rmtree(os.path.join(g_update_path))


def restart_exe():
    from subprocess import Popen

    Popen(os.path.join(os.getcwd(), "y2qq_GUI.exe"))


if __name__ == "__main__":
    try:
        time.sleep(1)  # delay for windows closing
        update_release()
        restart_exe()
    except Exception as e:
        pass
