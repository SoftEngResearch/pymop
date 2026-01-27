"""
Direct Python interfaces to Java code from JavaMOP.
"""

import os
import jpype
import jpype.imports
from jpype.types import *

def startJVM() -> None:
    """Starts the JVM, to be called when it's needed.

    Note:
        Since we are using JPype, the JVM can only be started once during the Python program.
    """
    dir_path = os.path.dirname(os.path.realpath(__file__))
    if not jpype.isJVMStarted():
        jpype.startJVM(
            classpath=[
                os.path.join(dir_path, 'java-packages/*'),
                os.path.join(dir_path, 'java-packages/javamop-packages/*'),
                os.path.join(dir_path, 'java-packages/javamop-packages/plugins/*')
            ],
            convertStrings=False
        )

# Ensure the JVM is started at the beginning
startJVM()

# Import Java packages after JVM start
import com.runtimeverification.rvmonitor.logicrepository.plugins.ere as ere
import com.runtimeverification.rvmonitor.logicrepository.plugins.ltl as ltl
import com.runtimeverification.rvmonitor.logicrepository.plugins.fsm as fsm
import com.runtimeverification.rvmonitor.logicrepository.plugins.cfg as cfg
import com.runtimeverification.rvmonitor.logicrepository as logicrepository
import java.lang
import java.io
from jpype.types import *

def invokeLogicPlugin(logic: str, input_string: str) -> str:
    """Invoke JavaMOP logic plugin with a given XML string.

    Refer to JavaMOP's website for the input/output XML formats of logic plugins.

    Args:
        logic (str): The logical formalism of the given input string.
        input_string (str): An XML input string to the logic plugin.

    Returns:
        str: Converted logical formula in XML format.
    """
    # Ensure JVM is started
    startJVM()

    # Select the appropriate plugin
    plugin = None
    if logic == 'ere':
        plugin = ere.EREPlugin()
    elif logic == 'ltl':
        plugin = ltl.LTLPlugin()
    elif logic == 'fsm':
        plugin = fsm.FSMPlugin()
    elif logic == 'cfg':
        plugin = cfg.CFGPlugin()
    else:
        raise ValueError(f'Selected logic "{logic}" is not supported')

    # Process the input string with the selected plugin
    input_stream = java.io.ByteArrayInputStream(JString(input_string).getBytes())
    logic_input_data = logicrepository.LogicRepositoryData(input_stream)
    logic_output_xml = plugin.process(logic_input_data.getXML())
    logic_output_data = logicrepository.LogicRepositoryData(logic_output_xml)

    # Convert the output to a string
    output_string = str(JString(logic_output_data.getOutputStream().toByteArray()))
    return output_string

def shutdownJVM() -> None:
    """Shuts down the JVM, to be called when it's no longer needed.

    Note:
        It is not possible to start the JVM again after it has been shut down.
    """
    if jpype.isJVMStarted():
        jpype.shutdownJVM()
