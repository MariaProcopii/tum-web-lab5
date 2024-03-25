#!/usr/bin/env python

import re
import ssl
import sys
import socket
import subprocess 

from urllib.parse import urlparse
from bs4 import BeautifulSoup
from lxml import etree

HTTP_PORT = 80
HTTPS_PORT = 443

class Parser:

    def parse_url(self, url):
        parsed_url = urlparse(url)

        scheme = parsed_url.scheme
        host = parsed_url.netloc
        path = parsed_url.path

        return [scheme, host, path]

    def parse_html_page(self, data):
        return subprocess.run(
            ["lynx", "-stdin", "-dump"],
            input=data,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
        ).stdout
    
    def parse_html_links(self, data):
        soup = BeautifulSoup(data, "html.parser")
        dom = etree.HTML(str(soup))

        links = dom.xpath("//span/a//following-sibling::h3/../@href")
        return links


class HTTPHandler:

    def __init__(self):
        self.search_link = "https://www.google.com/search?q={}"
        self.search_path = "/search?q={}"
        self.parser = Parser()
    
    def request(self, host, port, path):
        response = "" 
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))

        if port == HTTPS_PORT:
            ctx = ssl.create_default_context()
            sock = ctx.wrap_socket(sock, server_hostname=host)
        
        sock.sendall(
            (f"GET {path} HTTP/1.1\r\n" +
             f"Host: {host}\r\n" +
             "Connection: close\r\n" +
             "User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:123.0) Gecko/20100101 Firefox/123.0\r\n" +
             "Accept: */*\r\n" +
             "\r\n").encode()
        )

        while True:
            data = sock.recv(4096)
            if not data: break
            response += data.decode("utf-8")
        
        sock.close()

        headers, body = response.split("\r\n\r\n", 1)

        if re.match(r"HTTP/1.1 3\d{2}", headers) and "Location:" in headers:
            location = re.search(r"Location: (.+)\r\n", headers).group(1)
            scheme, host, port = self.parser.parse_url(location)
            if scheme == "http":
                port = HTTP_PORT
            else:
                port = HTTPS_PORT
            
            return self.request(host, port, path)
        
        return [headers, body]
    
    def search(self, queries):
        search_query = '+'.join(queries)

        port = HTTPS_PORT
        path = self.search_path.format(search_query)
        host= urlparse(
            self.search_link.format(search_query)
        ).netloc

        _, body = self.request(host, port, path)
        return self.parser.parse_html_links(body)

if __name__=="__main__":
    http_handler = HTTPHandler()

    if "-u" in sys.argv:
        scheme, host, path = http_handler.parser.parse_url(sys.argv[-1])
        if scheme == "http":
            port = HTTP_PORT
        else:
            port = HTTPS_PORT
        
        header, body = http_handler.request(host, port, path)
        print(http_handler.parser.parse_html_page(body))

    elif "-s" in sys.argv:
        links = http_handler.search(sys.argv[2:])
        for idx, link in enumerate(links, 1):
            print(f"{idx}. {link}")
        
        option = input("Select the number of the link you want to access or enter `q` to quit\nOption >> ")
        if option == "q":
            sys.exit()
        elif 1 <= int(option) <= len(links):
            scheme, host, path = http_handler.parser.parse_url(links[int(option)])
            if scheme == "http":
                port = HTTP_PORT
            else:
                port = HTTPS_PORT
            
            header, body = http_handler.request(host, port, path)
            print(http_handler.parser.parse_html_page(body))
        else:
            print("Wrong option")
            sys.exit()

    else:
        print("""
    go2web -u <URL>         >> make an HTTP request to URL and print the response\n 
    go2web -s <search-term> >> make an HTTP request to search and print top 10 results\n 
    go2web -h               >> show help
    """)
