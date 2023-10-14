import optparse
import requests
import os
import time


def verbose(verbose, logstr):
    if verbose:
        print(logstr)


class FileUploader():
    def __init__(self, url, file_path, size, verbose):
        self.url = url
        self.file_path = file_path
        self.verbose = verbose
        self.chunk_size = size
        self.up_part_ext = '.uppart'
        self.cache_path = '.cache'

    def start(self):
        with open(self.file_path, 'rb') as f:
            verbose(self.verbose, f'{self.file_path}: start uploading')
            file_name = os.path.basename(self.file_path)
            size = os.path.getsize(self.file_path)
            start = 0

            cache_path = f'{os.path.dirname(self.file_path)}\{self.cache_path}'
            if not os.path.exists(cache_path):
                os.mkdir(cache_path)
            
            cache_file = f'{cache_path}\{file_name}{self.up_part_ext}'
            #print(cache_file)
            if os.path.exists(cache_file):
                with open(cache_file, 'r') as cf:
                    start = int(cf.read())
                    verbose(self.verbose, f'{file_name}: last upload progress {start}/{size}')
            f.seek(start)
            while start < size:
                end = min(start + self.chunk_size, size)
                chunk = f.read(self.chunk_size)
                headers = {
                    'Content-Range': f'bytes {start}-{end-1}/{size}',
                    'Content-Disposition': f'attachment; filename="{file_name}"'
                }
                response = requests.post(self.url, headers=headers, data=chunk)
                if response.status_code == 200 or response.status_code == 201:
                    with open(cache_file, 'w') as cf:
                        cf.write(str(end))
                    start = end
                    verbose(self.verbose, f'{file_name}: progress {start}/{size}')
                    print(f'{file_name}: {response.content}')
                else:
                    print(f'{file_name}: upload error! code={response.status_code}')
                    time.sleep(1)
                    


class FileDownloader():
    def __init__(self, url, file_path, size, verbose):
        self.url = url
        self.file_path = file_path
        self.verbose = verbose
        self.chunk_size = size

    def start(self):
        headers = {}
        if os.path.exists(self.file_path):
            start = os.path.getsize(self.file_path)
            headers = {'Range': f'bytes={start}-'}
            print(f'{self.url}: download resume from {start}')
        else:
            start = 0
            print('{self.url}: download start from beginning')
        response = requests.get(self.url, headers=headers, stream=True)
        with open(self.file_path, 'ab') as f:
            total_size = int(response.headers.get('content-length', start))
            for chunk in response.iter_content(chunk_size=self.chunk_size):
                if chunk:
                    f.write(chunk)
                    f.flush()
            print(f'success!')


def main():
    parser = optparse.OptionParser()
    parser.add_option("-f", "--file", dest="path", help="file path to be upload/download")
    parser.add_option("-u", "--url", dest="url", help="url to be upload/download")
    parser.add_option("-d", "--down", dest="isdown", action="store_true", default=False, help="download mode")
    parser.add_option("-s", "--size", dest="size", default=1024*1024*64, help="upload/download chunked size")
    parser.add_option("-v", "--verbose", dest="verbose", action="store_true", default=False, help="print running verbose log")
    (options, args) = parser.parse_args()

    if options.isdown:
        downloader = FileDownloader(options.url, options.path, int(options.size), options.verbose)
        downloader.start()
        return
    uploader = FileUploader(options.url, options.path, int(options.size), options.verbose)
    uploader.start()

if __name__ == '__main__':
    main()
