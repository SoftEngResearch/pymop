"""Defines dataclasses used as options for declaring spec events.
"""

from dataclasses import dataclass, field
from typing import Any, Tuple, Iterator
import weakref
import itertools

# ============================
# BUILTIN MODULES
# used to keep a referance to
# the original modules as they
# may be overriden by some specs
# ============================
OriginalList = list


# ============================
# CONSTANTS DECLARERS
# ============================
FALSE_EVENT = 123321132
TRUE_EVENT = 999999
VIOLATION = 8888888


# ============================
# HELPERS INSTRUMENTED METHODS
# ============================
class End:
    """
    End the execution of the program.
    """
    def end_execution(self):
        """
        usage: @self.event_after(call(End, 'end_execution'))
        """
        pass


# ============================
# PARAMETER INSTANCE DECLARERS
# ============================

@dataclass(frozen=True)  # hashable dataclass
class SpecParameter:
    """Represents a unique spec parameter and its type.

    Instances of ``SpecParameter`` are returned by the ``Spec.param()`` method,
    and should **not** be instantiated manually.
    """

    #: Identifier used internally to differentiate spec parameters.
    id: int

    #: The type of the values represented by this parameter.
    param_type: type = Any

    # The weak ref for this parameter.
    param_weak_ref: weakref = None

    # Customized function for comparison.
    def __lt__(self, other):
        if not isinstance(other, SpecParameter):
            return NotImplemented

        return str(self.param_type) < str(other.param_type)

    def __repr__(self):
        try:
            # some types don't have __name__ attribute
            return f'{self.param_type.__name__}-{self.id}'
        except AttributeError:
            return f'{self.param_type}-{self.id}'

    def __hash__(self) -> int:
        """Hash function for SpecParameter.

        Returns:
            The hash value of the SpecParameter instance.
        """
        return hash(self.id)

# ===============================
# PARAMETER COMBINATION DECLARERS
# ===============================

@dataclass(frozen=True)  # hashable dataclass
class SpecCombination:
    """Represents a unique spec parameter combination.

    This spec parameter combination is used to represent the parameter combination of the specification in addition to the tuple commonly used in the implementation.
    It would contains extra information such as the spec parameter type, less informative parameter combination to avoid redundant calculation.
    """
    spec_params: Tuple[SpecParameter, ...]
    spec_params_type: frozenset[type] = field(init=False)
    spec_params_type_set: set[type] = field(init=False)
    possible_sub_params: Tuple[Tuple[SpecParameter, ...]] = field(init=False)

    def __post_init__(self):
        # Convert set to frozenset to make it hashable
        object.__setattr__(self, 'spec_params_type', frozenset(param.param_type for param in self.spec_params))
        object.__setattr__(self, 'spec_params_type_set', set(self.spec_params_type))

        # Calculate possible sub params once at initialization
        sub_params = tuple(self.find_possible_sub_params(self.spec_params))
        object.__setattr__(self, 'possible_sub_params', sub_params)

    def __hash__(self):
        return hash((self.spec_params, self.spec_params_type, self.possible_sub_params))
    
    def __eq__(self, other):
        if not isinstance(other, SpecCombination):
            return NotImplemented
        return self.spec_params == other.spec_params and self.spec_params_type == other.spec_params_type and self.possible_sub_params == other.possible_sub_params

    def get_spec_param_type(self):
        """Get the types of the spec parameters.

        Returns:
            The types of the spec parameters.
        """
        return self.spec_params_type_set
    
    def find_possible_sub_params(self, processing_params: Tuple[SpecParameter, ...]) -> Iterator[Tuple[SpecParameter]]:
        """Generate all the possible parameter combinations that are less informative than the processing one.

        Args:
            processing_params: The parameter combination that is being processed.
        Returns:
            The possible parameter combinations that are less informative than the processing one.
        """
        # Generate all the possible combinations (starting from longest to shortest).
        for possible_length in range(len(processing_params) - 1, 0, -1):
            for possible_param in itertools.combinations(processing_params, possible_length):
                yield possible_param

        # Check if the processing parameter combination is empty.
        if not len(processing_params) == 0:
            # Generate the null combination in the end if not.
            yield ()

    def get_possible_sub_params(self) -> Tuple[Tuple[SpecParameter, ...]]:
        """Get all possible parameter combinations that are less informative than this one.
        
        Returns:
            A frozenset of parameter combinations that are less informative.
        """
        return self.possible_sub_params


# =============================
# EVENT INSTRUMENTATION TARGETS
# =============================

@dataclass
class BaseInstrumentTarget:
    """Represents a function which can be instrumented.
    """

    #: The module, class, or object which contains the function to be instrumented.
    namespace: Any

    #: The name of the function/property to be instrumented. Maybe a simple RegEx pattern.
    field: str


@dataclass
class call(BaseInstrumentTarget):
    """Represents callable function(s).

    Example:
        To represent the function ``threading.Thread.start()``::

            from pythonmop import call
            import threading
            ...
            call(threading.Thread, 'start')
    
    Example:
        To represent functions ``bisect.bisect_left()``,
        ``bisect.bisect_right()``, and ``bisect.bisect()``::

            from pythonmop import call
            import bisect
            ...
            call(bisect, 'bisect*') # "*" RegEx operator matches to any string
    """
    pass


@dataclass
class getter(BaseInstrumentTarget):
    """Represents property getter(s).

    Python property getters are functions, and can be instrumented as such.

    Example:
        Represent the getter of ``threading.Thread.daemon``::

            from pythonmop import getter
            import threading
            ...
            getter(threading.Thread, 'daemon') # This instrumentation target...
            ...
            my_thread = threading.Thread()
            print(my_thread.daemon) # ...represents "get" operations like this
    """
    pass


@dataclass
class setter(BaseInstrumentTarget):
    """Represents property setter(s).

    Python property setters are functions, and can be instrumented as such.

    Example:
        Represent the setter of ``threading.Thread.daemon``::

            from pythonmop import setter
            import threading
            ...
            setter(threading.Thread, 'daemon') # This instrumentation target...
            ...
            my_thread = threading.Thread()
            my_thread.daemon = True # ...represents "set" operations like this
    """
    pass


@dataclass
class deleter(BaseInstrumentTarget):
    """Represents property deleter(s).

    Python property deleters are functions, and can be instrumented as such.

    Example:
        Represent the deleter of ``threading.Thread.daemon``::

            from pythonmop import deleter
            import threading
            ...
            deleter(threading.Thread, 'daemon') # This instrumentation target...
            ...
            my_thread = threading.Thread()
            del my_thread.daemon # ...represents "del" operations like this
    """
    pass


# =========================
# EVENT PARAMETER DECLARERS
# =========================

@dataclass
class BaseParameterDeclaration:
    """Declares that a given spec parameter is used in an event.
    """

    #: Spec parameter object.
    param: SpecParameter


@dataclass
class target_param(BaseParameterDeclaration):
    """Sets the spec parameter to the target of function calls.
    """
    pass


@dataclass
class ret_param(BaseParameterDeclaration):
    """Sets the spec parameter to the return value of function calls.
    """
    pass

# TODO: Add an arg_param() dataclass for setting a spec parameter to an argument
