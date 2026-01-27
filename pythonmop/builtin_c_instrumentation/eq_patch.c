// eq_patch.c
#include <Python.h>
#include <pthread.h>

// Structure to store original tp_richcompare functions
typedef struct {
    PyTypeObject *type;
    richcmpfunc original_richcompare;
} TypePatch;

// List of types to patch (add more as needed)
static TypePatch patched_types[] = {
    {&PyFloat_Type, NULL},   // float
    {&PyLong_Type, NULL},   // int
    {&PyUnicode_Type, NULL}, // str (commented out to avoid logging issues)
    {&PyList_Type, NULL},    // list
    {&PyDict_Type, NULL},    // dict
    {&PyTuple_Type, NULL},   // tuple
    {&PySet_Type, NULL},     // set
    {NULL, NULL}
};

// Python callbacks for equality and inequality events
static PyObject *eq_callback = NULL;
static PyObject *ne_callback = NULL;
static PyObject *gt_callback = NULL;
static PyObject *lt_callback = NULL;
static PyObject *ge_callback = NULL;
static PyObject *le_callback = NULL;

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

// Custom richcompare function
static PyObject *my_richcompare(PyObject *a, PyObject *b, int op) {
    // Initialize recursion key
    init_recursion_key();
    
    // Check for recursion
    int in_callback = (pthread_getspecific(recursion_key) != NULL);
    
    // Find the original richcompare function first
    richcmpfunc original = NULL;
    for (int i = 0; patched_types[i].type != NULL; i++) {
        if (Py_TYPE(a) == patched_types[i].type || Py_TYPE(b) == patched_types[i].type) {
            original = patched_types[i].original_richcompare;
            break;
        }
    }
    
    if (!in_callback && eq_callback != NULL && op == Py_EQ) {
        // Set recursion guard
        pthread_setspecific(recursion_key, (void *)1);
        
        // Call Python callback
        PyGILState_STATE gstate = PyGILState_Ensure();
        
        // Get frame information using Python C API
        PyObject *frame = PyEval_GetFrame();
        PyObject *filename = NULL;
        PyObject *lineno = NULL;
        
        if (frame != NULL) {
            filename = PyObject_GetAttrString(frame, "f_code");
            if (filename != NULL) {
                PyObject *code = filename;
                filename = PyObject_GetAttrString(code, "co_filename");
                Py_DECREF(code);
            }
            lineno = PyObject_GetAttrString(frame, "f_lineno");
        }
        
        // Increment refcounts to ensure objects stay alive
        Py_INCREF(a);
        Py_INCREF(b);
        
        // Create tuple with 4 arguments: a, b, filename, lineno
        PyObject *args = PyTuple_Pack(4, a, b, 
            filename ? filename : Py_None,
            lineno ? lineno : PyLong_FromLong(0));
        
        if (filename) Py_DECREF(filename);
        if (lineno) Py_DECREF(lineno);
        
        PyObject *result = NULL;
        
        if (args == NULL) {
            PyErr_Print();
            Py_DECREF(a);
            Py_DECREF(b);
            PyGILState_Release(gstate);
            pthread_setspecific(recursion_key, NULL);
            return PyObject_RichCompare(a, b, op);
        }
        
        result = PyObject_CallObject(eq_callback, args);
        Py_DECREF(args);
        
        if (result == NULL) {
            // Clear the error and continue with original comparison
            PyErr_Clear();
            Py_DECREF(a);
            Py_DECREF(b);
            PyGILState_Release(gstate);
            pthread_setspecific(recursion_key, NULL);
            return PyObject_RichCompare(a, b, op);
        }
        
        Py_DECREF(result);
        Py_DECREF(a);
        Py_DECREF(b);
        PyGILState_Release(gstate);
        
        // Clear recursion guard
        pthread_setspecific(recursion_key, NULL);
    }
    
    if (!in_callback && ne_callback != NULL && op == Py_NE) {
        // Set recursion guard
        pthread_setspecific(recursion_key, (void *)1);
        
        // Call Python callback
        PyGILState_STATE gstate = PyGILState_Ensure();
        
        // Get frame information using Python C API
        PyObject *frame = PyEval_GetFrame();
        PyObject *filename = NULL;
        PyObject *lineno = NULL;
        
        if (frame != NULL) {
            filename = PyObject_GetAttrString(frame, "f_code");
            if (filename != NULL) {
                PyObject *code = filename;
                filename = PyObject_GetAttrString(code, "co_filename");
                Py_DECREF(code);
            }
            lineno = PyObject_GetAttrString(frame, "f_lineno");
        }
        
        // Increment refcounts to ensure objects stay alive
        Py_INCREF(a);
        Py_INCREF(b);
        
        // Create tuple with 4 arguments: a, b, filename, lineno
        PyObject *args = PyTuple_Pack(4, a, b, 
            filename ? filename : Py_None,
            lineno ? lineno : PyLong_FromLong(0));
        
        if (filename) Py_DECREF(filename);
        if (lineno) Py_DECREF(lineno);
        
        PyObject *result = NULL;
        
        if (args == NULL) {
            PyErr_Print();
            Py_DECREF(a);
            Py_DECREF(b);
            PyGILState_Release(gstate);
            pthread_setspecific(recursion_key, NULL);
            return PyObject_RichCompare(a, b, op);
        }
        
        result = PyObject_CallObject(ne_callback, args);
        Py_DECREF(args);
        
        if (result == NULL) {
            // Clear the error and continue with original comparison
            PyErr_Clear();
            Py_DECREF(a);
            Py_DECREF(b);
            PyGILState_Release(gstate);
            pthread_setspecific(recursion_key, NULL);
            return PyObject_RichCompare(a, b, op);
        }
        
        Py_DECREF(result);
        Py_DECREF(a);
        Py_DECREF(b);
        PyGILState_Release(gstate);
        
        // Clear recursion guard
        pthread_setspecific(recursion_key, NULL);
    }
    
    if (!in_callback && gt_callback != NULL && op == Py_GT) {
        // Set recursion guard
        pthread_setspecific(recursion_key, (void *)1);
        
        // Call Python callback
        PyGILState_STATE gstate = PyGILState_Ensure();
        
        // Get frame information using Python C API
        PyObject *frame = PyEval_GetFrame();
        PyObject *filename = NULL;
        PyObject *lineno = NULL;
        
        if (frame != NULL) {
            filename = PyObject_GetAttrString(frame, "f_code");
            if (filename != NULL) {
                PyObject *code = filename;
                filename = PyObject_GetAttrString(code, "co_filename");
                Py_DECREF(code);
            }
            lineno = PyObject_GetAttrString(frame, "f_lineno");
        }
        
        // Increment refcounts to ensure objects stay alive
        Py_INCREF(a);
        Py_INCREF(b);
        
        // Create tuple with 4 arguments: a, b, filename, lineno
        PyObject *args = PyTuple_Pack(4, a, b, 
            filename ? filename : Py_None,
            lineno ? lineno : PyLong_FromLong(0));
        
        if (filename) Py_DECREF(filename);
        if (lineno) Py_DECREF(lineno);
        
        PyObject *result = NULL;
        
        if (args == NULL) {
            PyErr_Print();
            Py_DECREF(a);
            Py_DECREF(b);
            PyGILState_Release(gstate);
            pthread_setspecific(recursion_key, NULL);
            return PyObject_RichCompare(a, b, op);
        }
        
        result = PyObject_CallObject(gt_callback, args);
        Py_DECREF(args);
        
        if (result == NULL) {
            // Clear the error and continue with original comparison
            PyErr_Clear();
            Py_DECREF(a);
            Py_DECREF(b);
            PyGILState_Release(gstate);
            pthread_setspecific(recursion_key, NULL);
            return PyObject_RichCompare(a, b, op);
        }
        
        Py_DECREF(result);
        Py_DECREF(a);
        Py_DECREF(b);
        PyGILState_Release(gstate);
        
        // Clear recursion guard
        pthread_setspecific(recursion_key, NULL);
    }
    
    if (!in_callback && lt_callback != NULL && op == Py_LT) {
        // Set recursion guard
        pthread_setspecific(recursion_key, (void *)1);
        
        // Call Python callback
        PyGILState_STATE gstate = PyGILState_Ensure();
        
        // Get frame information using Python C API
        PyObject *frame = PyEval_GetFrame();
        PyObject *filename = NULL;
        PyObject *lineno = NULL;
        
        if (frame != NULL) {
            filename = PyObject_GetAttrString(frame, "f_code");
            if (filename != NULL) {
                PyObject *code = filename;
                filename = PyObject_GetAttrString(code, "co_filename");
                Py_DECREF(code);
            }
            lineno = PyObject_GetAttrString(frame, "f_lineno");
        }
        
        // Increment refcounts to ensure objects stay alive
        Py_INCREF(a);
        Py_INCREF(b);
        
        // Create tuple with 4 arguments: a, b, filename, lineno
        PyObject *args = PyTuple_Pack(4, a, b, 
            filename ? filename : Py_None,
            lineno ? lineno : PyLong_FromLong(0));
        
        if (filename) Py_DECREF(filename);
        if (lineno) Py_DECREF(lineno);
        
        PyObject *result = NULL;
        
        if (args == NULL) {
            PyErr_Print();
            Py_DECREF(a);
            Py_DECREF(b);
            PyGILState_Release(gstate);
            pthread_setspecific(recursion_key, NULL);
            return PyObject_RichCompare(a, b, op);
        }
        
        result = PyObject_CallObject(lt_callback, args);
        Py_DECREF(args);
        
        if (result == NULL) {
            // Clear the error and continue with original comparison
            PyErr_Clear();
            Py_DECREF(a);
            Py_DECREF(b);
            PyGILState_Release(gstate);
            pthread_setspecific(recursion_key, NULL);
            return PyObject_RichCompare(a, b, op);
        }
        
        Py_DECREF(result);
        Py_DECREF(a);
        Py_DECREF(b);
        PyGILState_Release(gstate);
        
        // Clear recursion guard
        pthread_setspecific(recursion_key, NULL);
    }
    
    if (!in_callback && ge_callback != NULL && op == Py_GE) {
        // Set recursion guard
        pthread_setspecific(recursion_key, (void *)1);
        
        // Call Python callback
        PyGILState_STATE gstate = PyGILState_Ensure();
        
        // Get frame information using Python C API
        PyObject *frame = PyEval_GetFrame();
        PyObject *filename = NULL;
        PyObject *lineno = NULL;
        
        if (frame != NULL) {
            filename = PyObject_GetAttrString(frame, "f_code");
            if (filename != NULL) {
                PyObject *code = filename;
                filename = PyObject_GetAttrString(code, "co_filename");
                Py_DECREF(code);
            }
            lineno = PyObject_GetAttrString(frame, "f_lineno");
        }
        
        // Increment refcounts to ensure objects stay alive
        Py_INCREF(a);
        Py_INCREF(b);
        
        // Create tuple with 4 arguments: a, b, filename, lineno
        PyObject *args = PyTuple_Pack(4, a, b, 
            filename ? filename : Py_None,
            lineno ? lineno : PyLong_FromLong(0));
        
        if (filename) Py_DECREF(filename);
        if (lineno) Py_DECREF(lineno);
        
        PyObject *result = NULL;
        
        if (args == NULL) {
            PyErr_Print();
            Py_DECREF(a);
            Py_DECREF(b);
            PyGILState_Release(gstate);
            pthread_setspecific(recursion_key, NULL);
            return PyObject_RichCompare(a, b, op);
        }
        
        result = PyObject_CallObject(ge_callback, args);
        Py_DECREF(args);
        
        if (result == NULL) {
            // Clear the error and continue with original comparison
            PyErr_Clear();
            Py_DECREF(a);
            Py_DECREF(b);
            PyGILState_Release(gstate);
            pthread_setspecific(recursion_key, NULL);
            return PyObject_RichCompare(a, b, op);
        }
        
        Py_DECREF(result);
        Py_DECREF(a);
        Py_DECREF(b);
        PyGILState_Release(gstate);
        
        // Clear recursion guard
        pthread_setspecific(recursion_key, NULL);
    }
    
    if (!in_callback && le_callback != NULL && op == Py_LE) {
        // Set recursion guard
        pthread_setspecific(recursion_key, (void *)1);
        
        // Call Python callback
        PyGILState_STATE gstate = PyGILState_Ensure();
        
        // Get frame information using Python C API
        PyObject *frame = PyEval_GetFrame();
        PyObject *filename = NULL;
        PyObject *lineno = NULL;
        
        if (frame != NULL) {
            filename = PyObject_GetAttrString(frame, "f_code");
            if (filename != NULL) {
                PyObject *code = filename;
                filename = PyObject_GetAttrString(code, "co_filename");
                Py_DECREF(code);
            }
            lineno = PyObject_GetAttrString(frame, "f_lineno");
        }
        
        // Increment refcounts to ensure objects stay alive
        Py_INCREF(a);
        Py_INCREF(b);
        
        // Create tuple with 4 arguments: a, b, filename, lineno
        PyObject *args = PyTuple_Pack(4, a, b, 
            filename ? filename : Py_None,
            lineno ? lineno : PyLong_FromLong(0));
        
        if (filename) Py_DECREF(filename);
        if (lineno) Py_DECREF(lineno);
        
        PyObject *result = NULL;
        
        if (args == NULL) {
            PyErr_Print();
            Py_DECREF(a);
            Py_DECREF(b);
            PyGILState_Release(gstate);
            pthread_setspecific(recursion_key, NULL);
            return PyObject_RichCompare(a, b, op);
        }
        
        result = PyObject_CallObject(le_callback, args);
        Py_DECREF(args);
        
        if (result == NULL) {
            // Clear the error and continue with original comparison
            PyErr_Clear();
            Py_DECREF(a);
            Py_DECREF(b);
            PyGILState_Release(gstate);
            pthread_setspecific(recursion_key, NULL);
            return PyObject_RichCompare(a, b, op);
        }
        
        Py_DECREF(result);
        Py_DECREF(a);
        Py_DECREF(b);
        PyGILState_Release(gstate);
        
        // Clear recursion guard
        pthread_setspecific(recursion_key, NULL);
    }
    
    // Call original richcompare (or fallback to default)
    if (original) {
        return original(a, b, op);
    }
    
    return PyObject_RichCompare(a, b, op);
}

// Function to patch a type's tp_richcompare slot
static void patch_type(PyTypeObject *type, richcmpfunc new_richcompare) {
    for (int i = 0; patched_types[i].type != NULL; i++) {
        if (patched_types[i].type == type) {
            patched_types[i].original_richcompare = type->tp_richcompare;
            type->tp_richcompare = new_richcompare;
            break;
        }
    }
}

// Python function to apply the patch for equality
static PyObject *patch_eq(PyObject *self, PyObject *args) {
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
    Py_XSETREF(eq_callback, callback);
    
    // Patch all types if not already patched
    for (int i = 0; patched_types[i].type != NULL; i++) {
        if (patched_types[i].original_richcompare == NULL) {
            patch_type(patched_types[i].type, my_richcompare);
        }
    }
    
    Py_RETURN_NONE;
}

// Python function to apply the patch for inequality
static PyObject *patch_ne(PyObject *self, PyObject *args) {
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
    Py_XSETREF(ne_callback, callback);
    
    // Patch all types if not already patched
    for (int i = 0; patched_types[i].type != NULL; i++) {
        if (patched_types[i].original_richcompare == NULL) {
            patch_type(patched_types[i].type, my_richcompare);
        }
    }
    
    Py_RETURN_NONE;
}

// Python function to apply the patch for greater than
static PyObject *patch_gt(PyObject *self, PyObject *args) {
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
    Py_XSETREF(gt_callback, callback);
    
    // Patch all types if not already patched
    for (int i = 0; patched_types[i].type != NULL; i++) {
        if (patched_types[i].original_richcompare == NULL) {
            patch_type(patched_types[i].type, my_richcompare);
        }
    }
    
    Py_RETURN_NONE;
}

// Python function to apply the patch for less than
static PyObject *patch_lt(PyObject *self, PyObject *args) {
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
    Py_XSETREF(lt_callback, callback);
    
    // Patch all types if not already patched
    for (int i = 0; patched_types[i].type != NULL; i++) {
        if (patched_types[i].original_richcompare == NULL) {
            patch_type(patched_types[i].type, my_richcompare);
        }
    }
    
    Py_RETURN_NONE;
}

// Python function to apply the patch for greater than or equal
static PyObject *patch_ge(PyObject *self, PyObject *args) {
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
    Py_XSETREF(ge_callback, callback);
    
    // Patch all types if not already patched
    for (int i = 0; patched_types[i].type != NULL; i++) {
        if (patched_types[i].original_richcompare == NULL) {
            patch_type(patched_types[i].type, my_richcompare);
        }
    }
    
    Py_RETURN_NONE;
}

// Python function to apply the patch for less than or equal
static PyObject *patch_le(PyObject *self, PyObject *args) {
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
    Py_XSETREF(le_callback, callback);
    
    // Patch all types if not already patched
    for (int i = 0; patched_types[i].type != NULL; i++) {
        if (patched_types[i].original_richcompare == NULL) {
            patch_type(patched_types[i].type, my_richcompare);
        }
    }
    
    Py_RETURN_NONE;
}

// Python function to restore original behavior
static PyObject *unpatch_eq(PyObject *self, PyObject *args) {
    // Clear equality callback
    Py_XSETREF(eq_callback, NULL);
    
    // If no callbacks are active, restore original tp_richcompare
    if (ne_callback == NULL) {
        for (int i = 0; patched_types[i].type != NULL; i++) {
            if (patched_types[i].original_richcompare) {
                patched_types[i].type->tp_richcompare = patched_types[i].original_richcompare;
                patched_types[i].original_richcompare = NULL;
            }
        }
    }
    
    Py_RETURN_NONE;
}

// Python function to restore original behavior for inequality
static PyObject *unpatch_ne(PyObject *self, PyObject *args) {
    // Clear inequality callback
    Py_XSETREF(ne_callback, NULL);
    
    // If no callbacks are active, restore original tp_richcompare
    if (eq_callback == NULL) {
        for (int i = 0; patched_types[i].type != NULL; i++) {
            if (patched_types[i].original_richcompare) {
                patched_types[i].type->tp_richcompare = patched_types[i].original_richcompare;
                patched_types[i].original_richcompare = NULL;
            }
        }
    }
    
    Py_RETURN_NONE;
}

// Python function to restore original behavior for greater than
static PyObject *unpatch_gt(PyObject *self, PyObject *args) {
    // Clear greater than callback
    Py_XSETREF(gt_callback, NULL);
    
    // If no callbacks are active, restore original tp_richcompare
    if (eq_callback == NULL && ne_callback == NULL) {
        for (int i = 0; patched_types[i].type != NULL; i++) {
            if (patched_types[i].original_richcompare) {
                patched_types[i].type->tp_richcompare = patched_types[i].original_richcompare;
                patched_types[i].original_richcompare = NULL;
            }
        }
    }
    
    Py_RETURN_NONE;
}

// Python function to restore original behavior for less than
static PyObject *unpatch_lt(PyObject *self, PyObject *args) {
    // Clear less than callback
    Py_XSETREF(lt_callback, NULL);
    
    // If no callbacks are active, restore original tp_richcompare
    if (eq_callback == NULL && ne_callback == NULL && gt_callback == NULL) {
        for (int i = 0; patched_types[i].type != NULL; i++) {
            if (patched_types[i].original_richcompare) {
                patched_types[i].type->tp_richcompare = patched_types[i].original_richcompare;
                patched_types[i].original_richcompare = NULL;
            }
        }
    }
    
    Py_RETURN_NONE;
}

// Python function to restore original behavior for greater than or equal
static PyObject *unpatch_ge(PyObject *self, PyObject *args) {
    // Clear greater than or equal callback
    Py_XSETREF(ge_callback, NULL);
    
    // If no callbacks are active, restore original tp_richcompare
    if (eq_callback == NULL && ne_callback == NULL && gt_callback == NULL && lt_callback == NULL) {
        for (int i = 0; patched_types[i].type != NULL; i++) {
            if (patched_types[i].original_richcompare) {
                patched_types[i].type->tp_richcompare = patched_types[i].original_richcompare;
                patched_types[i].original_richcompare = NULL;
            }
        }
    }
    
    Py_RETURN_NONE;
}

// Python function to restore original behavior for less than or equal
static PyObject *unpatch_le(PyObject *self, PyObject *args) {
    // Clear less than or equal callback
    Py_XSETREF(le_callback, NULL);
    
    // If no callbacks are active, restore original tp_richcompare
    if (eq_callback == NULL && ne_callback == NULL && gt_callback == NULL && lt_callback == NULL && ge_callback == NULL) {
        for (int i = 0; patched_types[i].type != NULL; i++) {
            if (patched_types[i].original_richcompare) {
                patched_types[i].type->tp_richcompare = patched_types[i].original_richcompare;
                patched_types[i].original_richcompare = NULL;
            }
        }
    }
    
    Py_RETURN_NONE;
}

static PyMethodDef EqPatchMethods[] = {
    {"patch_eq", patch_eq, METH_VARARGS, "Patch == operator with a callback"},
    {"patch_ne", patch_ne, METH_VARARGS, "Patch != operator with a callback"},
    {"patch_gt", patch_gt, METH_VARARGS, "Patch > operator with a callback"},
    {"patch_lt", patch_lt, METH_VARARGS, "Patch < operator with a callback"},
    {"patch_ge", patch_ge, METH_VARARGS, "Patch >= operator with a callback"},
    {"patch_le", patch_le, METH_VARARGS, "Patch <= operator with a callback"},
    {"unpatch_eq", unpatch_eq, METH_NOARGS, "Restore original == behavior"},
    {"unpatch_ne", unpatch_ne, METH_NOARGS, "Restore original != behavior"},
    {"unpatch_gt", unpatch_gt, METH_NOARGS, "Restore original > behavior"},
    {"unpatch_lt", unpatch_lt, METH_NOARGS, "Restore original < behavior"},
    {"unpatch_ge", unpatch_ge, METH_NOARGS, "Restore original >= behavior"},
    {"unpatch_le", unpatch_le, METH_NOARGS, "Restore original <= behavior"},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef eqpatchmodule = {
    PyModuleDef_HEAD_INIT,
    "eq_patch",
    "Module to patch the == operator globally",
    -1,
    EqPatchMethods
};

PyMODINIT_FUNC PyInit_eq_patch(void) {
    return PyModule_Create(&eqpatchmodule);
}