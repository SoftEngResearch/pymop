#define PY_SSIZE_T_CLEAN
#include <Python.h>

static PyObject *call_callback = NULL;
static PyObject *return_callback = NULL;

static int extract_args_from_frame(PyFrameObject *frame,
                                   PyObject **func_name,
                                   PyObject **filename,
                                   PyObject **lineno,
                                   PyObject **kwargs,
                                   PyObject **args,
                                   PyObject **default_args,
                                   PyObject *return_value) {
    PyObject *code_obj = PyFrame_GetCode(frame);
    if (!code_obj) return -1;

    PyObject *name = PyObject_GetAttrString(code_obj, "co_name");
    PyObject *file = PyObject_GetAttrString(code_obj, "co_filename");
    Py_DECREF(code_obj);
    if (!name || !file) {
        Py_XDECREF(name);
        Py_XDECREF(file);
        return -1;
    }

    PyObject *line = PyLong_FromLong(PyFrame_GetLineNumber(frame));
    PyObject *kw = PyDict_New();
    PyObject *arglist = PyList_New(0);
    PyObject *def = PyDict_New();
    if (!line || !kw || !arglist || !def) {
        Py_XDECREF(name);
        Py_XDECREF(file);
        Py_XDECREF(line);
        Py_XDECREF(kw);
        Py_XDECREF(arglist);
        Py_XDECREF(def);
        return -1;
    }

    // Safely hold references to locals/globals (borrowed by default)
    PyObject *locals = PyEval_GetLocals();
    PyObject *globals = PyEval_GetGlobals();
    Py_XINCREF(locals);
    Py_XINCREF(globals);

    // Get parent frame's f_locals if it exists
    PyObject *parent_locals = NULL;
    PyFrameObject *back = PyFrame_GetBack(frame);
    if (back) {
        parent_locals = PyObject_GetAttrString((PyObject *)back, "f_locals");
        Py_DECREF(back);  // release new reference returned by PyFrame_GetBack
    }

    PyObject *global_ids = PySet_New(NULL);
    PyObject *parent_ids = PySet_New(NULL);
    if (!global_ids || !parent_ids) {
        Py_XDECREF(parent_locals);
        Py_XDECREF(global_ids);
        Py_XDECREF(parent_ids);
        Py_XDECREF(locals);
        Py_XDECREF(globals);
        Py_DECREF(name);
        Py_DECREF(file);
        Py_DECREF(line);
        Py_DECREF(kw);
        Py_DECREF(arglist);
        Py_DECREF(def);
        return -1;
    }

    // Fill identity sets
    Py_ssize_t pos = 0;
    PyObject *k, *v, *vid;

    if (globals) {
        pos = 0;
        while (PyDict_Next(globals, &pos, NULL, &v)) {
            vid = PyLong_FromVoidPtr(v);
            PySet_Add(global_ids, vid);
            Py_DECREF(vid);
        }
    }

    if (parent_locals) {
        pos = 0;
        while (PyDict_Next(parent_locals, &pos, NULL, &v)) {
            vid = PyLong_FromVoidPtr(v);
            PySet_Add(parent_ids, vid);
            Py_DECREF(vid);
        }
    }

    // Process frame locals
    pos = 0;
    while (PyDict_Next(locals, &pos, &k, &v)) {
        PyDict_SetItem(kw, k, v);
        PyList_Append(arglist, v);

        vid = PyLong_FromVoidPtr(v);
        int in_parent = PySet_Contains(parent_ids, vid);
        int in_global = PySet_Contains(global_ids, vid);
        Py_DECREF(vid);

        if (!in_parent && !in_global) {
            PyDict_SetItem(def, k, v);
        }
    }

    // Cleanup
    Py_XDECREF(parent_locals);
    Py_DECREF(global_ids);
    Py_DECREF(parent_ids);
    Py_XDECREF(locals);
    Py_XDECREF(globals);

    // Assign only after full success
    *func_name = name;
    *filename = file;
    *lineno = line;
    *kwargs = kw;
    *args = arglist;
    *default_args = def;

    return 0;
}

static int profile_func_call(PyObject *obj, PyFrameObject *frame, int what, PyObject *arg) {
    if (what != PyTrace_CALL || !call_callback) return 0;

    PyObject *func_name, *filename, *lineno, *kwargs, *args, *default_args;
    if (extract_args_from_frame(frame, &func_name, &filename, &lineno, &kwargs, &args, &default_args, NULL) != 0)
        return 0;

    PyObject *callback_args = Py_BuildValue("OOOOOO", func_name, filename, lineno, kwargs, args, default_args);
    Py_XDECREF(PyObject_CallObject(call_callback, callback_args));

    Py_XDECREF(func_name);
    Py_XDECREF(filename);
    Py_XDECREF(lineno);
    Py_XDECREF(kwargs);
    Py_XDECREF(args);
    Py_XDECREF(default_args);
    Py_XDECREF(callback_args);

    return 0;
}

static int profile_func_return(PyObject *obj, PyFrameObject *frame, int what, PyObject *arg) {
    if (what != PyTrace_RETURN || !return_callback) return 0;

    PyObject *func_name, *filename, *lineno, *kwargs, *args, *default_args;
    if (extract_args_from_frame(frame, &func_name, &filename, &lineno, &kwargs, &args, &default_args, arg) != 0)
        return 0;

    PyObject *callback_args = Py_BuildValue("OOOOOOO", func_name, filename, lineno, kwargs, args, default_args, arg ? arg : Py_None);
    Py_XDECREF(PyObject_CallObject(return_callback, callback_args));

    Py_XDECREF(func_name);
    Py_XDECREF(filename);
    Py_XDECREF(lineno);
    Py_XDECREF(kwargs);
    Py_XDECREF(args);
    Py_XDECREF(default_args);
    Py_XDECREF(callback_args);

    return 0;
}

static PyObject *py_on_call(PyObject *self, PyObject *args) {
    PyObject *cb;
    if (!PyArg_ParseTuple(args, "O", &cb)) return NULL;
    if (!PyCallable_Check(cb)) {
        PyErr_SetString(PyExc_TypeError, "Expected a callable");
        return NULL;
    }

    Py_XINCREF(cb);
    Py_XDECREF(call_callback);
    call_callback = cb;

    PyEval_SetProfile(profile_func_call, NULL);
    Py_RETURN_NONE;
}

static PyObject *py_on_return(PyObject *self, PyObject *args) {
    PyObject *cb;
    if (!PyArg_ParseTuple(args, "O", &cb)) return NULL;
    if (!PyCallable_Check(cb)) {
        PyErr_SetString(PyExc_TypeError, "Expected a callable");
        return NULL;
    }

    Py_XINCREF(cb);
    Py_XDECREF(return_callback);
    return_callback = cb;

    PyEval_SetProfile(profile_func_return, NULL);
    Py_RETURN_NONE;
}

static PyMethodDef ProfilerMethods[] = {
    {"on_call", py_on_call, METH_VARARGS, "Register call event callback"},
    {"on_return", py_on_return, METH_VARARGS, "Register return event callback"},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef ProfilerModule = {
    PyModuleDef_HEAD_INIT,
    "func_profiler",
    NULL,
    -1,
    ProfilerMethods
};

PyMODINIT_FUNC PyInit_func_profiler(void) {
    return PyModule_Create(&ProfilerModule);
}