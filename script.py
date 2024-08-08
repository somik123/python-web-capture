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

    def error_responder(self, error_msg):
        msg_json = json.dumps(error_msg)
        print(msg_json)
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(msg_json.encode('utf-8'))
        return

    def do_GET(self):
        if self.path == '/favicon.ico':
            with open("favicon.ico", "rb") as favicon_file:
                self.send_response(200)
                self.send_header('Content-Type', 'image/x-icon')
                self.end_headers()
                self.wfile.write(favicon_file.read())
                return
            print("")
            return
        else:
            error_msg = {
                "status": "ERROR",
                "request": self.path,
                "url": "",
                "msg": "",
            }

            url = ""
            full = False
            refresh = False
            
            try:
                # Parse the url into queries
                query = {}
                parsed_path = urlparse(self.path)
                index = self.path.index('?') + 1
                query_parse = parse_qsl(self.path[index:], keep_blank_values=True)
                for x in query_parse:
                    query[x[0]] = x[1]
                print(query)

                # Only process if secret matches query
                if len(secret) == 0 or ("secret" in query.keys() and secret == query["secret"]):
                    # Process queries
                    if "full" in query.keys():
                        full = True
                    if "refresh" in query.keys():
                        refresh = True

                    # validate the url
                    url = unquote( query["url"] )
                    parsed_url = urlparse(url)

                    if validators.url(url) and parsed_url.scheme == "https" :
                        error_msg["url"] = url

                        try:
                            # If image is cached, get from there instead
                            file_name = "screenshot.png"
                            if cache != "no" :
                                file_name = hashlib.sha256(url.encode()).hexdigest() + ".png"
                            save_file = save_dir + "/" + file_name
                            # If image is not cached, cache it (if enabled)
                            if refresh or cache == "no" or not os.path.exists(save_file):
                                print("Taking screenshot...")
                                takeScreenshot(url, save_file, full)
                                print("Saved to: " + save_file)
                            else:
                                print("Using cached: " + save_file)
                            # Start returning image
                            with open(save_file, "rb") as image_file:
                                self.send_response(200)
                                self.send_header('Content-Type', 'image/png')
                                self.end_headers()
                                self.wfile.write(image_file.read())
                                return
                        # Error processing screenshot
                        except:
                            error_msg["msg"] = "Error processing screenshot."
                            self.error_responder(error_msg)
                            return
                    
                    # URL validation failed
                    else:
                        error_msg["msg"] = "URL failed validation."
                        self.error_responder(error_msg)
                        return

                # Secret set but not matched
                else:
                    error_msg["msg"] = "Secret key is set and did not match request"
                    self.error_responder(error_msg)
                    return

            # Error parsing request or url
            except:
                error_msg["msg"] = "Error parsing request."
                self.error_responder(error_msg)
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
