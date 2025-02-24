import socket
import threading
import os

#debug
debug_flag = True



#summary function to do the calculations
def calculate_stats(filename):
    try:
        #reads the file for numbers format: 1 2 3 4 5 6 7 8 0
        with open(f"server/{filename}") as file:
            #read line
            line = file.readline().strip()
            #split the line into # of strings
            number_strings = line.split()
            #convert to float
            numbers = [float(num) for num in number_strings if num.strip()]

        if numbers:
            maxNum = max(numbers)
            minNum = min(numbers)
            averageNum = sum(numbers) / len(numbers)

            #create a new file with the values
            summary_filename = f"server/summary_{filename}"
            with open(summary_filename, 'w') as summary_file:
                summary_file.write(f"max: {maxNum}\nmin: {minNum}\naverage: {averageNum:.2f}\n")
            return summary_filename

        else:
            res_code = "011"
            raise ValueError("the file does not have numbers")

    except FileNotFoundError:
        print(f"File not found")
        return None
    except Exception as e:
        print(f"error: {e}")
        return None

# Function tcp client
def responseToTcpClient(TCPsocket):
    try:
        while True:
            #will receive the command from the client
            request = TCPsocket.recv(8000000)

            #if doesn't receive anything breaks the loop
            if not request:
                break

            #process the received message
            first_byte, request = request[0], request[1:]
            first_byte = format(first_byte, '08b')
            opcode, filename_length = first_byte[:3], int(first_byte[3:], 2)

            #handle put command

            if opcode == "000":
                print("Received put command from client")
                #get the file name from the request
                print("Raw request data:", request)

                print("Filename length:", filename_length)

                file_name = request[:filename_length].decode()


                file_size = int.from_bytes(request[filename_length:filename_length + 4], 'little')
                file_data = request[filename_length + 4:filename_length + 4 + file_size]

                #verify that it received correctly
                print(f"Opcode is {opcode}.\n File name is {file_name}.\n File size is {str(file_size)}.")
                with open(f"server/{file_name}",
                      "wb") as f:
                    f.write(file_data)

                #response message format
                res_code = "000"
                serverResponse = int(res_code+ format(filename_length, '05b'),2).to_bytes(1,'little' )

                #send response message TCP
                TCPsocket.send(serverResponse)



            #handle get command
            elif opcode == "001":
                print("Received get command from client")
                filename = request[:filename_length].decode()
                res_code = "001"
                try:
                    #file size
                    file_size = os.path.getsize(f"server/{filename}")
                #if the file is not found
                except FileNotFoundError:
                    res_code = "011"

                if res_code == "001":
                    filename_length = len(filename)
                    #convert the file size to 32 bit
                    file_size_bin = format(file_size, '032b')
                    if file_size < 2**32:
                        if filename_length <32:
                            serverResponse = int(res_code +format(filename_length, '05b'), 2).to_bytes(1, 'little') + filename.encode() + int(file_size_bin, 2).to_bytes(4, 'little')

                            with open(f"server/{filename}","rb") as f:
                                serverResponse += f.read()

                        else:
                            print("Size of the file is too big")
                            serverResponse = int(res_code+format(0, '05b'), 2).to_bytes(1, 'little')
                    else:
                        serverResponse = int(res_code+format(0, '05b'), 2).to_bytes(1, 'little')

            #send the server resposne to the client
                TCPsocket.send(serverResponse)

            #handle change command
            elif opcode == "010":
                print("Received change command from client")
                oldfile_name = request[:filename_length].decode()
                newfile_name_length = int.from_bytes(request[filename_length: filename_length + 1], 'little')
                newfile_name = request[filename_length + 1: newfile_name_length + filename_length + 1].decode()

                res_code = "010"
                try:
                    os.rename(f"server/{oldfile_name}", F"server/{newfile_name}")
                    print(f"Old file name: {oldfile_name} has been changed to new file name: {newfile_name}.")
                except:
                    # response to unsuccessful change
                    res_code = "101"
                    print("Failed to change file name")

                # send the server response to client
                serverResponse = int(res_code + format(0, '05b'), 2).to_bytes(1, 'little')

                TCPsocket.send(serverResponse)

            #summary command
            # handle summary
            elif opcode == "011":
                # implement the summary file name
                filename = request[:filename_length].decode()
                filename_length = len(filename)
                file_size = int.from_bytes(request[filename_length:filename_length + 4], 'little')
                file_data = request[filename_length + 4:filename_length + 4 + file_size]
                file_size_bin = format(file_size, '032b')

                if filename_length < 32:
                    # received summary request successfully
                    res_code = "010"
                    # will create a file with the summary
                    calculate_stats(filename)
                    serverResponse = int(res_code + format(filename_length, '05b'), 2).to_bytes(1,
                                                                                                'little') + filename.encode() + int(
                        file_size_bin, 2).to_bytes(4, 'little')



                else:
                    print("Error File not found")
                    res_code = "011"
                    serverResponse = int(res_code + format(0, '05b'), 2).to_bytes(1, 'little')

                #send value to client
                TCPsocket.send(serverResponse)

                # handle help command
            elif opcode == "100":
                print("Received help command from client")
                res_code = "110"
                help_command = (f"put/get/change/summary/help/bye")
                help_length = len(help_command)
                first_byte = int(res_code + format(help_length, '05b'), 2).to_bytes(1, 'little')
                serverResponse = first_byte + help_command.encode()

                # send response to client
                TCPsocket.send(serverResponse)


            #handle unknown requests command
            else:
                print(f"Unknown command {request}")
                res_code = "100"
                serverResponse = int(res_code + format(0, '05b'), 2).to_bytes(1, 'little')

                # send response to client
                TCPsocket.send(serverResponse)


    except socket.error as e:
        print(f"Error handling TCP client: {e}")
    finally:
        TCPsocket.close()

def responseToUdpClient(UDPsocket):
    while True:
        try:
            request, client_address = UDPsocket.recvfrom(8000000)

            # process the received message
            first_byte, request = request[0], request[1:]
            first_byte = format(first_byte, '08b')
            opcode, filename_length = first_byte[:3], int(first_byte[3:], 2)

            # handle put command

            if opcode == "000":
                print("Received put command from client")
                # get the file name from the request
                file_name = request[:filename_length].decode()

                # Return int of list of bytes
                file_size = int.from_bytes(request[filename_length:filename_length + 4], 'little')
                file_data = request[filename_length + 4:filename_length + 4 + file_size]

                # verify that it received correctly
                print(f"Opcode is {opcode}.\n File name is {file_name}.\n File size is {str(file_size)}.")
                with open(f"server/{file_name}",
                          "wb") as f:
                    f.write(file_data)

                # response message format
                res_code = "000"
                serverResponse = int(res_code + format(filename_length, '05b'), 2).to_bytes(1, 'little')

                # send response message UDP
                UDPsocket.sendto(serverResponse,client_address)



            # handle get command
            elif opcode == "001":
                print("Received get command from client")
                filename = request[:filename_length].decode()
                try:
                    # file size
                    file_size = os.path.getsize(f"server/{filename}")
                # if the file is not found
                except FileNotFoundError:
                    res_code = "011"

                # if doesnt go to file error
                res_code = "001"
                filename_length = len(filename)

                # convert the file size to 32 bit
                file_size_bin = format(file_size, '032b')
                if file_size < 2 ** 32:
                    if filename_length < 32:
                        serverResponse = int(res_code + format(filename_length, '05b'), 2).to_bytes(1,
                                                                                                    'little') + filename.encode() + int(
                            file_size_bin, 2).to_bytes(4, 'little')

                        with open(f"server/{filename}", "rb") as f:
                            serverResponse += f.read()

                    else:
                        print("Size of the file is too big")
                        serverResponse = int(res_code + format(0, '05b'), 2).to_bytes(1, 'little')
                else:
                    serverResponse = int(res_code + format(0, '05b'), 2).to_bytes(1, 'little')

                # send response message UDP
                UDPsocket.sendto(serverResponse, client_address)

            # handle change command
            elif opcode == "010":
                print("Received change command from client")
                oldfile_name = request[:filename_length].decode()
                newfile_name_length = int.from_bytes(request[filename_length: filename_length + 1], 'little')
                newfile_name = request[filename_length + 1: newfile_name_length + filename_length + 1].decode()

                res_code = "010"
                try:
                    os.rename(f"server/{oldfile_name}", F"server/{newfile_name}")
                    print(f"Old file name: {oldfile_name} has been changed to new file name: {newfile_name}.")
                except:
                    # response to unsuccessful change
                    res_code = "101"
                    print("Failed to change file name")

                # send the server response to client
                serverResponse = int(res_code + format(0, '05b'), 2).to_bytes(1, 'little')
                # send response message UDP
                UDPsocket.sendto(serverResponse, client_address)

            #handle summary
            elif opcode == "011":
                # implement the summary file name
                filename = request[:filename_length].decode()
                filename_length = len(filename)
                file_size = int.from_bytes(request[filename_length:filename_length + 4], 'little')
                file_data = request[filename_length + 4:filename_length + 4 + file_size]
                file_size_bin = format(file_size, '032b')


                if filename_length < 32:
                    #received summary request successfully
                    res_code = "010"
                    #will create a file with the summary
                    calculate_stats(filename)

                    serverResponse = int(res_code + format(filename_length, '05b'), 2).to_bytes(1,
                                                                                                'little') + filename.encode() + int(
                        file_size_bin, 2).to_bytes(4, 'little')


                else:
                    print("Error File not found")
                    res_code = "011"
                    serverResponse = int(res_code + format(0, '05b'), 2).to_bytes(1, 'little')

                # send response message UDP
                UDPsocket.sendto(serverResponse, client_address)

            # handle help command
            elif opcode == "100":
                print("Received help command from client")
                res_code = "110"
                help_command = (f"put/get/change/summary/help/bye")
                help_length = len(help_command)
                first_byte = int(res_code + format(help_length, '05b'), 2).to_bytes(1, 'little')
                serverResponse = first_byte + help_command.encode()

                # send response message UDP
                UDPsocket.sendto(serverResponse, client_address)


            # handle unknown requests command
            else:
                print(f"Unknown command {request}")
                res_code = "100"
                serverResponse = int(res_code + format(0, '05b'), 2).to_bytes(1, 'little')

                # send response message UDP
                UDPsocket.sendto(serverResponse, client_address)


        except socket.error as e:
            print(f"Error handling UDP client: {e}")
            break  # Exit the loop if there's an error


def startingTCPserver(ip_address, port_number):
    tcpSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcpSocket.bind((ip_address, port_number))
    tcpSocket.listen(5)
    print(f"TCP Server listening on {ip_address}:{port_number}")


    while True:
        TCPsocket, address = tcpSocket.accept()
        print(f"TCP connection established with {address}")
        client_thread = threading.Thread(target=responseToTcpClient, args=(TCPsocket,))
        client_thread.start()


def startingUDPserver(ip_address, port_number):
    UDPsocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    UDPsocket.bind((ip_address, port_number))
    print(f"UDP Server listening on {ip_address}:{port_number}")
    responseToUdpClient(UDPsocket)




if __name__ == "__main__":
    ip_address = '127.0.0.1'
    port_number = 12000

    tcp_thread = threading.Thread(target=startingTCPserver, args=(ip_address, port_number))
    udp_thread = threading.Thread(target=startingUDPserver, args=(ip_address, port_number))

    tcp_thread.start()
    udp_thread.start()

    tcp_thread.join()
    udp_thread.join()

    #will process the request sent by the client