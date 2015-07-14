__author__ = 'yaorenjie'
import hashlib
import re
import os
import argparse

class Check(object):
    """

    """
    class Offset(object):
        def __init__(self, offset_file_name):
            self._offset_file_name = offset_file_name
            if not os.path.isfile(self._offset_file_name):
                self.init()

        def init(self):
            file(self._offset_file_name, 'w').write('NO_FIRST_LINE_MD5|0')

        def save(self, tag, offset):
            """
            :return:
            """
            file(self._offset_file_name, 'w+').write(tag + '|' + str(offset))

        def read(self):
            """
            :return:
            """
            tag, offset = file(self._offset_file_name).read().split('|')
            return tag, int(offset)

    def __init__(self, file_name, keyword_type, keyword):
        """
        :param file_name:
        :param keyword_type:
        :param keyword:
        :return:
        """
        self._offset = self.Offset(offset_file_name='/tmp/python_log_keyword_check.' + hashlib.md5(keyword).hexdigest())
        self._file = file(file_name)
        self._current_tag, self._current_offset = self._offset.read()
        if self._is_file_rotated():
            self._offset.init()
        self._file.seek(self._current_offset)
        self._generate_keyword_re_pattern(keyword_type, keyword)

    def _generate_keyword_re_pattern(self, keyword_type, keyword):
        """
        :param keyword:
        :return:
        """
        if keyword_type == 'file':
            self._re_pattern = re.compile('(' + '|'.join(file(keyword).readlines()).replace('\n', '') + ')')
        elif keyword_type == 'str':
            self._re_pattern = re.compile(keyword)

    def _line2tag(self, line):
        return line

    def _is_file_rotated(self):
        """
        :return:
        """
        current_tag = self._line2tag(self._read_file_first_line())
        if current_tag == self._current_tag:
            return True
        else:
            self._current_tag = current_tag
            self._current_offset = 0
            return False

    def _read_file_first_line(self):
        tmp_offset = self._file.tell()
        self._file.seek(0)
        first_line = self._file.readline()
        self._file.seek(tmp_offset)
        return first_line.strip()

    def _read_lines(self):
        for line in self._file.read().split('\n'):
            if line == '':
                continue
            yield line

    def _is_re_matched(self, line):
        return True if len(self._re_pattern.findall(line)) > 0 else False

    def process(self):
        lines = self._read_lines()
        for line in lines:
            if self._is_re_matched(line):
                print line
        self._offset.save(self._current_tag, self._file.tell())

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='log file keyword check')
    parser.add_argument('--file', dest='file_name')
    parser.add_argument('--type', dest='keyword_type')
    parser.add_argument('--keyword', dest='keyword')
    args = parser.parse_args()
    c = Check(file_name=args.file_name, keyword_type=args.keyword_type, keyword=args.keyword)
    c.process()
