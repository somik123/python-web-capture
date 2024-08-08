[![Docker Image Build](https://github.com/somik123/python-web-capture/actions/workflows/main.yaml/badge.svg)](https://github.com/somik123/python-web-capture/actions/workflows/main.yaml)

# python-web-capture
Python script with playwright, all packaged into a docker container with port 8080 open for requests.

### Installation:
Pull and deploy the image on your localhost's port 8080 with:
```
volumes:
  pyweb_capture_data:
    name: pyweb_capture_data

services:
  pyweb-capture:
    restart: always
    container_name: pyweb-capture
    image: somik123/pyweb-capture:latest
    volumes:
      - pyweb_capture_data:/app/data
    environment:
      PYCAPTURE_SECRET: 1da12b5f29460177dcffbb3dd
      PYCAPTURE_CACHE: yes
      PYCAPTURE_DATA: /app/data
    ports:
      - 8080:8080
```

### Usage:
Replace `10.0.0.10` with the IP address or host of your machine.

Query parameters:
```
secret  - Required to provide if you set it in the env variable for the container.
url     - The url to the website you want to screenshot
full    - Set it if you want to capture the full page screeenshot
refresh - Set it if you want to refresh this specific screenshot
```

Capture full screen screenshot of a website: 
```
http://10.0.0.10:8080/?secret=1da12b5f29460177dcffbb3dd&full&url=https://github.com/somik123/python-web-capture
```


Capture simple screenshot of a website: 
```
http://10.0.0.10:8080/?secret=1da12b5f29460177dcffbb3dd&url=https://github.com/somik123/python-web-capture
```

Refresh screenshot of a website (instead of loading it from cache again):
```
http://10.0.0.10:8080/?secret=1da12b5f29460177dcffbb3dd&refresh&url=https://github.com/somik123/python-web-capture
```