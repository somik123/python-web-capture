from playwright.sync_api import sync_playwright
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, unquote, parse_qsl
import json, argparse, subprocess, validators, os, hashlib

# get env vars
secret = os.environ.get("PYCAPTURE_SECRET", "")
save_dir = os.environ.get("PYCAPTURE_DATA", "/tmp")
cache = os.environ.get("PYCAPTURE_CACHE", "no")

# Use playwright to capture a screenshot of the page
def takeScreenshot(url, save_file, full):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.goto(url)
        page.screenshot(path=save_file, full_page=full)
        browser.close()


class MyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        url = ""
        full = False
        refresh = False
        try:
            # Parse the url into queries
            query = {}
            parsed_path = urlparse(self.path)
            index = self.path.index('?') + 1
            query_parse = parse_qsl(self.path[index:], keep_blank_values=True)
            print(query_parse)
            for x in query_parse:
                query[x[0]] = x[1]
            print(query)

            # validate the url and query parameters
            tmp_url = unquote( query["url"] )
            if "full" in query.keys():
                full = True
            if "refresh" in query.keys():
                refresh = True
            parsed_url = urlparse(tmp_url)
            if validators.url(tmp_url) and parsed_url.scheme == "https" :
                if len(secret) > 0 and secret == query["secret"]:
                    url = tmp_url
        except:
           print("Exception validator")

        # Data OK
        self.send_response(200)
        if len(url) > 10:
            # If image is cached, get from there instead
            file_name = "screenshot.png"
            if cache.lower() == "yes" :
                file_name = hashlib.sha256(url.encode()).hexdigest() + ".png"
            save_file = save_dir + "/" + file_name
            try:
                # If image is not cached, cache it (if enabled)
                if refresh or not os.path.exists(save_file):
                    takeScreenshot(url, save_file, full)

                # Start returning image
                with open(save_file, "rb") as image_file:
                    self.send_header('Content-Type', 'image/png')
                    self.end_headers()
                    self.wfile.write(image_file.read())
            except:
                self.send_header('Content-Type', 'text/plain')
                self.end_headers()
                self.wfile.write("ERROR".encode('utf-8'))
        else:
            self.send_header('Content-Type', 'text/plain')
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
