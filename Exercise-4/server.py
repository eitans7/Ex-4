"""
 HTTP Server
 Author: Eitan Shoshan
"""
import socket
import os

QUEUE_SIZE = 10
IP = '0.0.0.0'
PORT = 80
SOCKET_TIMEOUT = 2
WEB_ROOT = "C:/work/cyber/Ex-4/webroot"
DEFAULT_URI = WEB_ROOT + "/index.html"
REDIRECTION_DICTIONARY = {"/moved": "/index.html"}
request_type = ""
request_uri = ""
request_protocol_version = ""
validate_header_flag = True
content_types_dict = {
    "html": "text/html; charset=utf-8",
    "jpg": "image/jpeg",
    "css": "text/css",
    "js": "text/javascript; charset=UTF-8",
    "txt": "text/plain",
    "ico": "image/x-icon",
    "gif": "image/gif",
    "png": "image/png"
}
response_content_type = ""
response_body_length = 0
response_status_code = "200 OK"
status_code_flag = True


def get_file_data(file_name):
    """
    Get data from file
    :param file_name: the name of the file
    :return: file data in a string
    """
    file_path = WEB_ROOT + file_name
    global response_body_length, response_status_code
    if os.path.exists(file_path):
        with open(file_path, 'rb') as file:
            content = file.read()
            response_body_length = len(content)
            return content
    else:
        response_status_code = "404 NOT FOUND"
        return None


def get_extension_from_url(url):
    last_slash_index = url.rfind('/')
    if last_slash_index != -1:
        # Extract the part of the URL after the last slash
        file_name_and_params = url[last_slash_index + 1:]
    else:
        file_name_and_params = url

    # Find the last dot instead of the first dot
    dot_index = file_name_and_params.rfind('.')
    if dot_index != -1:
        # Extract the extension, omitting the dot
        ext = file_name_and_params[dot_index + 1:]
        query_param_index = ext.find('?')
        if query_param_index != -1:
            ext = ext[:query_param_index]
        return ext
    else:
        return None


def handle_client_request(resource, client_socket):
    """
    Check the required resource, generate proper HTTP response and send
    to client
    :param resource: the required resource
    :param client_socket: a socket for the communication with the client
    :return: None
    """
    """ """
    global validate_header_flag, response_content_type, response_status_code, request_protocol_version, status_code_flag
    if (resource == '') or (resource == "/"):
        resource = "/index.html"
    uri = WEB_ROOT + resource

    if not validate_header_flag:
        response_status_code = "400 BAD REQUEST"
        status_code_flag = False
    if resource in REDIRECTION_DICTIONARY:
        response_status_code = '302 MOVED TEMPORARILY'
        status_code_flag = False
    if 'forbidden' in uri.lower():
        response_status_code = "403 FORBIDDEN"
        status_code_flag = False
    if 'error' in uri.lower():
        response_status_code = "500 ERROR SERVER INTERNAL"
        status_code_flag = False

    file_ext = get_extension_from_url(resource)
    if file_ext != None:
        response_content_type = content_types_dict[file_ext]
    data = None
    if status_code_flag:
        data = get_file_data(resource)

    if response_status_code != "302 MOVED TEMPORARILY":
        http_header = (request_protocol_version + chr(32) + response_status_code + chr(13) + chr(10) +
                       response_content_type + chr(13) + chr(10) +
                       str(response_body_length) + chr(13) + chr(10) + chr(13) + chr(10))
    else:
        http_header = (request_protocol_version + chr(32) + response_status_code + chr(13) + chr(10) +
                        "Location: /index.html" + chr(13) + chr(10) +
                       str(response_body_length) + chr(13) + chr(10) + chr(13) + chr(10))
    if data != None:
        http_response = http_header.encode() + data
    else:
        http_response = http_header.encode()
    client_socket.send(http_response)


def validate_http_request():
    """
    Check if request is a valid HTTP request and returns TRUE / FALSE and
    the requested URL
    :return: a tuple of (True/False - depending if the request is valid,
    the requested resource )
    """
    global validate_header_flag
    if validate_header_flag == True:
        if request_type != "GET":
            validate_header_flag = False
        if request_protocol_version != "HTTP/1.1":
            validate_header_flag = False
    return validate_header_flag, request_uri

def read_from_socket(client_socket, delimiter):
    content = ""
    global validate_header_flag
    recieved_char = client_socket.recv(1).decode()
    while recieved_char != delimiter:
        content = content + recieved_char
        recieved_char = client_socket.recv(1).decode()
    if delimiter == chr(13):
        recieved_char = client_socket.recv(1).decode()
        if recieved_char != chr(10):
            validate_header_flag = False

    return content

def consume_request(client_socket):
    request_data = b''
    delimiter = b'\r\n\r\n'
    delimiter_length = len(delimiter)
    read_buffer = b''

    while True:
        # Read one byte at a time
        part = client_socket.recv(1)
        request_data += part
        read_buffer += part

        # Keep only the last few characters that are needed to match the delimiter
        if len(read_buffer) > delimiter_length:
            read_buffer = read_buffer[-delimiter_length:]

        # Check if the delimiter is in the read buffer
        if read_buffer == delimiter:
            break

        if not part:
            break


def handle_client(client_socket):
    """
    Handles client requests: verifies client's requests are legal HTTP, calls
    function to handle the requests
    :param client_socket: the socket for the communication with the client
    :return: None
    """
    global request_type, request_uri, request_protocol_version, response_status_code, response_body_length
    print('Client connected')
    while True:
        response_status_code = "200 OK"
        response_body_length = 0
        request_type = read_from_socket(client_socket, " ")
        request_uri = read_from_socket(client_socket, " ")
        request_protocol_version = read_from_socket(client_socket, chr(13))
        #consume_request(client_socket)
        trash = client_socket.recv(5000)

        valid_http, resource = validate_http_request()
        if valid_http:
            print('Got a valid HTTP request')
            handle_client_request(resource, client_socket)
        else:
            print('Error: Not a valid HTTP request')
            break
    print('Closing connection')




def main():
    # Open a socket and loop forever while waiting for clients
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server_socket.bind((IP, PORT))
        server_socket.listen(QUEUE_SIZE)
        print("Listening for connections on port %d" % PORT)

        while True:
            client_socket, client_address = server_socket.accept()
            try:
                print('New connection received')
                client_socket.settimeout(SOCKET_TIMEOUT)
                handle_client(client_socket)
            except socket.error as err:
                print('received socket exception - ' + str(err))
            finally:
                client_socket.close()
    except socket.error as err:
        print('received socket exception - ' + str(err))
    finally:
        server_socket.close()


if __name__ == "__main__":
    main()
