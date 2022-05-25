import traceback
import time
import io
import os
import threading
import requests

g_m3u8_cache = {}  # virtual_filename: text
g_m3u8_source = {}  # video_id: url
g_local_m3u8_service = {}  # video_id: thread


def setup_m3u8_src(video_id, m3u8_url, mask=0):
    global g_m3u8_source
    g_m3u8_source[video_id] = m3u8_url


def get_filename_with_video_id(video_id, other_mask="0"):
    return f"local_{video_id}_{other_mask}.m3u8"


def prase_m3u8(file):
    m3u8_info_dict = {}
    with file as f:
        tmp_ts_list = []
        for line in f:
            if "#EXT-X-TARGETDURATION:" in line:
                m3u8_info_dict["duration"] = line
            if "#EXT-X-MEDIA-SEQUENCE" in line:
                start_seq = int(line.split(":")[1].strip())
                m3u8_info_dict["st_seq"] = start_seq
            if "#EXTINF:" in line:
                inf = line
                url = f.readline()
                tmp_ts_list.append(f"{inf}{url}")
            if "#EXT-X-DISCONTINUITY\n" in line:
                tmp_ts_list.append(line)
    m3u8_info_dict["ts_list"] = tmp_ts_list

    return m3u8_info_dict


def prase_m3u8_with_text(m3u8_text):
    file = io.StringIO(m3u8_text)
    return prase_m3u8(file)


def prase_m3u8_with_path(fp):
    file = open(fp, "r")
    return prase_m3u8(file)


def prase_m3u8_with_virtual_path(filename):
    global g_m3u8_cache
    if g_m3u8_cache.get(filename):
        return prase_m3u8_with_text(g_m3u8_cache[filename])
    else:
        return None


def write_local_m3u8_file(duration_str, start_seq, seq_list, file_path, is_file=False):
    global g_m3u8_cache

    file = open(file_path, "w") if is_file else io.StringIO()
    with file as f:
        f.write("#EXTM3U\n")
        f.write("#EXT-X-VERSION:3\n")
        f.write(duration_str)
        # try:
        #     seq_duration = float(seq_list[-1].split("#EXTINF:")[1].split(",\n")[0])
        # except Exception as e:
        #     seq_duration = 1.0
        # duration = len(seq_list) * seq_duration
        # f.write(f"#EXT-X-TARGETDURATION:{duration}\n")
        f.write(f"#EXT-X-MEDIA-SEQUENCE:{start_seq}\n")
        for seq in seq_list:
            f.write(seq)

        if is_file == False:
            g_m3u8_cache[file_path] = file.getvalue()
            print("-------------------------------")
            print(file_path)
            print("-------------------------------")
            # print(g_m3u8_cache[file_path])
            print(f"current_seq_len:{len(seq_list)}")


def merge_m3u8_file(video_id, m3u8_info_dict):
    global g_m3u8_cache
    cur_duration_str = m3u8_info_dict["duration"]
    cur_start_seq = m3u8_info_dict["st_seq"]
    cur_seq_list = m3u8_info_dict["ts_list"]
    cur_max_seq = cur_start_seq + len(cur_seq_list) - 1

    # default
    result_duration_str = cur_duration_str
    result_start_seq = cur_start_seq
    result_seq_list = cur_seq_list

    tmp_file_path = video_id
    if g_m3u8_cache.get(tmp_file_path):
        old_m3u8_info_dict = prase_m3u8_with_virtual_path(tmp_file_path)
        old_start_seq = old_m3u8_info_dict["st_seq"]
        old_seq_list = old_m3u8_info_dict["ts_list"]
        old_max_seq = old_start_seq + len(old_seq_list) - 1

        misssing_diff_seq = cur_start_seq - old_max_seq
        if misssing_diff_seq <= 0:
            diff_seq = cur_start_seq - old_start_seq
            if diff_seq > 0:
                result_seq_list = old_seq_list[:diff_seq] + cur_seq_list
                result_start_seq = old_start_seq
            else:  # ignore older seq
                return
        else:  # add missing seq
            loop_times = misssing_diff_seq - 1
            misssing_list = ["#EXT-X-DISCONTINUITY\n" for i in range(loop_times)]
            result_seq_list = old_seq_list + misssing_list + cur_seq_list
            result_start_seq = old_start_seq

    # clip the #EXT-X-DISCONTINUITY at the head
    result_start_seq, result_seq_list = clip_seq_if_start_with_discontinuty(
        result_start_seq, result_seq_list
    )

    # keep ablout 60 seq
    if len(result_seq_list) > 60:
        result_start_seq, result_seq_list = clip_seq_if_start_with_discontinuty(
            result_start_seq, result_seq_list, clip_num=10
        )

    write_local_m3u8_file(
        result_duration_str, result_start_seq, result_seq_list, tmp_file_path
    )


def clip_seq_if_start_with_discontinuty(result_start_seq, result_seq_list, clip_num=0):
    tmp_discontinuity_count = 0
    for seq in result_seq_list:
        if "#EXT-X-DISCONTINUITY" in seq:
            tmp_discontinuity_count += 1
        else:
            break

    # select max clip num
    clip_num = max(tmp_discontinuity_count, clip_num)

    if clip_num > 0:
        result_start_seq += clip_num
        result_seq_list = result_seq_list[clip_num:]

        print(f"Clipping head: [{clip_num}]")
    return result_start_seq, result_seq_list


def __consume_m3u8(video_id):
    global g_m3u8_cache
    global g_m3u8_source

    t = threading.currentThread()
    tmp_file_path = video_id

    retry_times = 0
    try:
        while getattr(t, "do_run", True):
            is_request_ok = request_remote_m3u8_sync(video_id)

            m3u8_info_dict = prase_m3u8_with_virtual_path(tmp_file_path)
            cur_duration_str = m3u8_info_dict.get("duration")
            cur_start_seq = m3u8_info_dict.get("st_seq")
            cur_seq_list = m3u8_info_dict.get("ts_list", [])

            if (
                m3u8_info_dict == None
                or len(cur_seq_list) == 0
                or is_request_ok == False
            ):  # no seq, should retry
                time.sleep(1)
                retry_times += 1
                if retry_times >= 10:
                    break
            else:
                retry_times = 0

            duration = float(cur_duration_str.split(":")[1].strip())
            try:
                seq_duration = float(
                    cur_seq_list[-1].split("#EXTINF:")[1].split(",\n")[0]
                )
            except Exception as e:  # handle
                seq_duration = 1.0

            sleep_time = max(seq_duration, 1)
            current_seq_len = len(cur_seq_list)
            if current_seq_len > 60:  # for better catching up
                remove_seq = 5
                result_start_seq = cur_start_seq + remove_seq
                result_seq_list = cur_seq_list[remove_seq:]
                write_local_m3u8_file(
                    cur_duration_str, result_start_seq, result_seq_list, tmp_file_path
                )
                print(f"Deleted 5 seq, Current:{current_seq_len - remove_seq}")
            elif current_seq_len > 5:  # buffer seq
                remove_seq = 1
                result_start_seq = cur_start_seq + remove_seq
                result_seq_list = cur_seq_list[remove_seq:]
                write_local_m3u8_file(
                    cur_duration_str, result_start_seq, result_seq_list, tmp_file_path
                )
                print(f"Deleted 1 seq, Current:{current_seq_len - remove_seq}")
            else:
                sleep_time = 1
            print(f"Current Seq len:{current_seq_len}")
            time.sleep(sleep_time)
    except Exception as e:
        err_str = traceback.format_exc()
        print(err_str)
        pass


def request_remote_m3u8_sync(video_id):
    is_OK = False
    try:
        url = g_m3u8_source[video_id]
        ret = requests.get(url)
        merge_m3u8_file(video_id, prase_m3u8_with_text(ret.text))
        is_OK = True
    except Exception as e:
        err_str = traceback.format_exc()
        print(err_str)
    return is_OK


def request_remote_m3u8_async(video_id):
    thread = threading.Thread(target=request_remote_m3u8_sync, args=(video_id,))
    thread.start()


def server_produce_m3u8(video_id, m3u8_url):
    global g_local_m3u8_service
    setup_m3u8_src(video_id, m3u8_url)

    # if g_local_m3u8_service.get(video_id):
    #     g_local_m3u8_service[video_id].do_run = False
    #     time.sleep(2)  # wait for thread end
    # thread = threading.Thread(target=__consume_m3u8, args=(video_id,))
    # g_local_m3u8_service[video_id] = thread
    # thread.start()
    # time.sleep(5)  # wait for thread requesting first m3u8 files

    # block retry for init m3u8
    for i in range(3):
        is_request_ok = request_remote_m3u8_sync(video_id)
        if is_request_ok:
            break
        time.sleep(1)
    # resturn local m3u8 url
    return f"http://127.0.0.1:10800/{video_id}.m3u8"


def __test():
    tmp_video_id = "231231"
    fp = os.path.join(os.getcwd(), "m3u8_cache", "testFiles")
    m3u8_info_dict = prase_m3u8_with_path(os.path.join(fp, "test1.m3u8"))
    merge_m3u8_file(tmp_video_id, m3u8_info_dict)
    m3u8_info_dict = prase_m3u8_with_path(os.path.join(fp, "test1copy.m3u8"))
    merge_m3u8_file(tmp_video_id, m3u8_info_dict)
    m3u8_info_dict = prase_m3u8_with_path(os.path.join(fp, "test2.m3u8"))
    merge_m3u8_file(tmp_video_id, m3u8_info_dict)
    m3u8_info_dict = prase_m3u8_with_path(os.path.join(fp, "test3.m3u8"))
    merge_m3u8_file(tmp_video_id, m3u8_info_dict)
    m3u8_info_dict = prase_m3u8_with_path(os.path.join(fp, "test4.m3u8"))
    merge_m3u8_file(tmp_video_id, m3u8_info_dict)

    print(g_m3u8_cache[tmp_video_id])
    # server_produce_m3u8(tmp_video_id)
    # while True:
    #     time.sleep(30)
    #     break


# __test()
