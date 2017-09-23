import argparse

import yaml


class TextBlock(object):
    def __init__(self, text, tab_replacement='  '):
        """

        :type text: str
        """
        self.text = text.replace('\t', tab_replacement)
        self.lines = self.text.splitlines()
        self.width = max([len(line) for line in self.lines])
        self.padded_width = self.width + 2
        self.height = len(self.lines)

    def get_line(self, item, raise_index_error=False, default=''):
        try:
            return self.lines[item]
        except IndexError:
            if raise_index_error:
                raise
            else:
                return default

    def get_line_justified(self, item, fillchar=' ', raise_index_error=False, default=''):
        return self.get_line(item, raise_index_error, default).ljust(self.width, fillchar)


class RSTFormatter(object):
    @staticmethod
    def any_of_table(blocks):
        """

        :type blocks: list of TextBlock
        """
        HEADER = 'any of'
        cnt = len(blocks)
        # no need table for single content
        if cnt < 2:
            return blocks[0] if blocks else ''
        # width = widths of contents + separators
        width = max((len(HEADER), sum([c.padded_width for c in blocks]))) + (cnt + 1)
        height = max([c.height for c in blocks])
        # rows separators
        top_bar = '+{}+'.format('-' * (width - 2))
        header_bar = '+{}+'.format('+'.join(['=' * c.padded_width for c in blocks]))
        bottom_bar = '+{}+'.format('+'.join(['-' * c.padded_width for c in blocks]))

        header = '|{}|'.format(HEADER.center(width - 2))
        body = '\n'.join(
            ['| {} |'.format(' | '.join([c.get_line_justified(i) for c in blocks])) for i in range(height)])
        return '\n'.join([top_bar,
                          header,
                          header_bar,
                          body,
                          bottom_bar])

    @staticmethod
    def preserve_indents(block):
        """

        :type block: TextBlock
        """
        return '\n'.join(['| {}'.format(line) for line in block.lines])

    @staticmethod
    def title(content, new_line_replacement=' ', tab_replacement='  '):
        prepared_content = content.strip().replace('\n', new_line_replacement).replace('\t', tab_replacement)
        return u'{}\n{}'.format(prepared_content, '=' * len(prepared_content))

    @staticmethod
    def subtitle(content, new_line_replacement=' ', tab_replacement='  '):
        prepared_content = content.strip().replace('\n', new_line_replacement).replace('\t', tab_replacement)
        return u'{}\n{}'.format(prepared_content, '-' * len(prepared_content))

    @staticmethod
    def emphasis(block):
        """

        :type block: TextBlock
        """
        return '\n'.join(['*{}*'.format(line) for line in block.lines])

    @classmethod
    def bullet_list(cls, blocks):
        return '\n'.join([cls._list_item(block) for block in blocks])

    @staticmethod
    def _list_item(block):
        """

        :type block: TextBlock
        """
        return '- ' + '\n  '.join(block.lines)


def format_schema(schema, formatter):
    """

    :param schema: Mapping
    :type formatter: RSTFormatter
    """
    REQUIRED = 'required'
    DEFAULT = 'default'

    def default(_dict):
        return '{}: {}'.format(DEFAULT, _dict.get(DEFAULT))

    def is_required(_dict):
        return _dict.get(REQUIRED, False)

    STANDARD_CONVERTER = lambda _key, content: formatter.preserve_indents(
        TextBlock(yaml.dump({_key: content}, default_flow_style=False)))

    rules_converters = {
        'anyof': lambda _key, content: formatter.any_of_table([TextBlock(yaml.dump(block, default_flow_style=False))
                                                               for block in content])
    }
    options = {}

    for key, value in schema.items():
        # title = formatter.title(key)
        subtitle = formatter.emphasis(TextBlock(REQUIRED)) if is_required(value) \
            else formatter.emphasis(TextBlock(default(value)))
        body = TextBlock(subtitle + '\n' +
                         yaml.dump({k: v for k, v in value.items() if k not in (DEFAULT, REQUIRED)},
                                   default_flow_style=False
                                   ))
        body = '\n'.join([rules_converters.get(k, STANDARD_CONVERTER)(v) for k, v in value])
        options[key] = body

    return '\n'.join(paragraphs)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('schema', help='Path to schema file')
    schema_path = parser.parse_args().schema
    with open(schema_path) as f:
        schema = yaml.load(f)
    document = format_schema(schema, RSTFormatter())


if __name__ == '__main__':
    main()
