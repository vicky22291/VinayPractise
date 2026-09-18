# Named Arguments for SQL Functions

- Source: https://www.databricks.com/blog/named-arguments-sql-functions
- Published: 2023-11-13
- Authors: Daniel Tenedorio, Xinyi Yu, Allison Wang, Wenchen Fan, Serge Rielau, Richard Yu
- Categories: engineering, data-engineering
- Images: 0 total, 0 extracted as architecture

Today, we introduce the new availability of named arguments for SQL functions. With this feature, you can invoke functions in more flexible ways. In this blog, we begin by introducing what this feature looks like, then show what it can do in the context of SQL user-defined functions (UDFs), and finally explore how it works with built-in functions. In sum, named arguments are a new useful way to make work easier for both heavy and light SQL users.

## What are Named Arguments?

In many programming languages, function definitions may include default values for one or more arguments. For instance, in Python, we can define a method like the following:

When a user wants to invoke this function, they can choose to do the following:

This is an example of a keyword argument, wherein we assign a parameter by associating the parameter name with its corresponding argument value. It is a flexible form of function invocation. This is especially useful in contexts where certain parameters are optional or there are large numbers of possible parameters for the function.

Today, we announce a similar syntax for the SQL language in Apache Spark 3.5 and Databricks Runtime 14.1. For example:

In this syntax, instead of using an equals sign, we use the “fat arrow” symbol (=>). This named argument *expression* `paramA => 6` is equivalent to `z = 8` in the Python function invocation. Having established this syntax, let us now consider how it works for different types of SQL functions.

## Using Named Arguments with SQL UDFs

Let’s take a look at the new introduction of named arguments for the Databricks SQL UDFs from [Introducing SQL User-Defined Functions](https://www.databricks.com/blog/2021/10/20/introducing-sql-user-defined-functions.html), which grant flexibility for users to extend and customize their queries for their own needs. It is also possible for users to plug in Python routines and register them as SQL functions as described in [Power to the SQL People: Introducing Python UDFs in Databricks SQL](https://www.databricks.com/blog/2022/07/22/power-to-the-sql-people-introducing-python-udfs-in-databricks-sql.html). As of today, these UDFs are ubiquitous parts of Databricks users’ applications.

The new support for named arguments that we announce today is consistent with the support for built-in functions described above. Let’s look at an example where we create a user-defined function with the following SQL statement:

Just like in the case of the `mask` function, we can make the following call:

This is exceptionally useful for UDFs where the input parameter lists grow long. The feature allows SQL users to specify only a few values during function invocation instead of enumerating them all by position. Here, we can take advantage of the fact that all SQL UDF definitions include user-specified argument names; this is already enforced by the syntax.

## Using Named Arguments with Built-in Spark SQL Functions

This feature also works in Apache Spark. For example, its mask SQL function has five input parameters, of which the last four are optional. In positional order, these parameters are named:

1. `str` (STRING, required)
2. `upperChar` (STRING, optional)
3. `lowerChar` (STRING, optional)
4. `digitChar` (STRING, optional)
5. `otherChar` (STRING, optional)

We can invoke the `mask` SQL function using a call like the following. Here we want to change the argument assignment of `digitChar` and want the other optional parameters to still have the same values. In a language where only positional arguments are supported, the calling syntax looks like this:

This is not ideal because even if we know default values exist, we must specify the arguments for other optional parameters. It becomes evident here that if we scale a function’s parameter list into the hundreds, it becomes ridiculous to enumerate many previous parameter values to only change one that you wanted later in the list.

With named arguments, everything changes. We can now use the following syntax:

With keyword arguments, we can just specify the parameter name `digitChar` and assign the value `d`. This means that we no longer have to enumerate the values of optional parameters in the preceding positions of `digitChar`. Additionally, we can now have more readable code and concise function invocation.

## Named Arguments Also Work With Built-in Databricks Functions

Named arguments have become a crucial component of many SQL functions introduced in Databricks Runtime 14.1.

For instance, we have the function `read_files,` which has hundreds of parameters because it has a long list of configurations that can be defined ([see documentation](https://docs.databricks.com/en/sql/language-manual/functions/read_files.html)). As a result, some parameters must be optional due to this design and must have their values assigned using named arguments.

Multiple other SQL functions are also being implemented that support named arguments. During this journey, we discover situations where value assignments using keyword arguments are the only reasonable way to specify information.

## Conclusion: Named Arguments Make Your Life Better

This feature gives us quality-of-life improvements and useability boosts in many SQL use cases. It lets users create functions and later invoke them in concise and readable ways. We also show how this feature is critical infrastructure for many initiatives currently ongoing in Databricks Runtime. Named argument support is an indispensable feature and makes it easier to write and call functions of many different types, both now and later in the future. Named arguments are available in Databricks Runtime 14.1 and later, and Apache Spark 3.5. Enjoy, and happy querying!
