# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/06_parse-wikipedia-dump.ipynb.

# %% auto 0
__all__ = ['process_index_file', 'process_worker', 'process_stream_contents', 'XMLSAXParser', 'extract_article_info', 'main',
           'combine_info', 'parse_args']

# %% ../nbs/06_parse-wikipedia-dump.ipynb 2
import os, bz2, queue, wikitextparser, multiprocessing, xml.sax, io, argparse, gzip, mwparserfromhell, pickle, joblib
from timeit import default_timer as timer
from tqdm import tqdm

# %% ../nbs/06_parse-wikipedia-dump.ipynb 4
def process_index_file(index_source, persist=True):
    index_offsets_persisted = index_source + ".offsets"

    if os.path.exists(index_offsets_persisted):
        with open(index_offsets_persisted, "r") as file: 
            offset_strings = file.readlines()
            sorted_offset_strings = [int(offset) for offset in offset_strings]
            return sorted_offset_strings
    else:
        stream_offsets = set()
        with bz2.BZ2File(index_source) as file:
            last_offset = -1
            for line in file:
                offset = int(line.decode("utf-8").split(":")[0])
                if offset != last_offset:
                    stream_offsets.add(offset)
                    last_offset = offset
                    
        sorted_stream_offsets = sorted(stream_offsets)
        if persist:
            with open(index_offsets_persisted, "w") as file:
                sorter_stream_offset_strings = [str(offset) for offset in sorted_stream_offsets]
                sorter_stream_offset_string = '\n'.join(sorter_stream_offset_strings)
                file.write(sorter_stream_offset_string)
                
        return sorted_stream_offsets
        

# %% ../nbs/06_parse-wikipedia-dump.ipynb 7
def process_worker(worker_queue, worker_outputs, articles_source):
    offsets_processed = 0
    stream_filehandle = open(articles_source, "rb")
    try:
        while True:
            stream_offset = worker_queue.get()
            if stream_offset is None:
                worker_outputs.put(None)
                break
            
            stream_filehandle.seek(stream_offset)
            decompressor = bz2.BZ2Decompressor()

            output = [b'<pages>']
            while not decompressor.eof: output.append(decompressor.decompress(stream_filehandle.read(65536)))
            output.append(b'</pages>')

            contents = b''.join(output)

            # actual task
            page_info, redirect_info = process_stream_contents(contents)
            page_info = extract_article_info(page_info)
            
            offsets_processed += 1
            worker_outputs.put((page_info, redirect_info))
    finally:
        # print(f"Worker process shutting down after processing {offsets_processed} offsets")
        stream_filehandle.close()
        

# %% ../nbs/06_parse-wikipedia-dump.ipynb 17
def process_stream_contents(manyPages):
    reader = XMLSAXParser()
    with io.BytesIO(manyPages) as byte_stream:
        xml.sax.parse(byte_stream, reader)
    return reader.page_info, reader.redirect_info
        

# %% ../nbs/06_parse-wikipedia-dump.ipynb 18
class XMLSAXParser(xml.sax.ContentHandler):
    def __init__(self):
        super().__init__()
        
        self.read_stack = []
        self.page_count = 0
        
        self.page_id, self.page_title, self.page_redirect = None, None, None
        self.page_ns, self.page_content = None, None
        
        self.in_page = False

        self.page_info, self.redirect_info = dict(), dict()

    def startElement(self, tag_name, attributes):
        self.text_aggregate = []

        if tag_name == "page":
            self.page_redirect, self.page_title, self.page_id = None, None, None
            self.page_ns, self.page_content, self.in_page = None, None, True
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
            if self.page_redirect is None: 
                self.page_info[self.page_id] = {'title': self.page_title, 'ns': self.page_ns, 'content': self.page_content}
            else:
                self.redirect_info[self.page_id] = {'title': self.page_title, 'redirect': self.page_redirect}
        else:
            if self.in_page:
                if self.read_stack[-1] == "page":
                    if tag_name == "title": self.page_title = element_string
                    elif (tag_name == "id") and self.read_stack[-1]: self.page_id = int(element_string)
                    elif tag_name == "ns": self.page_ns = int(element_string)
                elif self.read_stack[-1] == "revision":
                    if tag_name == "text": self.page_content = element_string
                    
    def characters(self, content):
        if self.in_page: self.text_aggregate.append(content)
            

# %% ../nbs/06_parse-wikipedia-dump.ipynb 22
def extract_article_info(page_info):
    processed_info = dict()
    
    for k,v in page_info.items():
        if v['ns'] == 0: 
            page_parsed = wikitextparser.parse(v['content'])

            page_category, page_seealso, page_hyperlinks, page_content = set(), set(), set(), ''
            for section in page_parsed.sections:
                used_section = False
                
                """ extract categories from the page """
                categories = [o.target for o in section.wikilinks if o.target is not None and o.target.startswith("Category:")]
                if len(categories): 
                    page_category.update(categories)
                    used_section = True
    
                """ extract seealso links """
                if section.title is not None and section.title.strip().lower() in ['see also', 'seealso']:
                    seealso = [o.target for o in section.wikilinks]
                    if len(seealso): 
                        page_seealso.update(seealso)
                        used_section = True
    
                """ add page title and content """
                if not used_section:
                    page_content = page_content + " " + section.plain_text()
                    
                    hyperlinks = [o.target.split('#')[0] for o in section.wikilinks if o.target is not None and len(o.target.split('#')[0])]
                    if len(hyperlinks): page_hyperlinks.update(hyperlinks)

            if len(page_category): processed_info.setdefault(k, {}).update({'category': list(page_category)})
            if len(page_seealso): processed_info.setdefault(k, {}).update({'see_also': list(page_seealso)})
            if len(page_hyperlinks): processed_info.setdefault(k, {}).update({'hyper_link': list(page_hyperlinks)})
                
            if k in processed_info: processed_info[k].update({'title':v['title'], 'content': page_content})
                
    return processed_info
    

# %% ../nbs/06_parse-wikipedia-dump.ipynb 25
def main(index_source, articles_source):
    try:
        sorted_stream_offsets = process_index_file(index_source)
        if (sorted_stream_offsets is None) or (len(sorted_stream_offsets) < 1): raise Exception("Index file unsuccessful.")
        
        process_count = multiprocessing.cpu_count()//2
        worker_queue, worker_outputs = multiprocessing.Queue(), multiprocessing.Queue()
        for x in sorted_stream_offsets: worker_queue.put(x)
        for _ in range(process_count): worker_queue.put(None)

        jobs = []
        for i in range(process_count):
            p = multiprocessing.Process(target=process_worker, args=(worker_queue, worker_outputs, articles_source))
            p.start(); jobs.append(p)
            
        num_proc_finished, worker_results = 0, []
        with tqdm(total=len(sorted_stream_offsets)) as pbar:
            while True:
                output = worker_outputs.get()
                if output is None: num_proc_finished += 1
                else: 
                    worker_results.append(output)
                    pbar.update(1)
                if num_proc_finished == process_count: break
            
        for j in jobs: j.join()
            
        return worker_results

    except Exception as e:
        print(e)
        

# %% ../nbs/06_parse-wikipedia-dump.ipynb 27
def combine_info(info):
    page_info, redirect_info = dict(), dict()
    for p,r in tqdm(info):
        page_info.update(p)
        redirect_info.update(r)
    return page_info, redirect_info
    

# %% ../nbs/06_parse-wikipedia-dump.ipynb 28
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--articles_source', type=str, required=True)
    parser.add_argument('--index_source', type=str, default=None)
    parser.add_argument('--cache_dir', type=str, required=True)
    return parser.parse_args()
    

# %% ../nbs/06_parse-wikipedia-dump.ipynb 29
if __name__ == "__main__":
    start_time = timer()
    
    args = parse_args()

    print('Extracting data ...')
    results = main(args.index_source, args.articles_source)

    print('Combining data ...')
    page_info, redirect_info = combine_info(results)

    print('Saving data ...')
    os.makedirs(args.cache_dir, exist_ok=True)
    
    page_file = f'{args.cache_dir}/page_info.joblib'
    joblib.dump(page_info, page_file)

    redirect_file = f'{args.cache_dir}/redirect_info.joblib'
    joblib.dump(redirect_info, redirect_file)
    
    end_time = timer()
    print(f'Total time taken: {end_time - start_time:.3f}.')

