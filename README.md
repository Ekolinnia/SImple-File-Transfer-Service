COEN366-FTP

A File Transfer Service (FTP) 

To run:

Download files client.py and server.py
Test files are located in the file folder. Place these files in client or server to test the FTP.
Open two seperate terminals
Run server.py by writting on terminal 1: python3 server/server.py and follow instructions.
Run client.py by writting on terminal 2: python3 client/client.py and follow instructions.
Supported commands

help : lists all available commands
put filename with its extention, example file.txt: copies file from client to server
get filename with its extention, example file.txt: copies file from server to client
change oldfilename newfilename, with its extention : renames file in server
summary filname: The server replies by generating a file containing the maximum, minimum and average. Please note that the numbers in the file to be summarized should be spaced apart from one another.
bye: closes connection
