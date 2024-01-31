"""
 HTTP Server
 Author: Eitan Shoshan
 Description: the derver is getting requests from the browser and servse it
 Date: 7/1/2024
"""
import socket
import os
import logging

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
LOG_FORMAT = '%(levelname)s | %(asctime)s | %(message)s'
LOG_LEVEL = logging.DEBUG
LOG_DIR = 'log'
LOG_FILE = LOG_DIR + '/server.log'


def get_file_data(file_name):
    """
    Get data from file
    :param file_name: the name of the file
    :return: data from file in a string
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
        response_body_length = 0
        return None


def can_convert_to_int(s):
    """
    checks if a string can be converted to an int
    :param s:
    :return: true or false
    """
    try:
        # Attempt to convert the string or character to an integer
        int(s)
        return True  # Conversion successful
    except ValueError:
        # Conversion failed
        return False


def get_extension_from_url(url):
    """
    gets the file extension from the url request
    :param url:
    :return: file extension e.g. html
    """
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


def handle_client_get_request(resource, client_socket):
    """
    Check the required resource, generate proper HTTP response and send
    to client
    :param resource: the required resource
    :param client_socket: a socket for the communication with the client
    :return: None
    """
    """ """
    global validate_header_flag, response_content_type, response_status_code, request_protocol_version, status_code_flag
    http_response = ""
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
    is_calc_next = False
    number = 0
    if resource[:15] == "/calculate-next":
        is_calc_next = True
        if resource[15:20] == "?num=":
            if can_convert_to_int(resource[20:]):
                number = int(resource[20:]) + 1
            else:
                is_calc_next = False
        else:
            is_calc_next = False
        if not is_calc_next:
            http_response = (request_protocol_version + chr(32) + "400 BAD REQUEST" + chr(13) + chr(10)
                             + chr(13) + chr(10)).encode()
        else:
            http_response = (request_protocol_version + chr(32) + response_status_code + chr(13) + chr(10) +
                               "Content-Type: string" + chr(13) + chr(10) + "Content-Length: " +
                               str(len(str(number))) + chr(13) + chr(10) + chr(13) + chr(10) + str(number)).encode()
    elif resource[:16] == "/calculate-area?":
        if '&' in resource:
            height_and_width = resource[16:].split('&')
            if (height_and_width[0])[:6] == "height":
                height = (height_and_width[0])[7:]
                width = (height_and_width[1])[6:]
            else:
                height = (height_and_width[1])[7:]
                width = (height_and_width[0])[6:]
            if (can_convert_to_int(height)) and (can_convert_to_int(width)):
                area = int(height) * int(width) / 2
                http_response = (request_protocol_version + chr(32) + response_status_code + chr(13) + chr(10) +
                                 "Content-Type: string" + chr(13) + chr(10) + "Content-Length: " +
                                 str(len(str(area))) + chr(13) + chr(10) + chr(13) + chr(10) + str(area)).encode()
            else:
                http_response = (request_protocol_version + chr(32) + "400 BAD REQUEST" + chr(13) + chr(10)
                                 + chr(13) + chr(10)).encode()
        else:
            http_response = (request_protocol_version + chr(32) + "400 BAD REQUEST" + chr(13) + chr(10)
                             + chr(13) + chr(10)).encode()
    elif resource[:7] == "/image?":
        image_name = resource[18:]
        file_data = get_file_data("/uploads/" + image_name)
        if response_status_code == "200 OK":
            content_type = get_extension_from_url(image_name)
            content_type = content_types_dict[content_type]
            http_response = (request_protocol_version + chr(32) + response_status_code + chr(13) + chr(10) +
                           "Content-Type: " + content_type + chr(13) + chr(10) +
                             "Content-Length: " + str(len(file_data)) + chr(13) + chr(10) + chr(13) + chr(10))
            http_response = http_response.encode() + file_data
        else:
            http_response = ((request_protocol_version + chr(32) + response_status_code + chr(13) + chr(10)
                           + chr(13) + chr(10))).encode()
    else:
        file_ext = get_extension_from_url(resource)
        if file_ext is not None:
            response_content_type = content_types_dict[file_ext]
        data = None
        if status_code_flag:
            data = get_file_data(resource)

        if response_status_code == "200 OK":
            http_header = (request_protocol_version + chr(32) + response_status_code + chr(13) + chr(10) +
                           "Content-Type: " + response_content_type + chr(13) + chr(10) + "Content-Length: " +
                           str(response_body_length) + chr(13) + chr(10) + chr(13) + chr(10))
        elif response_status_code == "302 MOVED TEMPORARILY":
            http_header = (request_protocol_version + chr(32) + response_status_code + chr(13) + chr(10) +
                         "Location: /" + chr(13) + chr(10) + chr(13) + chr(10))
        else:
            http_header = (request_protocol_version + chr(32) + response_status_code + chr(13) + chr(10)
                           + chr(13) + chr(10))
        if data is None:
            http_response = http_header.encode()
        else:
            http_response = http_header.encode() + data
    client_socket.send(http_response)
    logging.debug("A Response Was Sent Back To The Client.")


def read_until_delimiter(text, start_index, delimiter):
    """
    reads from a string beginning from a start index untill a delimiter
    :param text:
    :param start_index:
    :param delimiter:
    :return:
    """
    # Find the index of the delimiter starting from 'start_index'
    delimiter_index = text.find(delimiter, start_index)

    # If the delimiter is found, slice the string up to the delimiter
    if delimiter_index != -1:
        return text[start_index:delimiter_index]
    else:
        # If delimiter is not found, return the substring from 'start_index' to the end
        # Alternatively, you can return None or raise an error, depending on your needs
        return text[start_index:]


def save_data_to_file(data, extension, filename):
    """
    Saves byte data to a file with the given extension in a predefined directory.
    Handles both text and binary data based on the extension.

    Args:
    - data: The data to be saved in bytes.
    - extension: The file extension (e.g., 'txt', 'jpg'). Determines how the data is processed.
    - filename: The name of the file without the extension.

    Returns:
    - True if the file was successfully saved, False otherwise.
    """
    # Constant directory path where files will be saved
    directory = "C:/work/cyber/Ex-4/webroot/uploads"

    try:
        # Ensure the directory exists, create it if it doesn't
        if not os.path.exists(directory):
            os.makedirs(directory)

        file_path = os.path.join(directory, f"{filename}")

        # Determine the mode based on the file type
        mode = 'wb' if extension in ['jpg', 'ico', 'gif', 'png'] else 'w'

        with open(file_path, mode) as file:
            if mode == 'wb':
                file.write(data)  # Write binary data directly
            else:
                file.write(data.decode('utf-8'))  # Decode bytes to string for text files

    except Exception as e:
        print(f"An error occurred while saving the file: {e}")
        return False

    return True


def determine_file_extension(file_data):
    """
    Determines the file extension based on the given file data in bytes.
    This function uses simple heuristics and is not completely reliable, especially for text-based formats.

    Args:
    - file_data: The data of the file in bytes.

    Returns:
    - A string representing the file extension, or None if the extension cannot be determined.
    """
    signatures = {
        b'\xFF\xD8\xFF': 'jpg',
        b'\x89PNG\r\n\x1A\n': 'png',
        b'GIF87a': 'gif',
        b'GIF89a': 'gif',
        b'\x00\x00\x01\x00': 'ico',  # Common ICO files start with this
        # Add more signatures as needed
    }

    # Check binary signatures first
    for signature, extension in signatures.items():
        if file_data.startswith(signature):
            return extension

    # Attempt to identify text-based formats with very basic and unreliable checks
    try:
        text_content = file_data.decode('utf-8', errors='ignore').lower()
        if text_content.startswith(('<!doctype html', '<html')):
            return 'html'
        elif '{' in text_content and '}' in text_content:  # Very unreliable check for CSS
            return 'css'
        elif 'function' in text_content or 'const' in text_content or 'let' in text_content:  # Unreliable check for JS
            return 'js'
        # Plain text files have no signature; might return txt for any undetermined text-based format
        return 'txt'
    except UnicodeDecodeError:
        pass

    return None


def handle_client_post_request(resource, request_headers, client_socket):
    """
    handles the post requests
    :param resource:
    :param request_headers:
    :param client_socket:
    :return:
    """
    global response_status_code
    file_name = resource[18:]
    post_flag = True
    if "Content-Length" not in request_headers:
        post_flag = False
    elif "Content-Type" not in request_headers:
        post_flag = False
    if post_flag:
        content_length_index = request_headers.index("Content-Length")
        content_length = int(read_until_delimiter(request_headers, content_length_index + 16, chr(13)))
        file_data = client_socket.recv(content_length)
        while int(len(file_data)) != content_length:
            file_data = file_data + client_socket.recv(content_length - int(len(file_data)))
        file_content_type = get_extension_from_url(file_name)
        post_flag = save_data_to_file(file_data, file_content_type, file_name)
    if post_flag:
        response_status_code = "200 OK"
    else:
        response_status_code = "400 BAD REQUEST"
    post_request_response = (request_protocol_version + chr(32) + response_status_code +
                             chr(13) + chr(10) + chr(13) + chr(10))
    post_request_response = post_request_response.encode()
    client_socket.send(post_request_response)


def validate_http_request():
    """
    Check if request is a valid HTTP request and returns TRUE / FALSE and
    the requested URL
    :return: a tuple of (True/False - depending on if the request is valid,
    the requested resource )
    """
    global validate_header_flag
    if validate_header_flag:
        if request_type != "GET" and request_type != "POST":
            validate_header_flag = False
        if request_protocol_version != "HTTP/1.1":
            validate_header_flag = False
    return validate_header_flag, request_uri


def read_from_socket(client_socket, delimiter):
    """
    Parse the request
    :param client_socket:
    :param delimiter:
    :return: the content from the request untill the delimiter
    """
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


def handle_request_headers(client_socket):
    """
    reading from socket the headers
    :param client_socket:
    :return:
    """
    while_flag = True
    client_request_headers = ""
    recieved_char = ''
    while while_flag:
        recieved_char = client_socket.recv(1).decode()
        client_request_headers = client_request_headers + recieved_char
        if recieved_char == chr(13):
            recieved_char = client_socket.recv(1).decode()
            client_request_headers = client_request_headers + recieved_char
            if recieved_char == chr(10):
                recieved_char = client_socket.recv(1).decode()
                client_request_headers = client_request_headers + recieved_char
                if recieved_char == chr(13):
                    recieved_char = client_socket.recv(1).decode()
                    client_request_headers = client_request_headers + recieved_char
                    if recieved_char == chr(10):
                        while_flag = False
    return client_request_headers


def handle_client(client_socket):
    """
    Handles client requests: verifies client's requests are legal HTTP, calls
    function to handle the requests
    :param client_socket: the socket for the communication with the client
    :return: None
    """
    global request_type, request_uri, request_protocol_version, response_status_code, \
        response_body_length, status_code_flag
    status_code_flag = True
    print('Client connected')
    logging.debug("processing handle client func")

    request_type = read_from_socket(client_socket, " ")
    request_uri = read_from_socket(client_socket, " ")
    request_protocol_version = read_from_socket(client_socket, chr(13))
    logging.debug("Request Type: " + request_type)
    logging.debug("Request URI: " + request_uri)
    logging.debug("Request Protocol Version: " + request_protocol_version)

    request_headers = handle_request_headers(client_socket)
    logging.debug("Request Headers: " + request_headers)

    valid_http, resource = validate_http_request()
    logging.debug("Is The Request Valid: " + str(valid_http))
    if valid_http:
        print('Got a valid HTTP request')
        response_status_code = "200 OK"
        if request_type == "GET":
            handle_client_get_request(resource, client_socket)
        if request_type == "POST":
            handle_client_post_request(resource, request_headers, client_socket)
    else:
        print('Error: Not a valid HTTP request')
    print('Closing connection')


def main():
    """
    Runs the server
    :return: None
    """
    global status_code_flag
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server_socket.bind((IP, PORT))
        server_socket.listen(QUEUE_SIZE)
        print("Listening for connections on port %d" % PORT)

        while True:
            logging.debug("ready for client request")
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
    if not os.path.isdir(LOG_DIR):
        os.makedirs(LOG_DIR)
    logging.basicConfig(format=LOG_FORMAT, filename=LOG_FILE, level=LOG_LEVEL)
    assert get_extension_from_url("file.js") == "js"
    assert (get_file_data("/assert_test.txt")).decode() == "eitan"
    assert (can_convert_to_int("12") == True)
    assert (can_convert_to_int("fg") == False)
    main()
