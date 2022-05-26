import http.server
import socketserver
import threading

from . import m3u8_cache


class LocalM3u8_Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        fn = self.path.split("/")[1]
        if fn.endswith(".m3u8"):  # for better understanding url
            video_id = fn.split(".m3u8")[0]

            # # update m3u8 for next request
            # m3u8_cache.request_remote_m3u8_async(video_id)

            if m3u8_cache.g_m3u8_cache.get(video_id):
                self.send_response(200)
                self.send_header("Content-type", "text/plain; charset=UTF-8")
                self.end_headers()

                data = m3u8_cache.g_m3u8_cache[video_id]
                self.wfile.write(data.encode("utf-8"))
                return

        self.send_response(404)
        self.end_headers()
        return


g_http_server = None


def __start_server():
    global g_http_server
    PORT = 10800
    Handler = LocalM3u8_Handler
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        g_http_server = httpd
        httpd.serve_forever()


def start_server():
    shutdown_server()
    threading.Thread(target=__start_server, daemon=True).start()


def shutdown_server():
    if g_http_server:
        g_http_server.shutdown()
