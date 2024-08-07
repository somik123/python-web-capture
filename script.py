from playwright.sync_api import sync_playwright
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, unquote, parse_qsl
import json, argparse, subprocess, validators

def takeScreenshot(url, full):
    with sync_playwright() as playwright:
        #for browser_type in [p.chromium, p.firefox, p.webkit]:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.goto(url)
        page.screenshot(path='/tmp/screenshot.png', full_page=full)
        browser.close()


class MyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        url = ""
        full = False
        try:
            query = {}
            parsed_path = urlparse(self.path)
            index = self.path.index('?') + 1
            query_parse = parse_qsl(self.path[index:], keep_blank_values=True)
            print(query_parse)
            for x in query_parse:
                query[x[0]] = x[1]
            print(query)

            tmp_url = unquote( query["url"] )
            if "full" in query.keys():
                full = True
            parsed_url = urlparse(tmp_url)
            if validators.url(tmp_url) and parsed_url.scheme == "https" :
                url = tmp_url
        except:
           print("Exception validator")

        self.send_response(200)
        if len(url) > 10:
            self.send_header('Content-Type', 'image/png')
            self.end_headers()
            takeScreenshot(url, full)
            with open("/tmp/screenshot.png", "rb") as image_file:
                self.wfile.write(image_file.read())
        else:
            self.end_headers()
            self.wfile.write("ERROR".encode('utf-8'))
        return


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--bind', '-b', default='', metavar='ADDRESS', help='Specify alternate bind address [default: all interfaces]')
    parser.add_argument('port', action='store', default=9808, type=int, nargs='?', help='Specify alternate port [default: 9808]')
    args = parser.parse_args()

    hostName = args.bind
    serverPort = args.port

    webServer = HTTPServer((hostName, serverPort), MyServer)
    cmd = "hostname -I | cut -d\' \' -f1"
    IP = subprocess.check_output(cmd, shell=True).decode("utf-8")
    IP = IP.strip()
    print("Server started http://%s:%s" % (IP, serverPort))

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print("Server stopped.")
