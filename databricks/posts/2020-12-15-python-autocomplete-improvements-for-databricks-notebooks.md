# Python Autocomplete Improvements for Databricks Notebooks

*Notebook enhancements for Python autocomplete, docstrings, and Koalas library*

- Source: https://www.databricks.com/blog/2020/12/15/python-autocomplete-improvements-for-databricks-notebooks.html
- Published: 2020-12-15
- Authors: Richard Fung, Xinrong Meng, Takuya Ueshin, Hyukjin Kwon, Austin Ford
- Categories: engineering, open-source
- Images: 4 total, 0 extracted as architecture

At Databricks, we strive to provide a world-class development experience for data scientists and engineers, and new features are constantly getting added to our notebooks to improve our users’ productivity.  We are especially excited about the latest of these features, a new autocomplete experience for Python notebooks (powered by the [Jedi library](https://jedi.readthedocs.io/en/latest/) ) and new docstring code hints.  We are launching these features with the Databricks Runtime 7.4 (or DBR 7.4), so you can take advantage of this experience in Python notebooks that run on clusters with DBR 7.4 or later.

You activate the new autocomplete functionality by pressing the **Tab **key. Once you do so, the system examines the input at the cursor’s position to show you candidates for the completion of your code and those candidates’ type information based on your notebook’s current state. To get additional help on a completed name, press the **Shift+Tab** key to open a docstring code hint.

We are also launching a new version of the [Koalas library](https://koalas.readthedocs.io/en/latest/) (version 1.4.0) with support for these new autocomplete and docstring features, which comes pre-packaged with DBR 7.5.  The Koalas library is a drop-in replacement for the popular pandas Python library in data science; it uses Apache Spark’s big data processing capabilities on the backend while providing pandas’ familiar API interface to the user.

## Python autocomplete using static code analysis from the Jedi library

Databricks notebooks run Python code using the [IPython REPL](https://ipython.org/ipython-doc/3/development/how_ipython_works.html), an interactive Python interpreter. The [IPython 6.0 REPL](https://ipython.org/) introduced the [Jedi library](https://jedi.readthedocs.io/en/latest/) for code completion, which is the standard for Python autocomplete functionality in Jupyter notebooks. The Jedi library enables significant improvements over our prior autocomplete implementation by running static code analysis to make suggestions. With static code analysis, object names, their types, and function arguments can be resolved without running a cell (command).

*Autocomplete results are available in the Koalas library*

## Python docstring functionality activated by the Shift+Tab key

In addition to the new autocomplete, DBR 7.4 includes docstring hints activated by the **Shift+Tab** keyboard shortcut. Docstrings are read from code comments formatted in [PEP 257](https://www.python.org/dev/peps/pep-0257/), which are inlined as part of the source code. The docstrings contain the same information as [the **help()** function](https://docs.python.org/3/library/functions.html#help) on a resolved object name. Objects are loaded into the Python REPL by running a notebook cell.

*Example of a Koalas library docstring*

## Koalas: a drop-in replacement for the pandas library

Databricks ships the Koalas Python library as a drop-in replacement to the pandas library, a popular library in data science. Koalas takes advantage of  PySpark’s DataFrame API for processing big data on Apache Spark while keeping the API compatible with pandas; see also  [Koalas: Easy Transition from pandas to Apache Spark](https://www.databricks.com/blog/2019/04/24/koalas-easy-transition-from-pandas-to-apache-spark.html) and [the Koalas documentation](https://koalas.readthedocs.io/en/latest/). Databricks released a new Koalas library version 1.4.0 with enhanced autocomplete and docstring to improve your development and refactoring of code in Databricks notebooks.

### Enhanced type annotations for Koalas

In Koalas 1.4.0,  we added return type annotations to major Koalas objects, including  DataFrame, Series, Index, etc. These return type annotations help autocomplete infer the actual data type for precise and reliable suggestions, which will help you use the Koalas library as you’re writing code.

With the full coverage of return type annotations, the Koalas library has better support of autocomplete compared to the pandas library. Due to technical constraints in the pandas library, pandas doesn’t autocomplete in some cases, such as the example below.

* Unable to get autocomplete results in pandas*

*Autocompletion results are available in Koalas*

### Koalas docstrings in the notebook

As part of Koalas 1.4.0, we have added a rich body of docstrings to the Koalas code so developers can quickly digest the Koalas APIs.  Since these APIs are designed and implemented to run in a distributed environment, there can be subtle differences between the Koalas APIs and the corresponding pandas APIs.  With the new docstring hints feature, you can easily inspect these differences by pressing the **Shift+Tab** key to access the docstring rather than reading the source code or searching the documentation.

## Start using the improved autocomplete

To get the best experience with the new autocomplete and docstring features, attach to a DBR 7.4 cluster in order to enable the new features. At the top of your notebook, create a new cell at the top of your notebook to import all your libraries and execute that cell first. Once libraries are imported, autocomplete suggestions are available for the entire notebook. Then, press the **Tab** key for autocomplete or **Shift+Tab** key for docstrings and function parameters as you write your code.

If you don’t plan on running a notebook cell (for example, to do scratch work), then it’s best to keep the import statements and code in the same cell.

To get the latest Koalas autocomplete and docstrings, install the Koalas library 1.4.0 on a DBR 7.4 cluster. The Koalas library is also packaged with the DBR 7.5 release.

## Read more

- [Jedi: static code analysis for Python](https://jedi.readthedocs.io/en/latest/)
- [Koalas: Easy Transition from pandas to Apache Spark](https://www.databricks.com/blog/2019/04/24/koalas-easy-transition-from-pandas-to-apache-spark.html)
- [Koalas API documentation](https://koalas.readthedocs.io/en/latest/): pandas library for Apache Spark
- [Docstrings in PEP 257](https://www.python.org/dev/peps/pep-0257/)
