import socket
import os

print("Welcome to your File Transfer Service")

#function for debug displayed or not
debug_flag = True

def print_debug(line, debug_info=False):
    # If not debug_info= don't check flag
    # If debug_info = check flag.
    if not debug_info or debug_flag:
        print(f"ftp_client> {line}")

#function to procecss the response from server
def convertServerResponse(response):
    res_byte = response[0]
    res_byte = format(res_byte, '08b')
    res_code = res_byte[:3]
    print_debug(f"Response code received: {res_code}.")
    return res_code, int(res_byte[3:], 2)



# Function to get IP Address and Port number
def get_ip_and_port():
    while True:
        try:
            ip_address, port_number, debug_flag  = input("Provide IP address and Port number and debug_flag : ").split()

            return ip_address, int(port_number), int(debug_flag)
        except ValueError:
            print_debug("Invalid Input, please provide IP, Port and debug flag deperated by a space")
        except Exception as e:
            print_debug(f"An error occurred: {e}")


def tcp_connection(ip_address, port_number):
    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        clientSocket.connect((ip_address, port_number))
        print_debug("Session has been established")
        print_debug(f"IP Address: {ip_address}")
        print_debug(f"Port Number: {port_number}")
        print_debug("Enter help to view the available commands")

        while True:
            #connection established; get user input command
            client_command = input("myftp> ")
            #since user will input ex: get file.txt; need to sleep to get the command neccesary
            command = client_command.split(" ")
            # first part will process the command
            executed_command = command[0]

            #verify the commands
            #put command
            #format put filename
            if executed_command == "put":
                opcode = "000"
                #other part of string is the file name
                filename = command[1]
                try:
                    #size of the file in byte
                    file_size = os.path.getsize(f"client/{filename}")

                except:
                    #if file dont exist
                    print_debug("file does not exist")
                    continue


                #length of file name
                filename_length =len(filename)

                # convert the file name length in 32 bit
                filename_length_32bit = bin(filename_length)[2:].zfill(32)

                filename_length_5bits = filename_length_32bit[:5]

                #convert the file size in 4 bytes
                file_size_4bytes = file_size.to_bytes(4, 'little')

                #since 4 byte represents the file; that maximum file size allowed is 2^32 bytes

                #verify that the file is within the limit
                if(file_size < 2**32):
                    #verify that name length does not exceed 31 characters
                    if(filename_length <32):
                        #construct the request
                        filename_length_5bits = format(filename_length, '05b')
                        first_byte = int(opcode + filename_length_5bits, 2).to_bytes(1, 'little')
                        file_size_4bytes = file_size.to_bytes(4, 'little')

                        client_request = first_byte + filename.encode() + file_size_4bytes

                        #write in the file
                        with open(f"client/{filename}", "rb") as f:
                            client_request += f.read()

                        #send the client request to the TCP server to process
                        clientSocket.send(client_request)

                        #receive respononse from server
                        server_response =clientSocket.recv(8000000)


                        #only res_code needed from the server for the put command
                        res_code, _ = convertServerResponse(server_response)

                        #read the response
                        if(res_code == "000"):
                            print_debug("File transfer successfully completed!")
                        else:
                            print_debug("File transfer failed")
                    else:
                        print_debug("Length of file name is too large")

                else:
                    print_debug("Size of the file is too large")

            #get command (retrieve file)
            #format: get filename
            elif(executed_command == "get"):
                opcode = "001"
                filename = command[1]
                filename_length = len(filename)

                #make sure file lengh does not exceed 31 chaters including end
                if filename_length < 32:
                    client_request = int(opcode+ format(filename_length, '05b'),2).to_bytes(1, 'little') + filename.encode()

                    # send the client request to the TCP server to process
                    clientSocket.send(client_request)

                    # receive response from server
                    server_response = clientSocket.recv(8000000)

                    #read the response
                    res_code, filename_length = convertServerResponse(server_response)

                    if res_code == "001":
                        file_name = server_response[1:filename_length + 1].decode()
                        file_size = int.from_bytes(server_response[filename_length + 1:filename_length + 5],
                                                   'little')
                        file_data = server_response[filename_length + 5:filename_length + 5 + file_size]
                        with open(f"client/{file_name}", "wb") as f:
                            f.write(file_data)
                        print_debug("File downloaded successfully.")

                    elif res_code == "010":
                        print_debug("File not found.")
                else:
                    print_debug("Length of file name is too large")


            #change command (change old file name to new file name)
            #Format: change oldFilename newFilename
            elif executed_command == "change":
                try:
                    assert (len(command) == 3)
                except:
                    print_debug("Please input the function correctly following this format -> change oldFilename newFilename")
                old_file_name = command[1]
                new_file_name = command[2]
                opcode = "010"
                old_file_name_length = len(old_file_name)
                new_file_name_length = len(new_file_name)
                if old_file_name_length > 31 or new_file_name_length > 31:
                    print_debug("Old or new file name is too large.")
                else:
                    client_request = int(opcode + format(old_file_name_length, '05b'), 2).to_bytes(1, 'little')
                    client_request += old_file_name.encode()
                    client_request += int(format(new_file_name_length, '05b'), 2).to_bytes(1, 'little')
                    client_request += new_file_name.encode()

                    # send the client request to the TCP server to process
                    clientSocket.send(client_request)

                    # receive response from server
                    server_response = clientSocket.recv(8000000)

                    # read the response
                    res_code, _ = convertServerResponse(server_response)

                    if res_code == "000":
                        print_debug(
                        f"Old file name:{old_file_name} has been changed to new file name entered:{new_file_name}")
                    elif res_code == "101":
                        print_debug("Unsuccessful file name change.")


            elif executed_command == "summary":
                opcode = "011"
                filename = command[1]
                filename_length = len(filename)

                # verify that file name does not exceed from the character
                if filename_length < 32:
                    client_request = int(opcode + format(filename_length, '05b'), 2).to_bytes(1,
                                                                                              'little') + filename.encode()

                    # send the client request to the TCP server to process
                    clientSocket.send(client_request)

                    # receive response from server
                    server_response = clientSocket.recv(8000000)

                    # read the response
                    res_code,filename_length = convertServerResponse(server_response)

                    if res_code == "010":
                        print_debug(f"statistical summary request received for {filename} refer to server log")



                    elif res_code == "011":
                        print_debug("Error file not found or No Numerical Number in the File")

            #help command
            #format: help
            elif executed_command == "help":
                opcode = "100"
                client_request = int(opcode+format(0,'05b'), 2).to_bytes(1, 'little')

                # send the client request to the TCP server to process
                clientSocket.send(client_request)

                # receive response from server
                server_response = clientSocket.recv(8000000)

                # read the response
                res_code, lengh_help = convertServerResponse(server_response)

                if res_code == "110":
                    help_message = server_response[1:1 + lengh_help].decode()
                    print_debug(f"{help_message}")

            elif executed_command == "bye":
                print_debug("Closing client connection")
                clientSocket.close()
                break

            #if executed_commmand doesnt match with what exists....
            else:
                print_debug("Invalid command, use help for valid commands")



    except socket.error as e:
        print_debug(f"TCP connection failed: {e}")
        print_debug(f"IP Address: {ip_address}")
        print_debug(f"Port Number: {port_number}")
    finally:
        clientSocket.close()


# Function to connect client to server using UDP

def udp_connection(ip_address, port_number):
    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:

        print_debug("Session has been established")
        print_debug(f"IP Address: {ip_address}")
        print_debug(f"Port Number: {port_number}")

        #Same concept as TCP, but when sending request and receiving response, use the UDP conventions
        while True:
            #connection established; get user input command
            client_command = input("myftp> ")
            #since user will input ex: get file.txt; need to sleep to get the command neccesary
            command = client_command.split(" ")
            # first part will process the command
            executed_command = command[0]

            #verify the commands

            # put command
            # format put filename
            if executed_command == "put":
                opcode = "000"
                # other part of string is the file name
                filename = command[1]
                try:
                    # size of the file in byte
                    file_size = os.path.getsize(f"client/{filename}")

                except:
                    # if file dont exist
                    print_debug("file does not exist")
                    continue

                # length of file name
                filename_length = len(filename)

                # convert the file name length in 32 bit
                filename_length_32bit = bin(filename_length)[2:].zfill(32)

                filename_length_5bits = filename_length_32bit[:5]

                # convert the file size in 4 bytes
                file_size_4bytes = file_size.to_bytes(4, 'little')

                # since 4 byte represents the file; that maximum file size allowed is 2^32 bytes

                # verify that the file is within the limit
                if (file_size < 2 ** 32):
                    # verify that name length does not exceed 31 characters
                    if (filename_length < 32):
                        # construct the request
                        filename_length_5bits = format(filename_length, '05b')
                        first_byte = int(opcode + filename_length_5bits, 2).to_bytes(1, 'little')
                        file_size_4bytes = file_size.to_bytes(4, 'little')

                        client_request = first_byte + filename.encode() + file_size_4bytes

                        # write in the file
                        with open(f"client/{filename}", "rb") as f:
                            client_request += f.read()

                            # send the client request to the UDP server to process
                            clientSocket.sendto(client_request, (ip_address, port_number))

                            # receive respononse from server
                            server_response, serverAddr = clientSocket.recvfrom(8000000)

                            # only res_code needed from the server for the put command
                            res_code, _ = convertServerResponse(server_response)

                        # read the response
                        if (res_code == "000"):
                            print_debug("File transfer successfully completed!")
                        else:
                            print_debug("File transfer failed")
                    else:
                        print_debug("Length of file name is too large")

                else:
                    print_debug("Size of the file is too large")

            # get command (retrieve file)
            # format: get filename
            elif (executed_command == "get"):
                opcode = "001"
                filename = command[1]
                filename_length = len(filename)

                # make sure file lengh does not exceed 31 chaters including end
                if filename_length < 32:
                    client_request = int(opcode + format(filename_length, '05b'), 2).to_bytes(1,
                                                                                              'little') + filename.encode()

                    # send the client request to the UDP server to process
                    clientSocket.sendto(client_request, (ip_address, port_number))

                    # receive respononse from server
                    server_response, serverAddr = clientSocket.recvfrom(8000000)

                    # read the response
                    res_code,filename_length = convertServerResponse(server_response)

                    if res_code == "001":
                        file_name = server_response[1:filename_length + 1].decode()
                        file_size = int.from_bytes(server_response[filename_length + 1:filename_length + 5],
                                                   'little')
                        file_data = server_response[filename_length + 5:filename_length + 5 + file_size]
                        with open(f"client/{file_name}", "wb") as f:
                            f.write(file_data)
                        print_debug("File downloaded successfully.")

                    elif res_code == "010":
                        print_debug("File not found.")
                else:
                    print_debug("Length of file name is too large")


            #change command (change old file name to new file name)
            #Format: change oldFilename newFilename
            elif executed_command == "change":
                try:
                    assert (len(command) == 3)
                except:
                    print_debug("Please input the function correctly following this format -> change oldFilename newFilename")
                old_file_name = command[1]
                new_file_name = command[2]
                opcode = "010"
                old_file_name_length = len(old_file_name)
                new_file_name_length = len(new_file_name)
                if old_file_name_length > 31 or new_file_name_length > 31:
                    print_debug("Old or new file name is too large.")
                else:
                    client_request = int(opcode + format(old_file_name_length, '05b'), 2).to_bytes(1, 'little')
                    client_request += old_file_name.encode()
                    client_request += int(format(new_file_name_length, '05b'), 2).to_bytes(1, 'little')
                    client_request += new_file_name.encode()

                    # send the client request to the UDP server to process
                    clientSocket.sendto(client_request, (ip_address, port_number))

                    # receive respononse from server
                    server_response, serverAddr = clientSocket.recvfrom(8000000)

                    # only res_code needed from the server for the put command
                    res_code, _ = convertServerResponse(server_response)

                    if res_code == "000":
                        print_debug(
                        f"Old file name:{old_file_name} has been changed to new file name entered:{new_file_name}")
                    elif res_code == "101":
                        print_debug("Unsuccessful file name change.")


            elif executed_command == "summary":
                opcode = "011"
                filename = command[1]
                filename_length = len(filename)



                #verify that file name does not exceed from the character
                if filename_length < 32:
                    client_request = int(opcode+ format(filename_length, '05b'), 2).to_bytes(1, 'little') + filename.encode()

                    # send the client request to the UDP server to process
                    clientSocket.sendto(client_request, (ip_address, port_number))

                    # receive respononse from server
                    server_response, serverAddr = clientSocket.recvfrom(8000000)

                    # read the response
                    res_code,filename_length = convertServerResponse(server_response)

                    if res_code == "010":
                        print_debug(f"statistical summary request received for {filename} refer to server log")

                    elif res_code == "011":
                        print_debug("Error file not found or No Numerical Number in the File")

            #help command
            #format: help
            elif executed_command == "help":
                opcode = "100"
                client_request = int(opcode+format(0,'05b'), 2).to_bytes(1, 'little')

                # send the client request to the UDP server to process
                clientSocket.sendto(client_request, (ip_address, port_number))

                # receive respononse from server
                server_response, serverAddr = clientSocket.recvfrom(8000000)



                # read the response
                res_code, lengh_help = convertServerResponse(server_response)

                if res_code == "110":
                    help_message = server_response[1:1 + lengh_help].decode()
                    print_debug(f"{help_message}")

            elif executed_command == "bye":
                print_debug("Closing client connection")
                clientSocket.close()
                break

            #if executed_commmand doesnt match with what exists....
            else:
                print_debug("Invalid command, use help for valid commands")




    except socket.error as e:
        print_debug(f"UDP connection failed: {e}")
    finally:
        clientSocket.close()


# Ask the user to choose between UDP and TCP connection
protocol_selection = input("Press '1' for TCP, or Press '2' for UDP: ").strip()

# Response according to user's choice
if protocol_selection == '1':
    print_debug("You have chosen a TCP connection.")
    ip_address, port_number,debug_flag = get_ip_and_port()
    debug_flag = True if debug_flag == 1 else False

    tcp_connection(ip_address, port_number)

elif protocol_selection == '2':
    print_debug("You have chosen a UDP connection.")
    ip_address, port_number,debug_flag = get_ip_and_port()
    debug_flag = True if debug_flag == 1 else False

    udp_connection(ip_address, port_number)

else:
    print_debug("Invalid choice. Please press '1' for TCP or '2' for UDP.")