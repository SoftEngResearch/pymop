#include <Python.h>
#include <pthread.h>

// Structure to store original iterator-related functions
typedef struct {
    PyTypeObject *type;
    getiterfunc original_iter;
} TypePatch;

// List of types to patch (covers common iterables)
static TypePatch patched_types[] = {
    {&PyList_Type, NULL},    // list
    {&PyTuple_Type, NULL},   // tuple
    {&PyDict_Type, NULL},    // dict
    {&PySet_Type, NULL},     // set
    {&PyUnicode_Type, NULL}, // str
    {NULL, NULL}
};

// Python callbacks for loop start, iteration, and end
static PyObject *start_callback = NULL; // Called when __iter__ is invoked
static PyObject *next_callback = NULL;  // Called when __next__ is invoked
static PyObject *end_callback = NULL;   // Called when StopIteration is raised

// Thread-local recursion guard
static pthread_key_t recursion_key;
static int recursion_key_initialized = 0;

static void recursion_key_destructor(void *data) {
    // No-op; pthread_key_delete handles cleanup
}

static void init_recursion_key(void) {
    if (!recursion_key_initialized) {
        pthread_key_create(&recursion_key, recursion_key_destructor);
        recursion_key_initialized = 1;
    }
}

// Custom iterator wrapper type
typedef struct {
    PyObject_HEAD
    PyObject *iterator; // Wrapped iterator
    getiterfunc original_iter; // Original iterator function
} WrappedIteratorObject;

static PyObject *wrapped_iterator_iter(PyObject *self) {
    // Simply return self (iterator protocol requirement)
    Py_INCREF(self);
    return self;
}

static PyObject *wrapped_iterator_next(PyObject *self) {
    WrappedIteratorObject *wrapper = (WrappedIteratorObject *)self;
    PyObject *result = NULL;

    // Initialize recursion key
    init_recursion_key();

    // Check for recursion
    int in_callback = (pthread_getspecific(recursion_key) != NULL);

    if (!in_callback && next_callback != NULL) {
        // Set recursion guard
        pthread_setspecific(recursion_key, (void *)1);

        // Call Python callback
        PyGILState_STATE gstate = PyGILState_Ensure();

        // Get the caller's frame to extract filename and line number
        PyFrameObject *frame = PyEval_GetFrame();
        PyObject *filename = NULL;
        PyObject *lineno = NULL;

        if (frame != NULL) {
            PyCodeObject *code = PyFrame_GetCode(frame);
            if (code != NULL) {
                filename = code->co_filename; // Borrowed reference
                Py_INCREF(filename);
                lineno = PyLong_FromLong(PyFrame_GetLineNumber(frame));
                Py_DECREF(code);
            }
        }

        // Fallback if frame info is unavailable
        if (filename == NULL) {
            filename = PyUnicode_FromString("<unknown>");
        }
        if (lineno == NULL) {
            lineno = PyLong_FromLong(-1);
        }

        // Pass the iterator, filename, and line number to the callback
        PyObject *args = PyTuple_Pack(3, wrapper->iterator, filename, lineno);
        Py_DECREF(filename);
        Py_DECREF(lineno);

        if (args == NULL) {
            PyErr_Print();
            PyGILState_Release(gstate);
            pthread_setspecific(recursion_key, NULL);
            goto original_next;
        }

        PyObject *callback_result = PyObject_CallObject(next_callback, args);
        Py_DECREF(args);

        if (callback_result == NULL) {
            PyErr_Clear(); // Clear error and proceed
        } else {
            Py_DECREF(callback_result);
        }

        PyGILState_Release(gstate);
        pthread_setspecific(recursion_key, NULL);
    }

original_next:
    // Call the original iterator's next method
    result = PyObject_CallMethod(wrapper->iterator, "__next__", NULL);
    if (result == NULL && PyErr_Occurred() && PyErr_ExceptionMatches(PyExc_StopIteration)) {
        // Call end callback if set
        if (!in_callback && end_callback != NULL) {
            // Set recursion guard
            pthread_setspecific(recursion_key, (void *)1);

            // Call Python callback
            PyGILState_STATE gstate = PyGILState_Ensure();

            // Get the caller's frame to extract filename and line number
            PyFrameObject *frame = PyEval_GetFrame();
            PyObject *filename = NULL;
            PyObject *lineno = NULL;

            if (frame != NULL) {
                PyCodeObject *code = PyFrame_GetCode(frame);
                if (code != NULL) {
                    filename = code->co_filename; // Borrowed reference
                    Py_INCREF(filename);
                    lineno = PyLong_FromLong(PyFrame_GetLineNumber(frame));
                    Py_DECREF(code);
                }
            }

            // Fallback if frame info is unavailable
            if (filename == NULL) {
                filename = PyUnicode_FromString("<unknown>");
            }
            if (lineno == NULL) {
                lineno = PyLong_FromLong(-1);
            }

            // Pass the iterator, filename, and line number to the callback
            PyObject *args = PyTuple_Pack(3, wrapper->iterator, filename, lineno);
            Py_DECREF(filename);
            Py_DECREF(lineno);

            if (args != NULL) {
                PyObject *callback_result = PyObject_CallObject(end_callback, args);
                Py_DECREF(args);
                if (callback_result == NULL) {
                    PyErr_Clear(); // Clear error and proceed
                } else {
                    Py_DECREF(callback_result);
                }
            } else {
                PyErr_Clear();
            }

            PyGILState_Release(gstate);
            pthread_setspecific(recursion_key, NULL);
        }
        // Propagate StopIteration as-is
        return NULL;
    }

    return result;
}

static void wrapped_iterator_dealloc(WrappedIteratorObject *self) {
    Py_XDECREF(self->iterator);
    Py_TYPE(self)->tp_free((PyObject *)self);
}

static PyTypeObject WrappedIteratorType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    "for_patch.WrappedIterator", // tp_name
    sizeof(WrappedIteratorObject), // tp_basicsize
    0, // tp_itemsize
    (destructor)wrapped_iterator_dealloc, // tp_dealloc
    0, // tp_print
    0, // tp_getattr
    0, // tp_setattr
    0, // tp_as_async
    0, // tp_repr
    0, // tp_as_number
    0, // tp_as_sequence
    0, // tp_as_mapping
    0, // tp_hash
    0, // tp_call
    0, // tp_str
    0, // tp_getattro
    0, // tp_setattro
    0, // tp_as_buffer
    Py_TPFLAGS_DEFAULT, // tp_flags
    "Wrapped iterator for for-loop patching", // tp_doc
    0, // tp_traverse
    0, // tp_clear
    0, // tp_richcompare
    0, // tp_weaklistoffset
    wrapped_iterator_iter, // tp_iter
    wrapped_iterator_next, // tp_iternext
    0, // tp_methods
    0, // tp_members
    0, // tp_getset
    0, // tp_base
    0, // tp_dict
    0, // tp_descr_get
    0, // tp_descr_set
    0, // tp_dictoffset
    0, // tp_init
    0, // tp_alloc
    PyType_GenericNew, // tp_new
};

// Custom iter function
static PyObject *my_iter(PyObject *self) {
    // Initialize recursion key
    init_recursion_key();

    // Check for recursion
    int in_callback = (pthread_getspecific(recursion_key) != NULL);

    // Find the original iter function
    getiterfunc original = NULL;
    for (int i = 0; patched_types[i].type != NULL; i++) {
        if (Py_TYPE(self) == patched_types[i].type) {
            original = patched_types[i].original_iter;
            break;
        }
    }

    // Call original iter function
    PyObject *iterator = NULL;
    if (original) {
        iterator = original(self);
    } else {
        iterator = PyObject_GetIter(self);
    }

    if (iterator == NULL) {
        return NULL;
    }

    // Create wrapped iterator
    WrappedIteratorObject *wrapped = PyObject_New(WrappedIteratorObject, &WrappedIteratorType);
    if (wrapped == NULL) {
        Py_DECREF(iterator);
        return NULL;
    }

    wrapped->iterator = iterator;
    wrapped->original_iter = original;

    // Notify start of loop if callback is set
    if (!in_callback && start_callback != NULL) {
        // Set recursion guard
        pthread_setspecific(recursion_key, (void *)1);

        // Call Python callback
        PyGILState_STATE gstate = PyGILState_Ensure();

        // Get the caller's frame to extract filename and line number
        PyFrameObject *frame = PyEval_GetFrame();
        PyObject *filename = NULL;
        PyObject *lineno = NULL;

        if (frame != NULL) {
            PyCodeObject *code = PyFrame_GetCode(frame);
            if (code != NULL) {
                filename = code->co_filename; // Borrowed reference
                Py_INCREF(filename);
                lineno = PyLong_FromLong(PyFrame_GetLineNumber(frame));
                Py_DECREF(code);
            }
        }

        // Fallback if frame info is unavailable
        if (filename == NULL) {
            filename = PyUnicode_FromString("<unknown>");
        }
        if (lineno == NULL) {
            lineno = PyLong_FromLong(-1);
        }

        // Pass the iterable, filename, and line number to the callback
        PyObject *args = PyTuple_Pack(3, self, filename, lineno);
        Py_DECREF(filename);
        Py_DECREF(lineno);

        if (args == NULL) {
            PyErr_Print();
            Py_DECREF(wrapped);
            PyGILState_Release(gstate);
            pthread_setspecific(recursion_key, NULL);
            return NULL;
        }

        PyObject *result = PyObject_CallObject(start_callback, args);
        Py_DECREF(args);

        if (result == NULL) {
            PyErr_Clear(); // Clear error and proceed
        } else {
            Py_DECREF(result);
        }

        PyGILState_Release(gstate);
        pthread_setspecific(recursion_key, NULL);
    }

    return (PyObject *)wrapped;
}

// Function to patch a type's tp_iter slot
static void patch_type(PyTypeObject *type, getiterfunc new_iter) {
    for (int i = 0; patched_types[i].type != NULL; i++) {
        if (patched_types[i].type == type) {
            patched_types[i].original_iter = type->tp_iter;
            type->tp_iter = new_iter;
            break;
        }
    }
}

// Python function to patch loop start
static PyObject *patch_for_start(PyObject *self, PyObject *args) {
    PyObject *callback;
    if (!PyArg_ParseTuple(args, "O", &callback)) {
        return NULL;
    }

    if (!PyCallable_Check(callback)) {
        PyErr_SetString(PyExc_TypeError, "Callback must be callable");
        return NULL;
    }

    // Store callback
    Py_XINCREF(callback);
    Py_XSETREF(start_callback, callback);

    // Patch all types if not already patched
    for (int i = 0; patched_types[i].type != NULL; i++) {
        if (patched_types[i].original_iter == NULL) {
            patch_type(patched_types[i].type, my_iter);
        }
    }

    Py_RETURN_NONE;
}

// Python function to patch loop iteration
static PyObject *patch_for_next(PyObject *self, PyObject *args) {
    PyObject *callback;
    if (!PyArg_ParseTuple(args, "O", &callback)) {
        return NULL;
    }

    if (!PyCallable_Check(callback)) {
        PyErr_SetString(PyExc_TypeError, "Callback must be callable");
        return NULL;
    }

    // Store callback
    Py_XINCREF(callback);
    Py_XSETREF(next_callback, callback);

    // Patch all types if not already patched
    for (int i = 0; patched_types[i].type != NULL; i++) {
        if (patched_types[i].original_iter == NULL) {
            patch_type(patched_types[i].type, my_iter);
        }
    }

    Py_RETURN_NONE;
}

// Python function to patch loop end
static PyObject *patch_for_end(PyObject *self, PyObject *args) {
    PyObject *callback;
    if (!PyArg_ParseTuple(args, "O", &callback)) {
        return NULL;
    }

    if (!PyCallable_Check(callback)) {
        PyErr_SetString(PyExc_TypeError, "Callback must be callable");
        return NULL;
    }

    // Store callback
    Py_XINCREF(callback);
    Py_XSETREF(end_callback, callback);

    // Patch all types if not already patched
    for (int i = 0; patched_types[i].type != NULL; i++) {
        if (patched_types[i].original_iter == NULL) {
            patch_type(patched_types[i].type, my_iter);
        }
    }

    Py_RETURN_NONE;
}

// Python function to restore original behavior
static PyObject *unpatch_for(PyObject *self, PyObject *args) {
    // Clear callbacks
    Py_XSETREF(start_callback, NULL);
    Py_XSETREF(next_callback, NULL);
    Py_XSETREF(end_callback, NULL);

    // Restore original tp_iter
    for (int i = 0; patched_types[i].type != NULL; i++) {
        if (patched_types[i].original_iter) {
            patched_types[i].type->tp_iter = patched_types[i].original_iter;
            patched_types[i].original_iter = NULL;
        }
    }

    Py_RETURN_NONE;
}

static PyMethodDef ForPatchMethods[] = {
    {"patch_for_start", patch_for_start, METH_VARARGS, "Patch for loop start with a callback"},
    {"patch_for_next", patch_for_next, METH_VARARGS, "Patch for loop iteration with a callback"},
    {"patch_for_end", patch_for_end, METH_VARARGS, "Patch for loop end with a callback"},
    {"unpatch_for", unpatch_for, METH_NOARGS, "Restore original for loop behavior"},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef forpatchmodule = {
    PyModuleDef_HEAD_INIT,
    "for_patch",
    "Module to patch for loops globally",
    -1,
    ForPatchMethods
};

PyMODINIT_FUNC PyInit_for_patch(void) {
    PyObject *module;

    // Initialize WrappedIteratorType
    if (PyType_Ready(&WrappedIteratorType) < 0) {
        return NULL;
    }

    module = PyModule_Create(&forpatchmodule);
    if (module == NULL) {
        return NULL;
    }

    // Add WrappedIteratorType to module
    Py_INCREF(&WrappedIteratorType);
    PyModule_AddObject(module, "WrappedIterator", (PyObject *)&WrappedIteratorType);

    return module;
}