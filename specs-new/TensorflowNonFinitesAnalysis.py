from pythonmop import Spec, call, VIOLATION
import tensorflow as tf


class TensorflowNonFinitesAnalysis(Spec):
    """
    Checks for NaNs, infs, and -infs in TensorFlow tensors, including SparseTensor and RaggedTensor.
    """

    def __init__(self):
        super().__init__()

        @self.event_after(call(PymopArithmeticOperatorTracker, r'(__pymop__add__|__pymop__sub__|__pymop__mul__|__pymop__truediv__|__pymop__floordiv__|__pymop__mod__|__pymop__pow__|__pymop__lshift__|__pymop__rshift__|__pymop__and__|__pymop__or__|__pymop__xor__)'))
        def non_finite_op_by_arithmetic_operator(**kw):
            args = kw['args'][1:]
            return_val = kw['return_val']
            no_nan_in_input = True
            
            for arg in args:
                if self.check_tf_issue_found(arg):
                    no_nan_in_input = False
                    return {'verdict': VIOLATION, 
                            'custom_message': f"Non-finite value found in argument at {kw['call_file_name']}, {kw['call_line_num']}.",
                            'filename': kw['call_file_name'],
                            'lineno': kw['call_line_num']}
            
            if self.check_tf_issue_found(return_val):
                if no_nan_in_input:
                    return {'verdict': VIOLATION, 
                            'custom_message': f"Non-finite value found in argument at {kw['call_file_name']}, {kw['call_line_num']}.",
                            'filename': kw['call_file_name'],
                            'lineno': kw['call_line_num']}

        @self.event_before(call(PymopFuncCallTracker, 'after_call'))
        def non_finite_op(**kw):
            return_val = kw['args'][1]
            args = kw['args'][3]
            kwargs = kw['args'][4]
            no_nan_in_input = True
            
            for arg in args:
                if self.check_tf_issue_found(arg):
                    no_nan_in_input = False
                    return {'verdict': VIOLATION, 
                            'custom_message': f"Non-finite value found in argument at {kw['call_file_name']}, {kw['call_line_num']}.",
                            'filename': kw['call_file_name'],
                            'lineno': kw['call_line_num']}
            
            for arg in kwargs:
                if self.check_tf_issue_found(arg):
                    no_nan_in_input = False
                    return {'verdict': VIOLATION, 
                            'custom_message': f"Non-finite value found in argument at {kw['call_file_name']}, {kw['call_line_num']}.",
                            'filename': kw['call_file_name'],
                            'lineno': kw['call_line_num']}
            
            if self.check_tf_issue_found(return_val):
                if no_nan_in_input:
                    return {'verdict': VIOLATION, 
                            'custom_message': f"Non-finite value found in argument at {kw['call_file_name']}, {kw['call_line_num']}.",
                            'filename': kw['call_file_name'],
                            'lineno': kw['call_line_num']}

    # Copied as is from https://github.com/sola-st/DyLin/blob/820506e532000edaa76f22f55ba94323006b2405/src/dylin/analyses/TensorflowNonFinitesAnalysis.py#L14
    def check_contains_nan_or_inf(self, tensor: tf.Tensor) -> bool:
        try:
            # checks if tensor contains NaN / inf / -inf by throwing an exception
            tf.debugging.check_numerics(tensor, "")
        except Exception as e:
            try:
                # Some uncommon exceptions for e can be thrown which do not
                # contain a message attribute as expected
                if "Tensor had" in e.message:
                    return True
            except Exception:
                return False
        return False
    
    def check_tf_issue_found(self, value: any) -> bool:
        if isinstance(value, tf.Tensor) and tf.is_tensor(value) and self.check_contains_nan_or_inf(value):
            return True
        return False

    def match(self, call_file_name, call_line_num):
        print(
            f'Spec - {self.__class__.__name__}: Non-finite value detected in tensor. '
            f'File {call_file_name}, line {call_line_num}.')
# =========================================================================

'''
spec_instance = TensorflowNonFinitesAnalysis()
spec_instance.create_monitor("D")


# Test cases
a = tf.constant([float("nan")])  # Should trigger
b = tf.Variable([float("inf")])  # Should trigger
c = tf.ones((2, 2)) / tf.constant([0.0])  # Should trigger
d = tf.zeros((2, 2)) + tf.constant([float("-inf")])  # Should trigger

# SparseTensor doesn't
# work (tf.debugging.check_numeric function doesn't throw the expected
# exception that indicates the usage of nan or inf)
e = tf.SparseTensor(indices=[[0, 0], [1, 2]], values=[float("nan"), 1.0], dense_shape=[2, 3])  # Should trigger [For some reason it doesn't work]

f = tf.RaggedTensor.from_row_lengths([float("inf"), 1.0, 2.0], [2, 1])  # Should trigger
'''