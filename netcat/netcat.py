import socket
import sys
import getopt
import threading
import subprocess
import traceback

# define some global variables
listen = False
command = False
upload = False
execute = ""
target = ""
upload_destination = ""
port = 0

def usage():
    print("BHP Net Tool")
    print()
    print ("Usage: bhpnet.py -t target_host -p port")
    print ("-l --listen - listen on [host]:[port] for ¬ incoming connections")
    print ("-e --execute = file_to_run - execute the given file upon receiving a connection")
    print ("-c --command - initialize a command shell")
    print ("-u --upload=destination - upon receiving connection upload a file and write to [destination]")
    print()
    print()
    print ("Examples: ")
    print ("bhpnet.py -t 192.168.0.1 -p 5555 -l -c")
    print ("bhpnet.py -t 192.168.0.1 -p 5555 -l -u=c:\\target.exe")
    print ("bhpnet.py -t 192.168.0.1 -p 5555 -l -e=\"cat /etc/passwd\"")
    print("echo 'ABCDEFGHI' | ./bhpnet.py -t 192.168.11.12 -p 135")
    sys.exit(0)

def run_command(command):
    print("run_command func")
    command = command.rstrip()
    try:
        output = subprocess.check_output(command, stderr = subprocess.STDOUT, shell = True)
    except:
      output = "failed to execute command!"
      output =  output.encode()

    return output



def client_handler(client_socket):
   
    global upload
    global execute
    global command


    if len(upload_destination):
        file_buffer =  ""
        while True:
            print("==> Reading file_buffer...")
            data = client_socket.recv(1024).decode()

            message = "recieved!"
            client_socket.send(message.encode())
            if len(data) == 1:
                print("==> breaking from reading file buffer")
                break
            else:
                file_buffer += data
        try:
            print("creating files...")
            file_descriptor = open(upload_destination, "wb")
            file_descriptor.write(file_buffer.encode())
            file_descriptor.close()

            success_message = "successfully saved file"
            client_socket.send(success_message.encode())
        except:
            failed_message = "failed to saved file"
            client_socket.send(failed_message.encode())

    if len(execute):
        output = run_command(execute)
        client_socket.send(output.encode())

    if command:
        while True:
            message = "<BHP:#> "
            client_socket.send(message.encode())

            cmd_buffer = ""
            #while "\n" not in cmd_buffer:
            print("TEST WHILE TRUE")
            cmd_buffer = client_socket.recv(1024).decode()

            response = run_command(cmd_buffer)

            client_socket.send(response)



def client_sender(buffer):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect((target, port))
        if len(buffer):
            client.send(buffer.encode())

        while True:
            recv_len = 1
            response = ""
           
            while recv_len:
                    print("test recv_len")
                    data = client.recv(4096)
                    recv_len = len(data)
                    response += data.decode()
                    if recv_len < 4096:
                        break

            print(response),
            buffer = input("")
            buffer += "\n"

            # send it off
            client.send(buffer.encode())
    except Exception:
        traceback.print_exc()
        print("[*] Exeption! Exiting!")
        #tear down connection
        client.close()


def server_loop():
        print("test")
        global target
        if not len(target):
            target = "0.0.0.0"
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((target, port))
        server.listen(5)
        while True:
            client_socket, addr = server.accept()
            client_thread = threading.Thread(target = client_handler, args = (client_socket, ))
            client_thread.start()


def main():
    global listen
    global port
    global execute
    global command
    global upload_destination
    global target

    if not len(sys.argv[1:]):
        usage()
# read the commandline options
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hle:t:p:cu:", ["help","listen","execute","target","port","command","upload"])
    except getopt.GetoptError as err:
        print (str(err))
        usage()


    for o,a in opts:
        if o in ("-h","--help"):
            usage()
            print("test1")
        elif o in ("-l","--listen"):
            listen = True
            print("-l", listen)
        elif o in ("-e", "--execute"):
            execute = a
            print("test2")
        elif o in ("-c", "--commandshell"):
            command = True
            print("test3")
        elif o in ("-u", "--upload"):
            upload_destination = a
            print("-u is: ", a)
        elif o in ("-t", "--target"):
            target = a
            print("-t is:", a)
        elif o in ("-p", "--port"):
            port = int(a)
            print("-p is:", port)
        else:
            assert False,"Unhandled Option"

    if not listen and len(target) and port > 0:
        buffer = sys.stdin.read()
        # send data off
        client_sender(buffer)
        # we are going to listen and potentially
        # upload things, execute commands, and drop a shell back
        # depending on our command line options above
    if listen:
        server_loop()
            
main()



