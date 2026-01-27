# Function Call Instrumentation in Python

## The Problem

We want to receive events before and after any arbitrary function is called, capturing the following information:

- The function itself
- The positional parameters
- The keyword parameters
- The filename
- The line number
- The column offset

## Potential Solutions

### A. Monkey patching based approaches

These approaches generally do not work with native code (modules written in C).

### B. AST based approaches

> **Note:** `...` is used below to denote arbitrary arguments (positional or keyword). For example, `some_function(1, 2, a, b, c=d, e=other_func())` is simplified to `some_function(...)`.

#### 1. Replace the function call with a call to a wrapper function

**The instrumentation logic:**

```python
def get_wrapper(func):
    def wrapper_func(*args, **kwargs):
        # BEFORE CALL EVENT with func, args, and kwargs
        result = func(*args, **kwargs)
        # AFTER CALL EVENT with result, func, args, and kwargs
        return result
    return wrapper_func

# The original function
some_function(...)

# The instrumentation
get_wrapper(some_function)(...)

```

**Critique:**
This works in some cases but does not generalize well when instrumenting dependencies. Some functions depend on the call stack and their original context. When called within a wrapper, they may fail. One example is `eval`:

```python
def other_func(f):
    return eval('f+2') # Here eval finds the value of f from the stack

```

To solve this, we must call the function within its original context. This is possible if we wrap the _arguments_ with a pass-through function (for the "before" event) and the _function call itself_ with another pass-through (for the "after" event).

#### 2. Wrap the arguments and return value

**The instrumentation logic:**

```python
def before_call(func, *args, **kwargs):
    # BEFORE CALL EVENT with func, args, and kwargs
    return (*args, **kwargs)

def after_call(func, result):
    # AFTER CALL EVENT with result [we lost args, and kwargs]
    return result

# The original function
some_function(...)

# The instrumentation
after_call(
    some_function,
    some_function(
        before_call( # Should return ... (but this is the problem)
            some_function,
            ...
        )
    ),
)

```

**Critique:**
This approach fails because the syntax to unpack arguments differs depending on whether they are positional or keyword-based.

```python
some_function(a, b, c) # <-- Original using only pos args
some_function(*before_call(a, b, c)) # <-- Can be transformed

some_function(a=x, b=y, c=z) # <-- Original using only kwargs
some_function(**before_call(a=x, b=y, c=z)) # <-- Can be transformed

some_function(a, b=y, c=z) # <-- Original using both
some_function(***before_call(a, b=y, c=z)) # <-- NOPE!

```

There is no `***` operator in Python. A workaround is to use separate hooks for args and kwargs:

```python
some_function(a, b=y, c=z)
some_function(
    *before_args_call(a),
    **before_kwargs_call(b=y, c=z),
)

```

However, this splits the "before" event into two. We can attempt to fix this during instrumentation:

```python
def before_call_args(func, has_kwargs, args):
    if not has_kwargs:
        # BEFORE CALL EVENT with func and args [no kwargs :(]
        pass
    else:
        # Kwargs will emit the event
    return args

def before_call_kwargs(func, kwargs):
    # BEFORE CALL EVENT with func and kwargs [no args :(]
    return kwargs

# The original function
some_function(a, b, c=d)

# The instrumentation
after_call(
    some_function,
    some_function(
        *before_call_args(
            some_function,
            (a, b)
        ),
        **before_call_kwargs(
            some_function,
            {"c": d}
        )
    ),
)

```

**Remaining Issues:**

1. We do not have access to both `args` and `kwargs` simultaneously in the `BEFORE CALL` events.
2. We do not have the `args` available in the `AFTER CALL` event.

#### 3. Solving the argument access issue (The Naive Approach)

One way to ensure access is to pass both `args` and `kwargs` to both hooks. However, this causes double evaluation of arguments, which breaks programs with side effects.

```python
counter = 0
def get_num():
    global counter
    counter = counter + 1
    return counter

# The original function
some_function(a, b, c=get_num())

# The instrumentation
after_call(
    some_function,
    some_function(
        *before_call_args(
            some_function,
            (a, b),
            { "c": get_num() } # This will return 1
        ),
        **before_call_kwargs(
            some_function,
            (a, b),
            { "c": get_num() } # This will return 2 (CORRUPTION)
        )
    ),
)

```

#### 4. Solving the argument access issue (The Internal Stash Approach)

Since `before_call_kwargs` is always responsible for emitting the event when both types of arguments exist, we can store the positional args internally in a stash until `before_call_kwargs` is called. We can handle this using a dictionary and a unique key.

**Safety Considerations:**

1. **Thread safety:** Data must not be corrupted if the same call happens on different threads.
2. **Loop safety:** Successive calls to the same function must not corrupt stored values.
3. **Recursion safety:** Args evaluation triggering a call to the same function must be handled correctly.

**Initial Implementation:**

```python
class CallProxy:
    _stash = threading.local() # Ensures data is isolated per thread

    @classmethod
    def before_call_args(cls, key, func, has_kwargs, args):
        if not has_kwargs:
            # BEFORE CALL EVENT...

        if not hasattr(cls._stash, 'data'):
            cls._stash.data = {}

        # kwargs empty for now, will be replaced if they actually exist
        cls._stash.data[key] = (args, {})
        return args

    @classmethod
    def before_call_kwargs(cls, key, func, kwargs):
        if key in cls._stash.data:
            args = cls._stash.data[key][0]
        else:
            args = ()

        # BEFORE CALL EVENT with func, args, and kwargs
        cls._stash.data[key] = (args, kwargs) # Store for after_call event
        return kwargs

    @classmethod
    def after_call(cls, key, func, result):
        if key in cls._stash.data:
            args, kwargs = cls._stash.data[key]
        else:
            args, kwargs = ((), {})

        # AFTER CALL event with func, args, kwargs, and result
        del cls._stash.data[key] # Cleanup
        return result

```

**Reviewing Safety:**

1. **Thread safety:** `threading.local()` guarantees this.
2. **Loop safety:** On a single thread, the hooks run in order.
3. **Recursion safety:** **This is still an issue.**

If we use a static unique key (e.g., `'some-static-unique-key'`), recursion overwrites the data.

**Example of Recursion Corruption:**
`causing_recursion() -> before_call_args(2) -> causing_recursion() -> before_call_args(2) ...`

Subsequent calls to `before_call_args` overwrite the value at key `2`. When the stack unwinds, `after_call(2)` receives incorrect values.

---

### Solving Recursion Corruption

#### 4.1 The Stack Approach

Instead of storing a single value per key, we could store a stack. However, this depends on `after_call` successfully popping the value. If the function raises an exception, `after_call` won't run, leaving the stack corrupted.

#### 4.2 The Dynamic Key Approach

We need a dynamic key that is unique per specific function invocation. The challenge is generating this key such that it is available in `before_call_args`, `before_call_kwargs`, and `after_call`.

**Attempt A: The Walrus Operator**
Generate a key and store it in a variable using `:=`.

```python
# The original function
some_function(a, b, c=d)

# The instrumentation
after_call(
	key := uuid(), # a new key
	some_function,
	some_function(
		*before_call_args(
			key, # use the same key
			some_function,
			(a, b)
		),
		**before_call_kwargs(
			key, # use the same key
			some_function,
			{"c": d}
		)
	),
)

```

**Issues:**

1. Doesn't work in class definitions (assignments become class attributes, which could cause issues with that class especially if some code expects a certain set of attributes).
2. Walrus operator is not allowed in standard list comprehensions (though workarounds exist, consider the following code).

```python
[print(p, phrase.count(p)) for p in (phrase := 'Mary had a little lamb')] # not legal

[print(p, phrase.count(p)) for p in phrase if (phrase := 'Mary had a little lamb')] # legal
```

In fact this was one of the failed attempts to temporarily store the args of the function being called avoiding the usage of an internal dictionary to keep track of them.

**Attempt B: `sys._getframe` (The Winner)**
We can use `sys._getframe()` to get the current stack frame object (which is unique for each recursion step) and use its ID. Combined with the static key, this provides a robust unique key.

`key = static_key + id(sys._getframe(1))` (Using 1 for the parent frame).

### 5. Solving the Multiple Evaluations Issue

We previously assumed `some_function` always refers to the same function. This is not guaranteed, particularly with stateful properties of classes.

```python
class ToggleSwitch:
	def __init__(self):
		self._state = False

	@property
	def toggle(self):
		self._state = not self._state
	return self.do_action

	def do_action(self):
		return "Action performed"
		switch = ToggleSwitch()

# --- THE BUGGY AST TRANSFORMATION ---
# Original Code:
switch.toggle()

# Transformed to:
after_call(switch.toggle, switch.toggle())

# Execution:
after_call(
	switch.toggle, # <== Access 1: Flips state to True. Returns method.
	switch.toggle() # <== Access 2: Flips state to False. Runs method.
)

```

To fix this, we must avoid accessing the method more than once. We can store the function object itself in our stash along with the arguments.

---

## The Final Solution

We use a `CallProxy` with an internal stash keyed by a combination of a static ID and the stack frame ID.

```python
import sys
import threading

class CallProxy:
    _stash = threading.local() # Ensures data is isolated per thread

    @classmethod
    def before_call(cls, static_key, func, args, kwargs):
        key = (static_key, id(sys._getframe(1)))

        # BEFORE CALL EVENT with func, args, and kwargs

        if not hasattr(cls._stash, 'data'):
            # Init the dictionary
            cls._stash.data = {}

        cls._stash.data[key] = (func, args, kwargs)

        return func

    @classmethod
    def get_args(cls, static_key):
        key = (static_key, id(sys._getframe(1)))
        return cls._stash.data[key][1]

    @classmethod
    def get_kwargs(cls, static_key):
        key = (static_key, id(sys._getframe(1)))
        return cls._stash.data[key][2]

    @classmethod
    def after_call(cls, static_key, result):
        key = (static_key, id(sys._getframe(1)))
        if hasattr(cls._stash, 'data') and key in cls._stash.data:
            func, args, kwargs = cls._stash.data[key]
            del cls._stash.data[key]

            # AFTER CALL event with func, args, kwargs, and result

        return result

## EXAMPLE AST OUTPUT:

# The original code
some_function(a, b, c=x)

# The instrumentation
after_call(
    'some-static-unique-key',
    before_call(
        'some-static-unique-key',
        some_function,
        (a, b),
        { "c": x },
        # additional_info, like filepath, lineno etc...
    )(
        *get_args('some-static-unique-key'),
        **get_kwargs('some-static-unique-key')
    )
)

```
