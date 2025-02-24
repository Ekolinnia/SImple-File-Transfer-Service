# COEN366-FTP
A File Transfer Service (FTP) 
Anna Bui 40212221
Joseph Regipaultren 40156682

# To run:
1. Download files client.py and server.py
2. Test files are located in the file folder. Place these files in client or server to test the FTP.
3. Open two seperate terminals
4. Run server.py by writting on terminal 1: python3 server/server.py and follow instructions.
5. Run client.py by writting on terminal 2: python3 client/client.py and follow instructions.

# Supported commands
1. help : lists all available commands
2. put filename with its extention, example file.txt: copies file from client to server
3. get filename with its extention, example file.txt: copies file from server to client
4. change oldfilename newfilename, with its extention : renames file in server
5. summary filname: The server replies by generating a file containing the maximum, minimum and average. Please note that the numbers in the file to be summarized should be spaced apart from one another.
5. bye: closes connection

