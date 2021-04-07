import os
import re
import textwrap
import sys
from pathlib import Path

import requests
from lxml import html

import config


class GetData(object):
    __slots__ = ('obj_parser', 'url')

    def __init__(self, url: str) -> None:
        self.url = url
        self.obj_parser = None

    def get(self):
        try:
            get = requests.get(self.url)
            parsed_body = html.fromstring(get.text)

            params = config.content
            self.obj_parser = parsed_body.xpath(params)
            return True, self.obj_parser
        except Exception as err:
            return False, err

    def edit_link(self):
        domain = config.domain
        url = [self.url[:self.url.find(d)]+d for d in domain if d in self.url]
        return url[0]


class Files(GetData):
    __slots__ = ('make_dir')

    def __init__(self, url: str) -> None:
        GetData.__init__(self, url)
        self.make_dir = self.__make_path()

    def save_content(self, content: str) -> bool:
        try:
            path_file = re.sub('https://', '', self.url)
            # save symbol '/' in filename
            path_file = re.sub('/', u'\u2215', path_file)
            if self.make_dir is not None:
                path_file = f'{self.make_dir}/{path_file[:-1]}.txt'
            if self.make_dir is None:
                path_file = f'{path_file[:-1]}.txt'

            with open(file=path_file, mode='w') as f:
                f.write(content)
        except Exception as err:
            return False, err

    def __make_path(self):
        path = config.path_content
        try:
            if len(path) == 0:
                path = str(Path().absolute()) + '/'
                path = path.replace("\\", '/')
                # check domain in url
                new = self.edit_link()
                # Deleted by template 'https://'
                new = '{0}{1}/'.format(path, new.replace('https://', ''))
                os.makedirs(new)
                return new
            elif len(path) > 0:
                os.makedirs(path)
                return path
        except FileExistsError as err:
            if '183' in str(err):
                return new
            else:
                raise f'FileExistsError:{err}'


class TrueContent(GetData):
    __slots__ = ('__content')

    def __init__(self, url: str) -> None:
        GetData.__init__(self, url)
        self.obj_parser = self.get()[1]
        paragraph, links = self.__get_content(self.obj_parser)
        all_text = self.__add_links(paragraph, links)
        self.__content = self.__line_width(all_text)

    def __get_content(self, parser_obj: list) -> tuple:
        paragraphs = []     # content (all text)
        text_link = []      # text and link
        for i in parser_obj:
            if isinstance(i, html.HtmlElement):
                paragraphs.append(i.text_content())
            elif isinstance(i, html.etree._ElementUnicodeResult):
                result = str(i)
                if 'http' not in result:
                    template_link = self.edit_link()
                    link = f'{template_link}{i}'
                    text_link.append(f" [{link}]")
                elif 'http' in result:
                    text_link.append(f" [{i}]")
                else:
                    text_link.append(f" {i}")
        return paragraphs, text_link

    def __add_links(self, paragraphs: list, links: list) -> str:
        any_links = links[::2]  # links
        del links[::2]          # delete links
        links_word = links      # words next to the link

        edits = [num for num, p in enumerate(paragraphs) if [
            i for i in links_word if i in p]]
        for num in edits:
            for num_word, i in enumerate(links_word):
                paragraphs[num] = re.sub(
                    i, f'{i}{any_links[num_word]}', paragraphs[num])
        # last link and words
        paragraphs[-1] = f'{paragraphs[-1]}{any_links[-1]}'
        return paragraphs

    def __line_width(self, all_text: list) -> str:
        for num, i in enumerate(all_text):
            swap = '\n'.join(textwrap.wrap(i, width=80))
            all_text[num] = swap + '\n'
        return '\n'.join(all_text)

    def get_content(self):
        return self.__content


if __name__ == '__main__':
    if len(sys.argv) > 1:
        args = sys.argv[1:]
        for arg in args:
            init_content = TrueContent(arg)
            content = init_content.get_content()
            save = Files(arg).save_content(content)
