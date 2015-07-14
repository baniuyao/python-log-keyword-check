__author__ = 'baniu.yao@gmail.com'
import hashlib
import re
import os
import argparse

class LogKeywordCheck(object):
    """ A simple tool to check if keywords exist in log files.
    This tool is able to read file at the position it read last time and
    it can read keyword from file and command line args.

    """
    class Offset(object):
        """An internal class which is the abstract of offset

        """
        def __init__(self, offset_file_name):
            """Constructor for Offset, with offset_file_name

            Offset file only has one line like below:
            FILE_FIRST_LINE_MD5|100

            FILE_FIRST_LINE_MD% is used to judge if a log file is rotated
            and '100' here means the offset. The offset is calculated by
            'file.tell()'.

            :param offset_file_name: file_name for store offset info
            :return: None
            """
            self._offset_file_name = offset_file_name
            if not os.path.isfile(self._offset_file_name):
                self.init()

        def init(self):
            """Init offset_file name with default value
            :return: None
            """
            file(self._offset_file_name, 'w').write('NO_FIRST_LINE_MD5|0')

        def save(self, tag, offset):
            """ Save tag and offset into offset file

            :return: None
            """
            file(self._offset_file_name, 'w+').write('|'.join([tag, str(offset)]))

        def read(self):
            """ Read tag and offset from offset file
            :return: (tag, offset)
            """
            tag, offset = file(self._offset_file_name).read().split('|')
            return tag, int(offset)

    def __init__(self, file_name, keyword_type, keyword):
        """ Construction for LogKeywordCheck
        :param file_name: File to check
        :param keyword_type: this can be 'str' or 'file'.
        :param keyword: keywords conf file or a regex pattern
        :return: None
        """
        self._id = hashlib.md5(file_name + keyword_type + keyword).hexdigest()
        self._offset = self.Offset(offset_file_name='/tmp/log_keyword_check.' + self._id)
        self._file = file(file_name)
        self._current_tag, self._current_offset = self._offset.read()
        if self._is_file_rotated():
            self._offset.init()
        self._file.seek(self._current_offset)
        self._generate_keyword_re_pattern(keyword_type, keyword)

    def _generate_keyword_re_pattern(self, keyword_type, keyword):
        """ Generate regex pattern for fast matching
        :param keyword: keysord pattern
        :return: None
        """
        if keyword_type == 'file':
            self._re_pattern = re.compile('(' + '|'.join(file(keyword).readlines()).replace('\n', '') + ')')
        elif keyword_type == 'str':
            self._re_pattern = re.compile(keyword)

    def _line2tag(self, line):
        """ Convert line string into md5 to simplify the comparison of tag.
        :param line: input string
        :return: MD5_STRING
        """
        return hashlib.md5(line).hexdigest()

    def _is_file_rotated(self):
        """ Judge if the file has been rotated before. Log file only has append operation,
        so the first line of log file can be the tag of one certain log file. If the tag
        has changed, the log file has been rotated.
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
        """ Read the first line of file. The first line is used to judge
        if the file has been rotated

        :return: None
        """
        tmp_offset = self._file.tell()
        self._file.seek(0)
        first_line = self._file.readline()
        self._file.seek(tmp_offset)
        return first_line.strip()

    def _read_lines(self):
        """ Simple wrapper of file.read(). This function only does the strip() job.

        :return: line
        """
        for line in self._file.read().split('\n'):
            if line == '':
                continue
            yield line

    def _is_re_matched(self, line):
        """ This function is used to tell if the regex pattern has found matched string.

        :param line:
        :return: True/False
        """
        return True if len(self._re_pattern.findall(line)) > 0 else False

    def process(self):
        """ Main process which is invoked by __main__

        :return: None
        """
        lines = self._read_lines()
        error_lines = []
        for line in lines:
            if self._is_re_matched(line):
                error_lines.append(line)
        self._offset.save(self._current_tag, self._file.tell())
        if len(error_lines) > 0:
            print '\n'.join(error_lines)
        else:
            print 0

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='log file keyword check')
    parser.add_argument('--file', dest='file_name', required=True,
                        help='file to check')
    parser.add_argument('--type', dest='keyword_type', choices=['str', 'file'], required=True,
                        help='keyword type, str or file')
    parser.add_argument('--keyword', dest='keyword', required=True, nargs='+',
                        help='keyword conf file or keyword re pattern')
    args = parser.parse_args()
    """ If --keyword has more than one keyword, codes below will compose them into regex pattern
    like '(KEYWORD_1|KEYWORD_2|KEYWORD_3|...)'
    """
    if len(args.keyword) > 1:
        keyword = '(' + '|'.join(args.keyword) + ')'
    else:
        keyword = args.keyword[0]
    lkc = LogKeywordCheck(file_name=args.file_name, keyword_type=args.keyword_type, keyword=keyword)
    lkc.process()
