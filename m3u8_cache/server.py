import http.server
import socketserver

import m3u8_cache


class LocalM3u8_Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        fn = self.path.split("/")[1]
        if fn.endswith(".m3u8"):
            if m3u8_cache.g_m3u8_cache.get(fn):
                self.send_response(200)
                self.send_header("Content-type", "text/plain; charset=UTF-8")
                self.end_headers()

                data = m3u8_cache.g_m3u8_cache[fn]
                self.wfile.write(data.encode("utf-8"))
                return

        self.send_response(404)
        self.end_headers()
        return


def start_server():
    PORT = 10800
    Handler = LocalM3u8_Handler
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        httpd.serve_forever()


start_server()
