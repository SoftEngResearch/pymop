from setuptools import setup, find_packages  # , Extension
# import sys

# Define platform-specific linker args
# extra_link_args = ['-pthread'] if sys.platform != 'win32' else []

# Define the C extensions
# eq_patch_extension = Extension(
#     'pythonmop.builtin_c_instrumentation.eq_patch',
#     sources=['pythonmop/builtin_c_instrumentation/eq_patch.c'],
#     extra_link_args=extra_link_args
# )

# for_patch_extension = Extension(
#     'pythonmop.builtin_c_instrumentation.for_patch',
#     sources=['pythonmop/builtin_c_instrumentation/for_patch.c'],
#     extra_link_args=extra_link_args
# )

# func_profiler_extension = Extension(
#     'pythonmop.builtin_c_instrumentation.func_profiler',
#     sources=['pythonmop/builtin_c_instrumentation/func_profiler.c'],
#     extra_link_args=extra_link_args
# )

setup(
    name = 'pytest-pythonmop',
    version = '1.1.0',
    author = 'Stephen Shen, Mohammed Yaseen, Denini Gabriel, Kevin Guan, Junho Lee, Marcelo d\'Amorim, Owolabi Legunsen',
    author_email = 'zs435@cornell.edu, moha.98.1900@gmail.com, dgs@cin.ufpe.br, kzg5@cornell.edu, yax3ad@virginia.edu, mdamori@ncsu.edu, legunsen@cornell.edu',
    description = 'An MOP-style runtime verification pytest plugin in Python',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    packages = find_packages(),
    package_data={
        '': ['logicplugin/java-packages/*',
             'logicplugin/java-packages/javamop-packages/*',
             'logicplugin/java-packages/javamop-packages/plugins/*'],
    },
    install_requires=open('requirements.txt').readlines(),
    extras_require={
        'dev': open('dev-requirements.txt').readlines(),
    },
    # ext_modules=[eq_patch_extension, for_patch_extension, func_profiler_extension],
    classifiers=[
        'Framework :: Pytest',
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
    ],
)
