from enum import EnumMeta


class Column(object):

    def __init__(self, col_type=str, index=False, pk=False, composite=False, enum=None, required=False):
        self.col_type = col_type
        self.index = index
        self.pk = pk
        self.composite = composite
        self.enum = enum
        self.required = required or pk
        if enum:
            assert isinstance(enum, EnumMeta), enum
            self.enum_choices = set([x.value for x in enum])
        else:
            self.enum_choices = set()
