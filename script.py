from playwright.sync_api import sync_playwright
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, unquote, parse_qsl
import json, argparse, subprocess, validators, os, hashlib, time

# get env vars
username = os.environ.get("PYCAPTURE_USER", "")
password = os.environ.get("PYCAPTURE_PASS", "")
secret = os.environ.get("PYCAPTURE_SECRET", "")
save_dir = os.environ.get("PYCAPTURE_DATA", "/tmp")
cache = os.environ.get("PYCAPTURE_CACHE", "no")


# Use playwright to capture a screenshot of the page
def takeScreenshot(url: str, save_file: str, width: int, height: int, full: bool, delay: int):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.set_viewport_size({"width": width, "height": height})
        page.goto(url)
        if delay > 0:
            print("Sleeping for {}s".format(delay))
            time.sleep(delay)
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
        if self.path == '/':
            if len(username) != 0 or len(password) != 0:
                output_html = home_page_html.format(user_pass_prompt_html)
            elif len(secret) != 0:
                output_html = home_page_html.format(secret_prompt_html)
            else:
                output_html = home_page_html.format("")
            
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(output_html.encode('utf-8'))
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
            width = 1280
            height = 960
            delay = 0
            
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
                secret_valid = "secret" in query.keys() and secret == query["secret"]
                user_valid = "user" in query.keys() and username == query["user"]
                pass_valid = "pass" in query.keys() and password == query["pass"]
                auth_disabled = len(secret) == 0 and len(username) == 0 and len(password) == 0

                if auth_disabled or secret_valid or (user_valid and pass_valid):
                    # Process queries
                    if "full" in query.keys():
                        full = True
                    if "refresh" in query.keys():
                        refresh = True
                    if "width" in query.keys():
                        tmp_width = int(query["width"])
                        if tmp_width > 100 and tmp_width < 4096:
                            width = tmp_width
                    if "height" in query.keys():
                        tmp_height = int(query["height"])
                        if tmp_height > 100 and tmp_height < 4096:
                            height = tmp_height
                    if "delay" in query.keys():
                        tmp_delay = int(query["delay"])
                        if tmp_delay > 0 and tmp_delay < 10:
                            delay = tmp_delay

                    # validate the url
                    url = unquote( query["url"] )
                    parsed_url = urlparse(url)

                    if validators.url(url) and parsed_url.scheme == "https" :
                        error_msg["url"] = url

                        try:
                            # If image is cached, get from there instead
                            file_name = "screenshot.png"
                            if cache != "no" :
                                screenshot_params = "{} {} {} {} {}".format(width, height, full, delay, url)
                                file_name = hashlib.sha256(screenshot_params.encode()).hexdigest() + ".png"
                            file_path = save_dir + "/" + file_name
                            # If image is not cached, cache it (if enabled)
                            if refresh or cache == "no" or not os.path.exists(file_path):
                                print("Taking screenshot...")
                                takeScreenshot(url, file_path, width, height, full, delay)
                                print("Saved to: " + file_path)
                            else:
                                print("Using cached: " + file_path)
                            # Start returning image
                            with open(file_path, "rb") as image_file:
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
                    error_msg["msg"] = "Secret key or username/password is set and did not match"
                    self.error_responder(error_msg)
                    return

            # Error parsing request or url
            except:
                error_msg["msg"] = "Error parsing request."
                self.error_responder(error_msg)
                return

secret_prompt_html = """
                <div class="input-group mb-3">
                    <span class="input-group-text">Secret:</span>
                    <input class="form-control form-control-lg" type="text" name="secret" value="" />
                </div>
"""
user_pass_prompt_html = """
                <div class="input-group mb-3">
                    <span class="input-group-text">Username:</span>
                    <input class="form-control form-control-lg" type="text" name="user" value="" />
                    <span class="input-group-text">Password:</span>
                    <input class="form-control form-control-lg" type="text" name="pass" value="" />
                </div>
"""

home_page_html = """
<!DOCTYPE html>
<html>

<head>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet"
        integrity="sha384-QWTKZyjpPEjISv5WaRU9OFeRpok6YctnYmDr5pNlyT2bRjXh0JMhjY6hW+ALEwIH" crossorigin="anonymous">
</head>

<body>
    <form action="/">
        <div style="width: 700px; margin: 0 auto;">
            <div class="m-5">

                <div class="input-group mb-3">
                    <span class="input-group-text">URL:</span>
                    <input class="form-control form-control-lg" type="text" name="url" value="" />
                </div>
{}
                <div class="input-group mb-3">
                    <span class="input-group-text">Width:</span>
                    <input class="form-control form-control-lg" type="text" name="width" value="1280" />
                    <span class="input-group-text">Height:</span>
                    <input class="form-control form-control-lg" type="text" name="height" value="960" />
                </div>
                
                <div class="input-group mb-3">
                    <span class="input-group-text">Full page:</span>
                    <div class="input-group-text">
                        <input class="form-check-input" type="checkbox" name="full" value="1">
                    </div>
                    <span class="input-group-text">Refresh:</span>
                    <div class="input-group-text">
                        <input class="form-check-input" type="checkbox" name="refresh" value="1">
                    </div>
                    <span class="input-group-text">Delay:</span>
                    <select class="form-select" name="delay">
                        <option>0</option>
                        <option>1</option>
                        <option>2</option>
                        <option>3</option>
                        <option>4</option>
                        <option>5</option>
                        <option>6</option>
                        <option>7</option>
                        <option>8</option>
                        <option>9</option>
                        <option>10</option>
                    </select>
                    <input class="form-control form-control-lg btn btn-outline-primary" type="submit" value="Screenshot" />
                </div>

            </div>
        </div>
    </form>
</body>

</html>
"""

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
