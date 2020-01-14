# SSL certificate
## Issue certificate
To enable https instead of http for API endpoint, SSL certificate is required.
On OSX (Mojave),  install openssl by

```
$ brew install openssl
$ mkdir ssl_files
$ cd ssl_files
$ mkdir demoCA
$ touch demoCA/index.txt
$ echo 00 > demoCA/serial
```

Then, issue the certificates (`./ssl_files/ca.crt`) and key (`./ssl_files/ca.key`)

```
$ openssl genrsa -out ./ca.key 2048
$ openssl req -new -key ca.key -out ca.csr -subj '/C=JP/ST=Tokyo/L=Shibuya-ku/O=Oreore CA inc./OU=Oreore Gr./CN=Oreore CA'
$ openssl x509 -days 3650 -in ./ca.csr -req -signkey ./ca.key -out ca.crt
```

## Work on flask to enable https

```
$ brew update
$ brew install openssl
$ brew reinstall openssl

$ brew tap vapor/tap
$ brew install vapor/tap/vapor

$ sudo install_name_tool -change /usr/local/opt/openssl/lib/libssl.1.0.0.dylib /usr/local/opt/openssl/lib/libssl.1.1.dylib $(which vapor)
$ sudo install_name_tool -change /usr/local/opt/openssl/lib/libcrypto.1.0.0.dylib /usr/local/opt/openssl/lib/libssl.1.1.dylib $(which vapor)
```

## Add Dockerfile
In [docker-composer](./docker-compose.yml), you have to add

```
SSL_CERTIFICATETE_DIR: "ssl_files"
```

as `args`, and following lines to [Dockerfile](./Dockerfile)

```
ARG SSL_CERTIFICATETE_DIR

COPY ${SSL_CERTIFICATETE_DIR}/ca.crt /tmp
COPY ${SSL_CERTIFICATETE_DIR}/ca.key /tmp

ENV SSL_CERTIFICATE=/tmp/ca.crt \
    SSL_KEY=/tmp/ca.key

```

## Reference
- [issue free SSL from macOS](http://rikuga.me/2017/12/24/oreore-ca-and-ssl-cert/)
- [flask SSL setup](https://qiita.com/taka_katsu411/items/fb1ad876c0017b9fe49d)
- [openssl issue on macOS](https://stackoverflow.com/a/59007349)