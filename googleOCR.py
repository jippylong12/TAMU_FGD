from __future__ import print_function
import httplib2
import os
import time
from apiclient import errors
from apiclient.http import MediaFileUpload
from apiclient import discovery
import oauth2client
from oauth2client import client
from oauth2client import tools
_author_ = "Marcus Salinas"

# attempts to use google drive api to take pdf files and create an OCR version that we can use.


try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/drive-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/drive'
CLIENT_SECRET_FILE = 'client_secret_OCR.json'
APPLICATION_NAME = 'freeGradeDistribution'


def insert_file(service, title, description, parent_id, mime_type, filename):
  """Insert new file.

  Args:
    service: Drive API service instance.
    title: Title of the file to insert, including the extension.
    description: Description of the file to insert.
    parent_id: Parent folder's ID.
    mime_type: MIME type of the file to insert.
    filename: Filename of the file to insert.
  Returns:
    Inserted file metadata if successful, None otherwise.
  """
  media_body = MediaFileUpload(filename, mimetype=mime_type, resumable=True)
  body = {
    'title': title,
    'description': description,
    'mimeType': mime_type
  }
  # Set the parent folder.
  if parent_id:
    body['parents'] = [{'id': parent_id}]

  try:
    file = service.files().insert(
        body=body,
        media_body=media_body,
        ocr=True).execute()

    # Uncomment the following line to print the File ID
    # print 'File ID: %s' % file['id']

    return file
  except errors.HttpError as error:
    print ('An error occured: %s' % error)
    return None


def download_file(service, drive_file):
  """Download a file's content.

  Args:
    service: Drive API service instance.
    drive_file: Drive File instance.

  Returns:
    File's content if successful, None otherwise.
  """
  download_url = drive_file['exportLinks']['text/plain']
  if download_url:
    resp, content = service._http.request(download_url)
    if resp.status == 200:
      # print ('Status: %s' % resp)
      return content
    else:
      print ('An error occurred: %s' % resp)
      return None
  else:
    # The file doesn't have any content stored on Drive.
    return None

def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'client_secret_OCR.json')

    store = oauth2client.file.Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

def googleOCR(folderName,pdfList):
    """Shows basic usage of the Google Drive API.

    Creates a Google Drive API service object and outputs the names and IDs
    for up to 10 files.
    """
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('drive', 'v2', http=http)

    # create folder for year in
    file_metadata = {
        'title': folderName,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    rootFolder = service.files().insert(body=file_metadata,
                                        fields='id').execute()


    for pdf in pdfList:
        print(pdf)
        fileTitle = pdf.replace('.pdf','')
        print("OCR file")
        file = insert_file(service,fileTitle,'description',rootFolder.get('id'), 'application/pdf',pdf)
        print("done inserting file")
        time.sleep(3)
        print("downloading file")
        text = download_file(service,file)
        print("done downloading file")
        with open(fileTitle + '.txt','w') as outputFile:
            outputFile.write(text.strip())





# folderName = 'Summer2013'
# pdfList = ['grd20132VM.pdf']
# filePath = os.getcwd() + "\\GradeDistributionsDB\\" + folderName
# os.chdir(filePath)
# googleOCR(folderName,pdfList)