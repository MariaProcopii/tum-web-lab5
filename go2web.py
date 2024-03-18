#!/bin/python3

import sys
import socket


class HTTPHandler:

    def __init__(self):
        self.port = 80

    def request(self, url):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            host_ip = socket.gethostbyname(url)
        except socket.gaierror:
            print("[ERROR] Could not resolve the host name")
            sys.exit()

        sock.connect((host_ip, self.port))
        sock.send(f"GET / HTTP/1.1\r\nHost:{url}\r\n\r\n".encode("ascii"))
        response = sock.recv(4096)
        sock.close()

        print(response)


def help_message():
    print("go2web -u <URL>         # make an HTTP request to the specified URL and print the response\ngo2web -s <search-term> # make an HTTP request to search the term using your favorite search engine and print top 10 results\ngo2web -h               # show this help")


if __name__ == "__main__":
    http_handler = HTTPHandler() 

    if "-u" in sys.argv:
        http_handler.request(sys.argv[-1])
    elif "-s" in sys.argv:
        print("make a search")
    else:
        help_message()

