from pythonmop.monitor.formalismhandler.base import Base

from typing import Dict, List, Tuple, Set, FrozenSet
import itertools
import nltk
from nltk import CFG
from nltk.parse import RecursiveDescentParser


class Cfg(Base):
    """A class used to store the information of the CFG string structure and verifies if the event string matches the
       CFG string structure.
    """

    def __init__(self, formula: str, parameter_event_map: dict = None, coenable_mode: bool = False,
                 unit_test: bool = False):
        """Initialize the CFG formalism handler with a configuration string.

        Args:
            formula: The CFG string structure string inputted by the user.
            parameter_event_map: The parameter event map to be used for the CFG formalism.
            coenable_mode: The coenable mode to be used for whether to calculate the coenable set or not.
            unit_test: The unit test mode to be used for whether to run the unit test or not.
        """
        # If the unit test mode is True, then skip the whole initialization process.
        if unit_test:
            return

        # Initialize the parent class (base) => Nothing to do.
        super().__init__("", 'cfg', parameter_event_map, coenable_mode)

        # Convert the CFG string to a format that can be parsed by NLTK
        formula = self.convert_cfg(formula)

        # Parse the grammar string into a dictionary and eliminate left recursion before converting back to string
        parsed_grammar = self._parse_grammar(formula)  # Parse the grammar string into a dictionary
        transformed_grammar = self._eliminate_left_recursion(parsed_grammar)  # Eliminate left recursion
        output_grammar = self._format_grammar(transformed_grammar)  # Convert back to string

        # Convert the formatted grammar string back into a CFG object
        cfg = CFG.fromstring(output_grammar)

        # Declare the variable indicating whether coenable set is used
        self.coenable_mode = coenable_mode

        # Calculate the coenable set if it is needed for the CFG handler
        if coenable_mode:
            # Compute the coenable sets for the CFG handler
            self.coenable_set = {}
            self.coenable_set['match'] = self.compute_c_sets(cfg, self.compute_g_sets(cfg))

        # Initialize the parser with the CFG object
        self.parser = RecursiveDescentParser(cfg)

        # Get all productions of CFG structure
        self.productions = self._struct_parser(output_grammar)

        # Filter productions to get only those for the non-terminal 'S'
        self.s_productions = [prod for prod in self.productions if prod.lhs() == nltk.Nonterminal('S')]

        # Store the trace of the event
        self.event_trace = []

    def convert_cfg(self, cfg_formula: str) -> str:
        """Convert the CFG string to a format that can be parsed by NLTK.

        Args:
            cfg_formula: The CFG string structure string inputted by the user.
        """
        # Split the input string into individual productions
        productions = cfg_formula.strip().split('\n')

        # Extract non-terminals by finding the left-hand side of each production
        non_terminals = set()
        for production in productions:
            lhs, _ = production.split('->')
            non_terminals.add(lhs.strip())

        # Function to add single quotes around terminal symbols if not already quoted, excluding 'epsilon' and '|'
        def quote_terminals(production: str) -> str:
            """Add single quotes around terminal symbols if not already quoted, excluding 'epsilon' and '|'.

            Args:
                production: The single-line production string to be processed.
            """
            # Split the production into LHS and RHS
            lhs, rhs = production.split('->')
            lhs = lhs.strip()
            rhs = rhs.strip()

            # Splite the RHS into individual elements and quote terminals if not already quoted
            elements = rhs.split()

            # Process each element to correct the format for NLTK
            processed_elements = []
            for element in elements:
                # Check if element is a terminal symbol
                if element not in non_terminals and element != 'epsilon' and element != '|':
                    # Check if element is already quoted
                    if not (element.startswith("'") and element.endswith("'")):
                        processed_elements.append(f"'{element}'")  # Quote the terminal symbol
                    else:
                        processed_elements.append(element)  # Keep the terminal symbol as is
                else:
                    processed_elements.append(element)  # Keep the non-terminal symbol as is

            # Reconstruct the production with processed elements
            processed_rhs = ' '.join(processed_elements)
            return f'{lhs} -> {processed_rhs}'

        # Apply the quoting function to each production to get the CFG string in the correct format
        quoted_productions = [quote_terminals(production.rstrip(',')) for production in productions]

        # Join the productions back into a single string with the desired format
        return '\n'.join(quoted_productions)

    def _parse_grammar(self, grammar_str: str) -> Dict[str, List[Tuple[str, ...]]]:
        """Parse the grammar string into a dictionary for easier processing.
        Example:
            S -> 'b' S 'b' | 'b' A 'b' | epsilon
            A -> A 'a' | 'a'
        will be parsed into:
            {'S': [('b', 'S', 'b'), ('b', 'A', 'b'), ()], 'A': [('A', 'a'), ('a',)]}

        Args:
            grammar_str: The grammar string inputted by the user.
        """
        # Initialize the grammar dictionary
        grammar = {}

        # Split the grammar string into individual productions
        productions = grammar_str.split('\n')

        # Process each production to extract LHS and RHS
        for production in productions:
            # Split the production into LHS and RHS and strip the whitespace
            lhs, rhs = production.split(' -> ')
            lhs = lhs.strip()
            rhs = rhs.strip()

            # Convert the RHS grammars into a list of tutle for future processing.
            # Handling empty elements marked as epsilon and converting them to empty tuples
            rhs_grammar = []
            rhs_elements = rhs.split(' | ')

            # Process each element in the RHS grammars
            for element in rhs_elements:
                # Check if the element is not epsilon or empty string
                if element.strip() != "epsilon" and element.strip() != "''":
                    # Convert the element into a tuple of strings
                    rhs_grammar.append(tuple(element.strip().split(' ')))
                else:
                    # Add an empty tuple to the list
                    rhs_grammar.append(())

            # Add the processed RHS grammars to the grammar dictionary
            grammar[lhs] = rhs_grammar

        # Return the processed grammar dictionary
        return grammar

    def _eliminate_left_recursion(self, grammar: Dict[str, List[Tuple[str, ...]]]) -> Dict[str, List[Tuple[str, ...]]]:
        """Special function to eliminate left recursion from the grammar dictionary.
        which can cause infinite loops in the NLTK parser (Paull's Algorithm).

        Example:
            S -> S 'a' | 'b'
            will be transformed into:
            S -> 'b' S_added
            S_added -> 'a' S_added | epsilon

        Args:
            grammar: The grammar dictionary to be processed.
        """
        # Declare a dictionary to store the new grammar
        new_grammar = {}

        # Process individual productions in the input grammar
        for lhs, rhs_grammar in grammar.items():

            # Declare two lists to store the productions with and without left recursion
            rhs_with_recursion = []
            rhs_without_recursion = []

            # Separate productions into list with and without left recursion according to the first element of the production
            for rhs in rhs_grammar:
                # Check if the production is left recursive
                if rhs and rhs[0] == lhs:
                    rhs_with_recursion.append(rhs[1:])  # Remove the first element which is left recursive part (α part)
                else:
                    rhs_without_recursion.append(rhs)   # β part

            # If left recursion is found in the production
            if rhs_with_recursion:
                # Create new nonterminal for the recursive part to avoid infinite loops
                new_nonterminal = lhs + "_added"

                # Rewrite the original productions without left recursion (β A' productions)
                new_rhs_grammar = []
                for rhs in rhs_without_recursion:
                    if rhs:
                        # Combined the original RHS with the new nonterminal
                        new_rhs_grammar.append(rhs + (new_nonterminal,))
                    else:
                        # If β is epsilon, just use the new nonterminal
                        new_rhs_grammar.append((new_nonterminal,))

                # Create α A' productions
                new_nonterminal_rhs_grammar = []
                for rhs in rhs_with_recursion:
                    new_nonterminal_rhs_grammar.append(rhs + (new_nonterminal,))
                new_nonterminal_rhs_grammar.append(())  # Add epsilon production

                # Add both sets of productions to the new grammar
                new_grammar[lhs] = new_rhs_grammar
                new_grammar[new_nonterminal] = new_nonterminal_rhs_grammar
            else:
                # If no left recursion, keep productions as is
                new_grammar[lhs] = rhs_grammar

        # Return the new grammar dictionary
        return new_grammar

    def _format_grammar(self, grammar: Dict[str, List[Tuple[str, ...]]]) -> str:
        """Format the grammar dictionary back into a string for easier processing.

        Example:
            {'S': [("'b'", 'S', "'b'"), ("'b'", 'A', "'b'"), ()], 'A': [('A', "'a'"), ("'a'",)]}
            will be converted into:
            S -> 'b' S 'b' | 'b' A 'b' |
            A -> A 'a' | 'a'

        Args:
            grammar: The processed grammar dictionary to be converted back into a string.
        """
        # Declare a list to store the formatted productions
        result = []

        # Process each nonterminal and its productions
        for lhs, rhs_grammar in grammar.items():

            # Process each production in the RHS grammar into a string
            rhs_str = []
            for rhs in rhs_grammar:
                if rhs:
                    rhs_str.append(' '.join(rhs))
                else:
                    rhs_str.append("")

            # Add the formatted production to the result list
            result.append(f"{lhs} -> {'|'.join(rhs_str)}")

        # Return the final formatted grammar string
        return '\n'.join(result)
    
    def compute_g_sets(self, cfg: CFG) -> Dict[str, Set[FrozenSet[str]]]:
        """
        Compute G(X) for all terminals and non-terminals in the given CFG.

        Args:
            cfg (CFG): The context-free grammar parsed using NLTK.

        Returns:
            dict: A dictionary where keys are terminals and non-terminals and values are sets of terminal sequences.
        """
        # Get all productions for the CFG formula
        productions = cfg.productions()

        # Extract non-terminals (set of all LHS of productions) for the CFG formula
        non_terminals = {str(prod.lhs()) for prod in productions}

        # Extract terminals (symbols in RHS that are strings) for the CFG formula
        # If the symbol is a string, then it is a terminal
        terminals = {symbol for prod in productions for symbol in prod.rhs() if isinstance(symbol, str)}

        # Initialize G(X) for the final results
        # For each terminal, add itself in a set to the g_sets
        g_sets = {terminal: {frozenset([terminal])} for terminal in terminals}

        # For each non-terminal, initialize an empty set for further processing
        g_sets.update({non_terminal: set() for non_terminal in non_terminals})

        # Declare a new dictionary to track updates to determine when to stop
        update_status = {}
        for non_terminal in non_terminals:
            update_status[non_terminal] = True

        # Iteratively update the g_sets until no updates are made
        while any(update_status.values()):

            # Check through each non-terminal in the CFG formula
            for non_terminal in non_terminals:

                # Reset the update status for the current non-terminal to False
                update_status[non_terminal] = False

                # Check through each production related to the current non-terminal in the CFG formula
                for prod in productions:
                    if str(prod.lhs()) == non_terminal:

                        # Find all RHS symbols of the current production
                        rhs = prod.rhs()

                        # Base case: all the symbols in the RHS are terminals
                        if all(isinstance(symbol, str) for symbol in rhs):
                            # Combine all the terminals in the RHS to form a new sequence
                            new_seq = frozenset(rhs)
                            if new_seq not in g_sets[non_terminal]:
                                g_sets[non_terminal].add(new_seq)

                                # Update the update status for the current non-terminal to True
                                update_status[non_terminal] = True

                        # Iterative case: some of the symbols in the RHS are non-terminals
                        else:
                            # Declare a new list to store the sets of the RHS symbols
                            sub_sets = []

                            # Check through each symbol in the RHS
                            for symbol in rhs:
                                # If the symbol is a non-terminal, then add its current corresponding set to the sub_sets
                                if isinstance(symbol, nltk.grammar.Nonterminal):
                                    sub_sets.append(g_sets[str(symbol)])

                                # If the symbol is a terminal, then add its current corresponding set to the sub_sets
                                else:
                                    sub_sets.append({frozenset([symbol])})

                            # For each possible combination of sequences from the RHS symbols
                            for sequence in itertools.product(*sub_sets):

                                # Create a new sequence by flattening and combining all sequences
                                combined_seq = frozenset(itertools.chain.from_iterable(sequence))

                                # Add the new sequence to the non-terminal's set if not already present
                                if combined_seq not in g_sets[non_terminal]:
                                    g_sets[non_terminal].add(combined_seq)
                                    update_status[non_terminal] = True

        # Return the final results if no updates are made
        return g_sets


    def compute_c_sets(self, cfg: CFG, g_sets: Dict[str, Set[FrozenSet[str]]]) -> Dict[str, Set[FrozenSet[str]]]:
        """
        Compute C(X) for all terminals and non-terminals in the given CFG based on G(X).
        
        Args:
            cfg (CFG): The context-free grammar parsed using NLTK.
            g_sets (dict): The G-sets computed for all terminals and non-terminals.

        Returns:
            dict: A dictionary where keys are terminals and non-terminals and values are their coenable sets.
        """
        # Initialize C(X) for the final results
        c_sets = {}

        # Add a empty set for each terminal and non-terminal
        for symbol in g_sets:
            c_sets[symbol] = set()

        # Declare a new dictionary to track updates to determine when to stop
        update_status = {}
        for symbol in c_sets:
            update_status[symbol] = True

        # Iteratively update the c_sets until no updates are made
        while any(update_status.values()):

            # Reset the update status for all symbols to False
            for symbol in c_sets:
                update_status[symbol] = False

            # Check through each production in the CFG
            for prod in cfg.productions():
                lhs = str(prod.lhs())  # Left-hand side of the production (A)
                rhs = prod.rhs()  # Right-hand side of the production (β1, x, β2...)

                # If production is of the form A → β1, compute coenable set for β1
                if len(rhs) == 1:

                    # Add all sequences from C(A) to C(β1)
                    for sequence in c_sets[lhs]:
                        if sequence not in c_sets[str(rhs[0])]:
                            c_sets[str(rhs[0])].add(sequence)
                            update_status[str(rhs[0])] = True  # Update the update status for the current non-terminal to True

                # If production is of the form A → β1xβ2, compute coenable set for x
                elif len(rhs) >= 2:

                    # Check through each possible combination of sequences in the RHS
                    for i in range(len(rhs)):

                        # beta1 = rhs[:i]  # Left part before x (discussed in the paper) - not useful
                        x = str(rhs[i])  # The symbol x being evaluated (discussed in the paper)
                        beta2 = rhs[i+1:]  # Right part after x (discussed in the paper)
            
                        # Get the c_set for A and the g_set for β2
                        c_set_A = c_sets[lhs]
                        g_set_beta2 = set()
                        for symbol in beta2:
                            if str(symbol) in g_sets:
                                for sequence in g_sets[str(symbol)]:
                                    g_set_beta2.add(sequence)

                        # Declare a new variable (x) and list for the new sequences to be added to the target variable's c_sets
                        target_variable = x
                        new_sequences = []

                        # Now combine C(A) with G(β2) to find the new sequences to add to C(x)
                        if len(c_set_A) == 0:  # If C(A) is empty, then add all sequences from G(β2) to C(x)
                            for seq_beta2 in g_set_beta2:
                                new_sequences.append(seq_beta2)
                        elif len(g_set_beta2) == 0:  # If G(β2) is empty, then add all sequences from C(A) to C(x)
                            for seq_A in c_set_A:
                                new_sequences.append(seq_A)
                        else:  # If C(A) and G(β2) are not empty, then add all combinations of sequences from C(A) and G(β2) to C(x)
                            for seq_A in c_set_A:
                                for seq_beta2 in g_set_beta2:
                                    new_sequences.append(frozenset(seq_A | seq_beta2))  # Use union instead of '+'

                        # Add the new sequences to C(x)
                        for new_sequence in new_sequences:
                            if new_sequence not in c_sets[target_variable]:
                                c_sets[target_variable].add(new_sequence)
                                update_status[target_variable] = True

        # Return the final results if no updates are made
        return c_sets

    def _struct_parser(self, formula: str) -> List[nltk.grammar.Production]:
        """Parse the structure string into processable structure for future usages.

        Args:
            formula: The CFG string structure string inputted by the user.
        """
        # Convert the formula into a CFG object and return its productions
        grammar = CFG.fromstring(formula)
        return grammar.productions()

    def transition(self, event: str) -> List[str]:
        """Transition the event trace and check if the event matches the CFG.

        Args:
            event: The event to be appended to the event trace.
        """
        # Append the event to the event trace
        self.event_trace.append(event)

        # If the fail status is True, return ['fail'] as the event can no longer match the CFG formula
        if self.fail_status:
            return ['fail']

        # Check if the event matches the CFG formula
        if self._matches_cfg():
            return ['match']
        # If the event does not match the CFG formula, check if it is a prefix of the CFG formula
        else:
            # If the event is not a prefix of the CFG formula, set the fail status to True as the event can no longer match the CFG formula
            if not self._is_prefix_of_cfg():
                self.fail_status = True
                return ['fail']
            # If the event is a prefix of the CFG formula, return an empty list
            else:
                return []

    def _matches_cfg(self) -> bool:
        """Check if the event matches the CFG formula."""
        # Try to parse the string using the parser with the event trace
        try:
            parse_trees = list(self.parser.parse(self.event_trace))

            # If parse_trees is not empty, the string matches the CFG
            return len(parse_trees) > 0

        # If the event does not match the CFG formula, return False
        except ValueError:
            return False

    def _is_prefix_of_cfg(self) -> bool:
        """Check if the event is a prefix of a possible sentence matching the CFG formula."""
        # Get the event trace
        sentence = self.event_trace

        # Check each rhs grammar defined by the S terminal
        for rule in self.s_productions:

            # Initialize the count to calculate the number of words matched with the rhs grammar
            count = 0

            # Get the rhs grammar
            rhs_grammar = rule.rhs()

            # Check each symbol in the rhs grammar
            for element in rhs_grammar:

                # If the count is greater than or equal to the length of the sentence, return True as the sentence is a prefix of the CFG formula
                if count >= len(sentence):
                    return True

                # If the element is a nonterminal, check if the follwing sentence can be matched with the grammar defined by the nonterminal
                if isinstance(element, nltk.grammar.Nonterminal):
                    # Get the number of words matched with the grammar defined by the nonterminal
                    result = self._is_prefix_of_productions(sentence[count:], element)

                    # If the result is 0, break the loop as the sentence is not a prefix of the CFG formula
                    if result == 0:
                        break
                    # If the result is -1, continue the loop without incrementing the count as epsilon is matched in this case
                    elif result == -1:
                        pass
                    # If the result is greater than 0, increment the count by the result
                    else:
                        count += result

                # If the element is a terminal, check if the element matches the sentence
                elif element != sentence[count]:
                    break

                # If the element matches the sentence, increment the count
                else:
                    count += 1

            # If the count is greater than or equal to the length of the sentence, return True as the sentence is a prefix of the CFG formula
            if count >= len(sentence):
                return True

        # If no prefix is found, return False
        return False

    def _is_prefix_of_productions(self, sentence: List[str], in_sym: nltk.grammar.Nonterminal) -> int:
        """Check if the sentence is a prefix of a possible sentence matching the grammar defined by the nonterminal.

        Args:
            sentence: The sentence to be checked.
            in_sym: The nonterminal to be checked.
        """
        # Get the productions defined by the nonterminal
        sym_productions = [prod for prod in self.productions if prod.lhs() == in_sym]

        # Initialize the max count to calculate the number of words matched with the grammar defined by the nonterminal
        max_count = 0

        # Check each rhs grammar defined by the nonterminal
        for rule in sym_productions:

            # Initialize the count to calculate the number of words matched with the rhs grammar
            count = 0

            # Get the rhs grammar
            rhs_grammar = rule.rhs()

            # Special case for epsilon production where the count is set to -1
            if rhs_grammar == ():
                if max_count == 0:
                    max_count = -1
                continue

            # Check each symbol in the rhs grammar
            for element in rhs_grammar:

                # If the count is greater than or equal to the length of the sentence, return the count as the sentence is a prefix of the CFG formula
                if count >= len(sentence):
                    return count

                # If the symbol is a nonterminal, check if the follwing sentence can be matched with the grammar defined by the nonterminal
                if isinstance(element, nltk.grammar.Nonterminal):
                    # Get the number of words matched with the grammar defined by the nonterminal
                    result = self._is_prefix_of_productions(sentence[count:], element)

                    # If the result is 0, break the loop as the sentence is not a prefix of the CFG formula
                    if result == 0:
                        break
                    # If the result is -1, continue the loop without incrementing the count as epsilon is matched in this case
                    elif result == -1:
                        pass
                    # If the result is greater than 0, increment the count by the result
                    else:
                        count += result

                # If the element is a terminal, check if the element matches the sentence
                elif element != sentence[count]:
                    break

                # If the element matches the sentence, increment the count
                else:
                    count += 1

            # Update the max count
            max_count = max(max_count, count)

        # Return the max count
        return max_count
