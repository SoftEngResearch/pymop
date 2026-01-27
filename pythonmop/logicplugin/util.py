"""
Utility functions for logic plugins.
"""

from typing import Optional, List, Dict, Set, FrozenSet
import re
import xml.etree.ElementTree as ET

def parseXMLOutput(xml_str: str) -> Dict:
    """Parse an XML string from the output of a logic plugin.

    Args:
        xml_str (str): String containing XML value.

    Returns:
        dict: Dictionary of parsed data.
    """
    logic_data = {
        'logic': None,
        'formula': None,
        'events': None,
        'categories': None,
        'minimizedFSM': None
    }

    root = ET.fromstring(xml_str)
    for mop_field in root:

        # Find the first level tag and text
        tag = mop_field.tag
        text = mop_field.text.strip() if mop_field.text else ""

        # Add the value of XML to the dict
        if tag == 'Events':
            logic_data['events'] = text.split()
        elif tag == 'Categories':
            logic_data['categories'] = text.split()
        elif tag == 'Property':
            for property_field in mop_field:

                # Find the second level tag and text
                property_tag = property_field.tag
                property_text = property_field.text.strip() if property_field.text else ""

                # Add the value of XML to the dict
                if property_tag == 'Logic':
                    logic_data['logic'] = property_text.lower()
                elif property_tag == 'Formula':
                    logic_data['formula'] = property_text

        elif tag == 'EnableSets':
            if logic_data['logic'] == 'cfg':
                lines = text.split('\n')
                logic_data['enableSet_match'] = (parse_enable_sets(lines[1]))
            # TODO: Add enable set calculation for ERE, LTL and FSM.
        elif tag == 'Message' and text.startswith('MINIMIZED:'):
            logic_data['minimizedFSM'] = text[10:].strip()

    return logic_data

def parse_enable_sets(enable_sets_content: str) -> Dict[str, Set[FrozenSet[str]]]:
    """Parse the EnableSets content into a dictionary, handling any number of sets for each event.

    Args:
        enable_sets_content (str): String containing the enable sets.

    Returns:
        Dict[str, Set[FrozenSet[str]]]: Parsed enable sets.
    """
    enable_sets_dict = {}

    # Regex pattern to match the enable sets format with any number of sets
    pattern = re.compile(r'(\w+)=\[\[(.*?)\]\]')

    # Find all matches in the enable sets content
    matches = pattern.findall(enable_sets_content)

    for match in matches:
        event = match[0]
        sets_content = match[1]
        # Split the overall sets content by '], [' to separate individual sets
        raw_sets = sets_content.split('], [')

        parsed_sets = set()
        for raw_set in raw_sets:
            # Remove leading '[' and trailing ']' from each raw set
            raw_set = raw_set.strip('[]')
            # Split the set by commas and strip whitespace
            set_items = [item.strip() for item in raw_set.split(',')] if raw_set else []
            # Create a frozen set from the items
            frozen_set = frozenset(set_items)
            # Add the frozen set to the event's parsed sets
            parsed_sets.add(frozen_set)

        # Add the event and its sets to the dictionary
        enable_sets_dict[event] = parsed_sets

    return enable_sets_dict

def generateXMLInput(logic: str, formula: str, events: List[str], categories: Optional[List[str]] = None) -> str:
    """Generate XML input string for JavaMOP logic plugin.

    Args:
        logic (str): Logical formalism.
        formula (str): Logical formula.
        events (List[str]): List of events in the formula.
        categories (Optional[List[str]]): For FSM, a list of states.

    Returns:
        str: XML string which can be used as input for a JavaMOP logic plugin.
    """
    # If logic is FSM and categories aren't given, parse categories
    logic = logic.lower()
    if logic == 'fsm' and categories is None:
        categories = FSMParseCategories(formula)

    # Generate XML tree
    root = ET.Element('mop')

    # Add events
    events_elem = ET.Element('Events')
    events_elem.text = ' '.join(events)
    root.append(events_elem)

    # Add categories
    if categories is not None:
        categories_elem = ET.Element('Categories')
        categories_elem.text = ' '.join(categories)
        root.append(categories_elem)

    # Add logic and formula
    logic_elem = ET.Element('Logic')
    logic_elem.text = logic
    formula_elem = ET.Element('Formula')
    formula_elem.text = formula.strip() if logic == 'cfg' else formula
    property_elem = ET.Element('Property')
    property_elem.append(logic_elem)
    property_elem.append(formula_elem)
    root.append(property_elem)

    return ET.tostring(root, encoding='utf-8').decode('utf-8')

def FSMParseCategories(formula: str) -> List[str]:
    """Parse categories from an FSM formula.

    Args:
        formula (str): FSM formula.

    Returns:
        List[str]: List of states/categories.
    """
    categories = []
    formula = decodeArrows(formula)
    tokens = formula.split()
    for i in range(len(tokens)):
        if tokens[i] == '[':
            # A token before an open square bracket is a category.
            # e.g. mystate [
            categories.append(tokens[i - 1])
        elif tokens[i][-1] == '[':
            # A token which ends with an open square bracket contains a
            # category. e.g. mystate[
            categories.append(tokens[i][:-1])
    return categories
    
def decodeArrows(formula: str) -> str:
    """Decode HTML encoded arrows.

    Args:
        formula (str): Formula string.

    Returns:
        str: Formula string with decoded arrows.
    """
    # Replace HTML encoded arrows with symbols
    return formula.replace("&gt;", ">").replace("&lt;", "<")
