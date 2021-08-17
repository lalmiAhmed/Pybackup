import zipfile
import os
from progress.bar import Bar
import time
from datetime import date
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from socket import gethostbyname,gaierror
import httplib2
import shutil
from pathlib import Path


path_in = Path(os.path.dirname(__file__) + "/target") # On Linux :"/target" , On Windows: "\\target"
path_out = Path(os.path.dirname(__file__) + "/toUpload") # On Linux: "/toUpload", On Windows: "\\toUpload"
tries = 3 ; delay = 3

def now():
    t = time.localtime()
    return time.strftime("%H:%M:%S", t)

def file_compress(inp_file_names, out_zip_file,path):
    compression = zipfile.ZIP_DEFLATED
    zf = zipfile.ZipFile(out_zip_file, mode="w") 
    bar = Bar('Processing', max=len(os.listdir(path))) #progressing bar
    with open('log.txt','a+') as log:
        log.write("\n************************* "+str(date.today())+" *************************\n")
        try:
            for file_to_write in inp_file_names:
                zf.write(file_to_write, file_to_write, compress_type=compression)
                bar.next()
            try:
                shutil.move(out_zip_file,path_out)
            except shutil.Error as err:
                log.write(now()+"~--> "+" overwriting an existing zip\n")
                os.remove(Path(str(path_out)+"/"+out_zip_file))
                shutil.move(out_zip_file,path_out)
                pass
            log.write(now()+"~--> "+" Compression done\n")
        except FileNotFoundError as e:
            log.write(now()+"~--> "+ f' *** Exception occurred during zip process \n{e} \n')
        finally:
            zf.close()
            bar.finish()
           
file_name_list = []
for file in os.listdir(path_in):
    file_name_list.append(Path(str(path_in)+"/"+file))

zip_file_name = str(date.today().strftime('%d-%m-%Y'))+".zip"
file_compress(file_name_list, zip_file_name,path_in)

######################################################################################################

gauth = GoogleAuth()           
drive = GoogleDrive(gauth)  
i = 0
while(i<tries):
    try:
        with open('log.txt','a+') as log:
            file_list = drive.ListFile({'q': "'root' in parents and trashed=false"}).GetList()
            if not(file_list): log.write(now()+"~--> empty drive directory"+ "\n"+ "\n")
            file_list_titles = []
            for file in file_list:
                file_list_titles.append(file['title']) # getting a list of files titles from drive
            bar = Bar('Processing', max=len(os.listdir(path_out))) #progressing bar
            for x in os.listdir(path_out):
                if not(x in file_list_titles):
                    f = drive.CreateFile({'title': x})
                    f.SetContentFile(os.path.join(path_out, x))
                    f.Upload()
                    log.write(now()+"~--> the file named"+x+" uploaded successfully"+ "\n")
                    bar.next()
                    f = None
                else:
                    log.write(now()+"~--> the file named %s exists. \n" % x)
            bar.finish()
            break

    except httplib2.ServerNotFoundError or gaierror:
        with open('log.txt','a+') as log:
            log.write(now()+"~--> Failed to connect, trying after few minutes... \n")
            pass
        time.sleep(delay) ; i +=1