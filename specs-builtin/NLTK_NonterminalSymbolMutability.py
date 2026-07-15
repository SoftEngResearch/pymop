# ============================== Define spec ==============================
from pythonmop import Spec, call, getKwOrPosArg, TRUE_EVENT, FALSE_EVENT
from nltk import Nonterminal

class NLTK_NonterminalSymbolMutability(Spec):
    """
    When creating a Nonterminal, the provided symbol must be immutable.
    src: https://www.nltk.org/api/nltk.grammar.html
    """

    # a map with object and hash
    seen_hash_values = []
    already_in_monitor = False

    def __init__(self):
        super().__init__()

        @self.event_after(call(Nonterminal, '__init__'))
        def nonterminal_created(**kw):
            # to avoid infinite recursion
            self.already_in_monitor = True
            hash_value = hash(kw['obj'])
            self.already_in_monitor = False

            self.seen_hash_values.append(hash_value)

        @self.event_after(call(Nonterminal, '__hash__'))
        def symbol_mutated(**kw):
            if self.already_in_monitor:
                return FALSE_EVENT

            hash_value = kw['return_val']

            if hash_value not in self.seen_hash_values:
                return TRUE_EVENT
            else:
                self.already_in_monitor = False
                return FALSE_EVENT

    ere = 'nonterminal_created symbol_mutated'
    creation_events = ['nonterminal_created']

    def match(self, call_file_name, call_line_num):
        # TODO:
        print(
            f'Spec - {self.__class__.__name__}: The provided symbol must be immutable. file {call_file_name}, line {call_line_num}.')
# =========================================================================