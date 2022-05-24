import time
import io
import os
import threading


def get_filename_with_video_id(video_id):
    return f"tmp_{video_id}.m3u8"


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
            if "#EXT-X-DISCONTINUITY" in line:
                tmp_ts_list.append(line)
    m3u8_info_dict["ts_list"] = tmp_ts_list

    return m3u8_info_dict


def prase_m3u8_with_text(m3u8_text):
    file = io.StringIO(m3u8_text)
    return prase_m3u8(file)


def prase_m3u8_with_file(filename):
    file = open(filename, "r")
    return prase_m3u8(file)


def write_local_m3u8_file(duration, start_seq, seq_list, file_path, is_using_file=True):
    file = open(file_path, "w") if is_using_file else io.StringIO(file_path)
    with file as f:
        f.write("#EXTM3U\n")
        f.write("#EXT-X-VERSION:3\n")
        f.write(duration)
        f.write(f"#EXT-X-MEDIA-SEQUENCE:{start_seq}\n")
        for seq in seq_list:
            f.write(seq)


def merage_m3u8_file(video_id, m3u8_info_dict=None, max_cache_seq=10):
    cur_duration_str = m3u8_info_dict["duration"]
    cur_start_seq = m3u8_info_dict["st_seq"]
    cur_seq_list = m3u8_info_dict["ts_list"]
    cur_max_seq = cur_start_seq + len(cur_seq_list) - 1

    # default
    result_duration_str = cur_duration_str
    result_start_seq = cur_start_seq
    result_seq_list = cur_seq_list

    tmp_file_path = get_filename_with_video_id(video_id)
    if os.path.exists(tmp_file_path):
        old_m3u8_info_dict = prase_m3u8_with_file(tmp_file_path)
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
    write_local_m3u8_file(
        result_duration_str, result_start_seq, result_seq_list, tmp_file_path
    )


def consume_m3u8(video_id):
    tmp_file_path = get_filename_with_video_id(video_id)
    if os.path.exists(tmp_file_path):
        while True:
            m3u8_info_dict = prase_m3u8_with_file(tmp_file_path)
            cur_duration_str = m3u8_info_dict["duration"]
            cur_start_seq = m3u8_info_dict["st_seq"]
            cur_seq_list = m3u8_info_dict["ts_list"]
            if len(cur_seq_list) == 0:
                break
            cur_max_seq = cur_start_seq + len(cur_seq_list) - 1

            result_start_seq = cur_start_seq + 1
            result_seq_list = cur_seq_list[1:]
            write_local_m3u8_file(
                cur_duration_str, result_start_seq, result_seq_list, tmp_file_path
            )

            duration = float(cur_duration_str.split(":")[1].strip())
            time.sleep(duration / 3)


def server_produce_m3u8(video_id):
    thread = threading.Thread(target=consume_m3u8, args=(video_id,), daemon=True)
    thread.start()


def __test():
    tmp_video_id = "231231"
    fp = os.path.join(os.getcwd(), "m3u8_cache", "testFiles")
    m3u8_info_dict = prase_m3u8_with_file(os.path.join(fp, "test1.m3u8"))
    merage_m3u8_file(tmp_video_id, m3u8_info_dict)
    m3u8_info_dict = prase_m3u8_with_file(os.path.join(fp, "test1copy.m3u8"))
    merage_m3u8_file(tmp_video_id, m3u8_info_dict)
    m3u8_info_dict = prase_m3u8_with_file(os.path.join(fp, "test2.m3u8"))
    merage_m3u8_file(tmp_video_id, m3u8_info_dict)
    m3u8_info_dict = prase_m3u8_with_file(os.path.join(fp, "test3.m3u8"))
    merage_m3u8_file(tmp_video_id, m3u8_info_dict)
    m3u8_info_dict = prase_m3u8_with_file(os.path.join(fp, "test4.m3u8"))
    merage_m3u8_file(tmp_video_id, m3u8_info_dict)

    server_produce_m3u8(tmp_video_id)

    while True:
        time.sleep(30)
        break


__test()
