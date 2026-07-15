# ============================== Define spec ==============================
from pythonmop import Spec, call, TRUE_EVENT, FALSE_EVENT
from string import Template


class StringTemplate_ChangeAfterCreate(Spec):
    """
    Note further that you cannot change the delimiter after class creation
    (i.e. a different delimiter must be set in the subclass’s class namespace).
    src: https://docs.python.org/3/library/string.html#string.Template.template
    """

    def __init__(self):
        super().__init__()
        self.created_classes_delimier = {}  # key: class, value: delimiter

        @self.event_before(call(Template, '__init__'))
        def class_creation(**kw):
            obj = kw['obj']
            self.created_classes_delimier[obj] = obj.delimiter

        @self.event_before(call(Template, 'substitute'))
        def call_substitute(**kw):
            return check_change(**kw)

        @self.event_before(call(Template, 'safe_substitute'))
        def call_safe_substitute(**kw):
            return check_change(**kw)

        def check_change(**kw):
            obj = kw['obj']
            if obj in self.created_classes_delimier:
                if obj.delimiter != self.created_classes_delimier[obj]:
                    return TRUE_EVENT

            return FALSE_EVENT

    ere = 'class_creation (call_safe_substitute | call_substitute)+'
    creation_events = ['class_creation']

    def match(self, call_file_name, call_line_num):
        print(
            f'Spec - {self.__class__.__name__}: Note further that you cannot change the delimiter after class creation.'
            f'file {call_file_name}, line {call_line_num}.')


# =========================================================================
'''
spec_instance = StringTemplate_ChangeAfterCreate()
spec_instance.create_monitor("StringTemplate_ChangeAfterCreate")


# Create a template with a custom delimiter
class MyTemplate(Template):
    delimiter = '%'


# Change the delimiter
template = MyTemplate('Hello')
template.substitute(who='world')

MyTemplate.delimiter = '#'
template.substitute(who='world')
template.safe_substitute()
'''