# python-web-capture
Python script with playwright, all packaged into a docker container with port 8080 open for requests.

### Installation:
Pull and deploy the image on your localhost's port 8080 with:
```
docker run --name pyweb-capture -p 8080:8080 -d somik123/pyweb-capture:latest
```

### Usage:
Replace `10.0.0.10` with the IP address or host of your machine.

Capture full screen screenshot of a website: 
```
http://10.0.0.10:8080/?full&url=https://github.com/somik123/python-web-capture
```


Capture simple screenshot of a website: 
```
http://10.0.0.10:8080/?url=https://github.com/somik123/python-web-capture
```
