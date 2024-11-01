



from ftplib import FTP, error_perm, all_errors
from pathlib import Path

import subprocess
import datetime
import json
import time
import sys
import os


if getattr(sys, 'frozen', False):     # If the script is running as an executable
    currentPath = os.path.dirname(sys.executable)
else:
    currentPath = os.path.dirname(os.path.abspath(__file__))     # If the script is running as a .py file
JSON_PATH = os.path.join(currentPath, "config.json")
TIMEOUT = 4


def transferFile(localFileToUpload, remoteFilePath, ftp):
    try:
        if os.path.exists(localFileToUpload):
            with open(localFileToUpload, "rb") as file:
                ftp.storbinary(f"STOR {remoteFilePath}", file)
        else:
            print(f"Could not upload file: {localFileToUpload}. \n DOES NOT EXIST")
    except EOFError:
        print(f"There wass an error uploading file: {localFileToUpload}")

   

def main():
    # READS CONFIG DATA FROM JSON FILE
    try:
        if os.path.exists(JSON_PATH) == True:
            with open(JSON_PATH) as file:
                config = json.load(file)
        else:
            print(f"Script didnt find config file, make sure config.json is in same dir. PATH={JSON_PATH}")
            return "error"
    except json.JSONDecodeError as error:
        print(f"There was an error reading JSON data, wrong fotmatting?\n{error}")
        return "error"

    # CONNECTS TO FTP SEVRER
    try:
        ftp = FTP(config["ftp_server"], timeout=TIMEOUT)
        ftp.login(config["username"], config["password"])
        ftp.cwd(config["remote_path"])
        print("Sucsessfully connected to FTP server")
    except error_perm as e:
        print(f"Permission error, connecting to FTP server: {e}")
        return "error"
    except all_errors as e:
        print(f"There was a FTP error: \n{e}")
        return "error"


    # GENERATES THE PARENTFOLDER BACKUP NAME
    parentFolderName = config["backup_folder_name"] + str(datetime.datetime.now().strftime("%d-%m-%Y_%H_%M_%S")) # PLACES THE BACUP INTO A PARENT FOLDER
    ftp.mkd(parentFolderName)


    localPath = config["backup_path"] # THIS IS UPDATED EVRYTIME THE SCAN GOES DEEPER / SHALLOW
    currentStructurePath = parentFolderName
    transferedLocalFolders = [] # KEEPS TRACK OF TRANSFERED FILES/FOLDERS. SO WE DONT TRANSFER THE SAME FILE TWICE
    while True:

        if localPath == config['backup_path'].rsplit("/", 1)[0]: # STOPS IF CURRENT COPY LOCALPATH = BACKUP PATH 
            break
        
        filesInDir = os.listdir(localPath)
        foundFolder = False

        for file in filesInDir:

            if localPath + "/" + file not in transferedLocalFolders: # IF FILE HAS NOT BEEN TRANSFERED/COPIED
                if os.path.isdir(localPath + "/" + file):

                    localPath += "/" + file
                    currentStructurePath += "/" + file

                    ftp.mkd(currentStructurePath) # MAKE FOLDER
                    foundFolder = True

                    print(f"Transfered Folder: {currentStructurePath}")
                    break
                
                else: # NOT DIR
                    filePath = localPath + "/" + file
                    stucturePath = currentStructurePath + "/" + file

                    transferFile(filePath,  stucturePath, ftp) # TRANSFER FILE
                    transferedLocalFolders.append(filePath) # SAVE FILE PATH, SO IT DOESNT GET TRANSFERED AGAIN

                    print(f"Transfered File:   {stucturePath}")



        if foundFolder == False: # IF THE CURRENT FOLDER PATH DOES NOT CONTAIN ANY FOLDERS
            transferedLocalFolders.append(localPath)
            localPath = localPath.rsplit("/", 1)[0] # GOES TO PARENT FOLDER
            currentStructurePath = currentStructurePath.rsplit("/", 1)[0] # GOES TO PARENT FOLDER
            

    ftp.quit()


if __name__ == "__main__":
    error = main()
    if error == "error":
        time.sleep(60)


#transferFile()

