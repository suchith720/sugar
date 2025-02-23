# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/06_parse-wikipedia-dump.ipynb.

# %% auto 0
__all__ = ['process_index_file', 'process_worker', 'XMLSAXParser', 'process_stream_contents', 'main',
           'extract_article_categories', 'extract_article_text', 'extract_article_redirects', 'get_proc_func',
           'parse_args']

# %% ../nbs/06_parse-wikipedia-dump.ipynb 2
import os, bz2, queue, wikitextparser, multiprocessing, xml.sax, io, argparse, gzip, mwparserfromhell
from timeit import default_timer as timer

# %% ../nbs/06_parse-wikipedia-dump.ipynb 3
def process_index_file(index_source, persist=True):
    index_offsets_persisted = index_source + ".offsets"

    if os.path.exists(index_offsets_persisted):
        try:
            index_filehandle = open(index_offsets_persisted, "r")
            offset_strings = index_filehandle.readlines()
            sorted_offset_strings = [int(offset) for offset in offset_strings]
            return sorted_offset_strings
        finally:
            index_filehandle.close()

    else:
        stream_offsets = set()
        try:
            index_filehandle = bz2.BZ2File(index_source)

            last_offset = -1
            for line in index_filehandle:
                offset = int(line.decode("utf-8").split(":")[0])
                if offset != last_offset:
                    stream_offsets.add(offset)
                    last_offset = offset
        finally:
            index_filehandle.close()

        sorted_stream_offsets = sorted(stream_offsets)

        if persist:
            try:
                offset_output_filehandle = open(index_offsets_persisted, "w")
                sorter_stream_offset_strings = [str(offset) for offset in sorted_stream_offsets]
                sorter_stream_offset_string = '\n'.join(sorter_stream_offset_strings)

                offset_output_filehandle.write(sorter_stream_offset_string)
            finally:
                offset_output_filehandle.close()

        return sorted_stream_offsets
        

# %% ../nbs/06_parse-wikipedia-dump.ipynb 4
def process_worker(work_queue, work_queue_lock, articles_source, cache_dir, proc_type):
    offsets_processed = 0
    stream_filehandle = open(articles_source, "rb")
    try:
        while True:
            try:
                work_queue_lock.acquire()
                stream_offset = work_queue.get(block=False)
            finally:
                work_queue_lock.release()

            stream_filehandle.seek(stream_offset)
            decompressor = bz2.BZ2Decompressor()

            output = [b'<pages>']
            while not decompressor.eof:
                output.append(decompressor.decompress(stream_filehandle.read(65536)))
            output.append(b'</pages>')

            contents = b''.join(output)
            process_stream_contents(contents, cache_dir, proc_type)
            offsets_processed += 1
    except queue.Empty:
        return
    finally:
        print("Worker process shutting down after processing {} offsets".format(offsets_processed))
        stream_filehandle.close()

# %% ../nbs/06_parse-wikipedia-dump.ipynb 5
class XMLSAXParser(xml.sax.ContentHandler):
    def __init__(self, cache_dir, proc_type):
        super().__init__()

        self.cache_dir, self.proc_func = cache_dir, get_proc_func(cache_dir, proc_type)

        self.read_stack = []
        self.page_id = None
        self.page_title = None
        self.page_redirect = None
        self.page_ns = None
        self.page_content = None

        self.page_count = 0
        self.in_page = False

    def startElement(self, tag_name, attributes):

        self.text_aggregate = []

        if tag_name == "page":
            self.page_redirect = None
            self.page_title = None
            self.page_id = None
            self.page_ns = None
            self.page_content = None
            self.in_page = True
        else:
            if (tag_name == "redirect") and (self.read_stack[-1] == "page"):
                self.page_redirect = attributes["title"]

        self.read_stack.append(tag_name)

    def endElement(self, tag_name):
        if (len(self.read_stack) > 0) and (tag_name == self.read_stack[-1]):
            del self.read_stack[-1]
        else:
            raise Exception("Tag ({}) does not match open tag ({}).".format(tag_name, self.read_stack[-1]))

        element_string = ''.join(self.text_aggregate)

        if tag_name == "page":
            self.in_page = False
            # We have the whole page so do with it what you will
            self.proc_func(self.cache_dir, self.page_id, self.page_ns, self.page_title, self.page_redirect, self.page_content)
        else:
            if self.in_page:
                if self.read_stack[-1] == "page":
                    if tag_name == "title":
                        self.page_title = element_string
                    elif (tag_name == "id") and self.read_stack[-1]:
                        self.page_id = int(element_string)
                    elif tag_name == "ns":
                        self.page_ns = int(element_string)
                elif self.read_stack[-1] == "revision":
                    # the actual page contents exist as a revision
                    if tag_name == "text":
                        self.page_content = element_string

    text_aggregate = []

    def characters(self, content):
        if self.in_page:
            self.text_aggregate.append(content)
            

# %% ../nbs/06_parse-wikipedia-dump.ipynb 6
def process_stream_contents(manyPages, cache_dir, proc_type):
    reader = XMLSAXParser(cache_dir, proc_type)
    try:
        byte_stream = io.BytesIO(manyPages)
        xml.sax.parse(byte_stream, reader)
    finally:
        byte_stream.close()
        

# %% ../nbs/06_parse-wikipedia-dump.ipynb 7
def main(index_source, articles_source, cache_dir, proc_type):
    os.makedirs(cache_dir, exist_ok=True)
    try:
        sorted_stream_offsets = process_index_file(index_source)
        if (sorted_stream_offsets is None) or (len(sorted_stream_offsets) < 1):
            raise Exception("Index file unsuccessful")

        process_count = multiprocessing.cpu_count()//2

        work_queue = multiprocessing.Queue()
        work_queue_lock = multiprocessing.Lock()

        [work_queue.put(x) for x in sorted_stream_offsets]

        jobs = []

        for i in range(process_count):
            p = multiprocessing.Process(target=process_worker, args=(work_queue,work_queue_lock, articles_source, cache_dir, proc_type))
            p.start()
            jobs.append(p)

        for j in jobs:
            j.join()

    except Exception as e:
        print(e)

# %% ../nbs/06_parse-wikipedia-dump.ipynb 8
# this is a placeholder. Presumably you would do something more useful
def extract_article_categories(cache_dir, page_id, page_ns, page_title, page_redirect, page_content):
    if page_redirect is None and page_ns == 0:
        page_parsed = wikitextparser.parse(page_content)

        categories = [o.target for o in page_parsed.wikilinks if o.target is not None and o.target.startswith("Category:")]
        if len(categories):
            with open(f'{cache_dir}/categories/{page_id}.txt', 'w') as file:
                file.write(f'{page_id}->{page_title}\n')
                for o in categories: file.write(o + '\n')
            print("Parsed page {}-{}".format(page_id, page_title))

    elif page_redirect is not None and (page_ns == 0 or page_ns == 14) and len(page_title) and len(page_redirect):
        fname = f'{cache_dir}/page_redirects/{page_id}.txt' if page_ns == 0 else f'{cache_dir}/category_redirects/{page_id}.txt'
        with open(fname, 'w') as file:
            file.write(f'{page_title}->{page_redirect}\n')
        print(f'{page_title}->{page_redirect}')

def extract_article_text(cache_dir, page_id, page_ns, page_title, page_redirect, page_content):
    if page_redirect is None and page_ns == 0:
        page_parsed = mwparserfromhell.parse(page_content)
        text = page_parsed.strip_code()
        if len(text):
            with open(f'{cache_dir}/texts/{page_id}.txt', 'w') as file:
                file.write(f'{page_id}->{page_title}\n')
                file.write(text + '\n')
            print("Parsed page {}-{}".format(page_id, page_title))

    elif page_redirect is not None and page_ns == 0 and len(page_title) and len(page_redirect):
        fname = f'{cache_dir}/page_redirects/{page_id}.txt'
        with open(fname, 'w') as file:
            file.write(f'{page_title}->{page_redirect}\n')
        print(f'{page_title}->{page_redirect}')

def extract_article_redirects(cache_dir, page_id, page_ns, page_title, page_redirect, page_content):
    if page_redirect is not None and page_ns == 0:
        fname = f'{cache_dir}/page_redirects/{page_id}.txt'
        with open(fname, 'w') as file:
            file.write(f'{page_title}->{page_redirect}\n')
        print(f'{page_title}->{page_redirect}')

# %% ../nbs/06_parse-wikipedia-dump.ipynb 9
def get_proc_func(cache_dir, proc_type):
    if proc_type == 'page_category':
        os.makedirs(f'{cache_dir}/categories/', exist_ok=True)
        os.makedirs(f'{cache_dir}/page_redirects/', exist_ok=True)
        os.makedirs(f'{cache_dir}/category_redirects/', exist_ok=True)
        return extract_article_categories
    elif proc_type == 'page_text':
        os.makedirs(f'{cache_dir}/texts/', exist_ok=True)
        os.makedirs(f'{cache_dir}/page_redirects/', exist_ok=True)
        return extract_article_text
    elif proc_type == 'page_redirects':
        os.makedirs(f'{cache_dir}/page_redirects/', exist_ok=True)
        return extract_article_redirects
    else: raise ValueError(f'Invalid function type: {proc_type}')

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--articles_source', type=str, required=True)
    parser.add_argument('--cache_dir', type=str, required=True)
    parser.add_argument('--proc_type', type=str, required=True)
    parser.add_argument('--index_source', type=str, default=None)
    return parser.parse_args()

# %% ../nbs/06_parse-wikipedia-dump.ipynb 10
if __name__ == "__main__":
    start_time = timer()
