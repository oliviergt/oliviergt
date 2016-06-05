import argparse
import httplib2
import keyring
import os
import tempfile

# pip install --upgrade google-api-python-client
from oauth2client.contrib.keyring_storage import Storage
from apiclient.discovery import build
from oauth2client.client import OAuth2WebServerFlow

# TODO: keep track of version. Only download if necessary. Use a sqlite3
# database.
# TODO: Restore directory structure.
# TODO: Use only last 8 digits of id. This is just to eliminate name clashes
# anyway.
# TODO: ods vs xlsx.
# TODO: print all mimetypes to export formats.
# TODO: restore the modified date to match date from API.

KEYRING_SERVICE = 'export-google-drive'

OAUTH_SCOPE = 'https://www.googleapis.com/auth/drive'
REDIRECT_URI = 'urn:ietf:wg:oauth:2.0:oob'

DOCX = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
ODS = 'application/x-vnd.oasis.opendocument.spreadsheet'
SVG = 'image/svg+xml'  
PPTX = 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
PDF = 'application/pdf'

# u'application/vnd.google-apps.spreadsheet' --> ODS
# u'application/vnd.google-apps.drawing' --> SVG
# u'application/vnd.google-apps.form'
# u'application/vnd.google-apps.document' --> DOCX
# u'application/vnd.google-apps.map'
# u'application/vnd.google-apps.folder'
# u'application/vnd.google-apps.presentation' --> PPTX

class Exporter(object):

  def __init__(self, drive_service, export_directory):
    self.drive_service = drive_service
    self.export_directory = export_directory

  def Run(self):
    all_items = [item for item in self.ListFiles()]
    google_apps_types = set()
    for item in all_items:
      if 'mimeType' in item and 'google-apps' in item['mimeType']:
        google_apps_types.add(item['mimeType'])
    print google_apps_types
        
    for item in all_items:
      if 'mimeType' in item and 'google-apps' in item['mimeType']:
        for field in ['id', 'title', 'version', 'mimeType', 'ownedByMe',
            'modifiedDate']:
          if field in item:
            print '%s=%s' % (field, repr(item[field]))
        if 'exportLinks' in item:
          self.Export(item)
        print

  def ListFiles(self):
    page_token = None
    while True:
      files = self.drive_service.files().list(pageToken=page_token).execute()
      for item in files['items']:
        yield item
      page_token = files.get('nextPageToken')
      if not page_token:
        break

  def Export(self, item):
    for mime_type in item['exportLinks']:
      print mime_type
    self.ExportType('pdf', item, PDF, 'pdf')
    self.ExportType('native', item, ODS, 'ods')
    self.ExportType('native', item, DOCX, 'docx')
    self.ExportType('native', item, SVG, 'svg')
    self.ExportType('native', item, PPTX, 'pptx')

  def ExportType(self, folder, item, mime_type, extension):
    if mime_type not in item['exportLinks']:
      return
    download_url = item['exportLinks'][mime_type]
    title = item['title'].replace('/', '-')
    export_filename = os.path.join(
        self.export_directory,
        folder,
        '%s %s.%s' % (item['id'], title, extension))
    print "Downloading to %s" % export_filename
    if True:
      return
    resp, content = self.drive_service._http.request(download_url)
    if resp.status == 200:
      # May overwrite. That's what we want.
      with open(export_filename, 'wb') as f:
        f.write(content)
    else:
      print 'ERROR downloading %s' % item.get('title')


def Makedirs(directory):
  if not os.path.exists(directory):
    os.makedirs(directory)

def Main(user_name):
  # https://console.developers.google.com
  client_id = keyring.get_password(KEYRING_SERVICE, 'client_id')
  client_secret = keyring.get_password(KEYRING_SERVICE, 'client_secret')
  export_directory = tempfile.mkdtemp(prefix='google-drive-%s-' % user_name)
  Makedirs(os.path.join(export_directory, 'pdf'))
  Makedirs(os.path.join(export_directory, 'native'))

  storage = Storage(KEYRING_SERVICE, user_name)
  credentials = storage.get()

  if credentials is None:
    # Run through the OAuth flow and retrieve credentials
    flow = OAuth2WebServerFlow(client_id, client_secret, OAUTH_SCOPE, REDIRECT_URI)
    authorize_url = flow.step1_get_authorize_url()
    print 'Go to the following link in your browser: ' + authorize_url
    code = raw_input('Enter verification code: ').strip()
    credentials = flow.step2_exchange(code)
    storage.put(credentials)

  # Create an httplib2.Http object and authorize it with our credentials
  http = httplib2.Http()
  http = credentials.authorize(http)

  drive_service = build('drive', 'v2', http=http)
  exporter = Exporter(drive_service, export_directory)
  exporter.Run()


if __name__ == "__main__":
  parser = argparse.ArgumentParser(description='Export data from drive')
  parser.add_argument('user_name', metavar='name',
      help='the Google user name')
  args = parser.parse_args()
  Main(args.user_name)
