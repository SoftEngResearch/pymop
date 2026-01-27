"""Logic plugins for converting logical formulas.

Example:
    Converting an ERE formula into FSM::

        ere = EREData(formula='(a b)* ~(b ~(a b))', events=['a', 'b'])
        fsm_formula = EREData.toFSM().formula
    
Example:
    Minimizing an FSM formula::

        # fsm = FSMData(...)
        
        fsm_min = fsm.minimized()
"""

from pythonmop.logicplugin import util
from pythonmop.logicplugin import javamop
from typing import Optional, List, TypeVar, Dict, Set, FrozenSet

FSMDataType = TypeVar('FSMDataType', bound='FSMData')

class FSMData:
    """Represents an FSM formula.
    """

    def __init__(self, formula: str, events: List[str], states: Optional[List[str]] = None):
        #: FSM formula.
        self.formula = formula

        #: List of events.
        self.events = events

        #: List of possible states in FSM.
        self.states = states
        if self.states is None:
            self.states = util.FSMParseCategories(self.formula)
    
    def minimized(self) -> FSMDataType:
        """Creates a minimized version of itself.

        Returns:
            Minimized FSM formula.
        """
        xmlInput = util.generateXMLInput('fsm', self.formula, self.events, self.states)
        xmlOutput = javamop.invokeLogicPlugin('fsm', xmlInput)
        data = util.parseXMLOutput(xmlOutput)
        return FSMData(data['minimizedFSM'], data['events'], data['categories'])

class EREData:
    """Represents an ERE formula.
    """
    
    def __init__(self, formula: str, events: List[str]):
        #: ERE formula.
        self.formula = formula

        #: List of events.
        self.events = events

    def toFSM(self) -> FSMData:
        """Creates an FSM version of itself.

        Returns:
            FSM formula corresponding to this ERE formula.
        """
        xmlInput = util.generateXMLInput('ere', self.formula, self.events)
        xmlOutput = javamop.invokeLogicPlugin('ere', xmlInput)
        data = util.parseXMLOutput(xmlOutput)
        return FSMData(data['formula'], data['events'], data['categories'])

class LTLData:
    """Represents an LTL formula.
    """
    
    def __init__(self, formula: str, events: List[str]):
        #: LTL formula.
        self.formula = formula

        #: List of events.
        self.events = events
    
    def toFSM(self) -> FSMData:
        """Creates an FSM version of itself.

        Returns:
            FSM formula corresponding to this LTL formula.
        """
        xmlInput = util.generateXMLInput('ltl', self.formula, self.events)
        xmlOutput = javamop.invokeLogicPlugin('ltl', xmlInput)
        data = util.parseXMLOutput(xmlOutput)
        return FSMData(data['formula'], data['events'], data['categories'])


class CFGData:
    """Represents an CFG formula.
    """

    def __init__(self, formula: str, events: List[str], enableSet: Dict[str, Set[FrozenSet[str]]] = None):
        #: CFG formula.
        self.formula = formula

        #: List of events.
        self.events = events

        # Dict of enable set
        self.enableSet = enableSet

    def toFSM(self):
        """Creates an FSM version of itself.

        Returns:
            FSM formula corresponding to this ERE formula.
        """

        categories = ['match']
        xmlInput = util.generateXMLInput('cfg', self.formula, self.events, categories)
        xmlOutput = javamop.invokeLogicPlugin('cfg', xmlInput)
        data = util.parseXMLOutput(xmlOutput)
        return CFGData(data['formula'], data['events'], data['enableSet_match'])
