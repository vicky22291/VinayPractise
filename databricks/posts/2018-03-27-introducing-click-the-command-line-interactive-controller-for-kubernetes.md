# Introducing Click: The Command Line Interactive Controller for Kubernetes

- Source: https://www.databricks.com/blog/2018/03/27/introducing-click-the-command-line-interactive-controller-for-kubernetes.html
- Published: 2018-03-27
- Authors: Nick Lanham
- Categories: engineering, platform
- Images: 2 total, 0 extracted as architecture

[Click](https://github.com/databricks/click) is an open-source tool that lets you quickly and easily run commands against Kubernetes resources, without copy/pasting all the time, and that easily integrates into your existing command line workflows.

At Databricks we use [Kubernetes](https://kubernetes.io/), a lot. We deploy our services (of which there are many) in unique namespaces, across multiple clouds, in multiple regions. Each of those (service, namespace, cloud, region) needs to be specified to target a particular Kubernetes cluster and object. That means that crafting the correct `kubectl` command line can become a feat in and of itself. A slow, error prone feat.

Because it is difficult to target the right Kubernetes resource with `kubectl`, it hampers our ability to deploy, debug, and fix problems. This is enough of a pain point that almost all our engineers who regularly interact with Kubernetes have hacked up some form of shell alias to inject parameters into their kubectl commands to alleviate parts of this.
 `
 After many tedious revisions of our developers’ personal aliases, we felt like there had to be a better way. Out of this requirement, Click was born.

## Motivation

Click remembers the current Kubernetes "thing" (a "resource" in Kubernetes terms), making it easier for the operator to interact with that resource. This was motivated by a common pattern we noticed using, something like:

1. `kubectl get pods`
2. copy the name of the pod
3. `kubectl logs [pasted pod]`
4. ohh right forgot the container
5. `kubectl logs -c [container] [pasted pod]`
6. Then we want the events from the pod too, and so we have to paste again
7. Rinse, repeat

Note that these different actions are often applied to the **same** object (be it a pod, service, deployment, etc). We often want to inspect the logs, then check what version is deployed, or view associated events. This idea of a "current object", inspired us to start writing Click.

Another major motivation was the recognition that the command line was already excellent tool for most of what we were trying to do. Something like "count how many log lines mention a particular alert" is elegantly expressible via a `kubectl -> grep -> wc pipeline`. We felt that encouraging developers to move to something like the Kubernetes dashboard (or some other gui tool) would be a major downgrade in our ability to quickly drill down on the plethora of information available through `kubectl` (or really, through the [Kubernetes API](https://kubernetes.io/docs/concepts/overview/kubernetes-api/)).

**A caveat:** Click isn't intended to be used in a scripting context. `kubectl` is already excellent in that space, and we saw little value in trying to replace any of its functionality there. Click therefore doesn't have a "run one command and exit" mode, but rather always functions as a REPL.

## Overview of Click

Note first that Click is organized like a REPL. When you run it, you're dropped into the "Click shell" where you start running Click commands. So, enough prelude, what does click actually look like? Below is a short clip showing Click in action.

### Click commands

Firstly, Click has comprehensive help built right in. You can just type `help` for a list and brief description of all the commands you can run. From within a Click shell, you can run any specific command with `-h` to get a full description of its usage. From experience, once the "REPL" model of interaction is understood, most users discover how to do what they want without too much trouble.

Click commands can be divided into four categories, so each command does one of the following:

1. Set the current context or namespace (the combination of which I'll call a "scope")
2. Search the current scope for a resource
3. Select a resource returned from the search
4. Operate on the selected resource

The `ctx` command sets the current context, and the `ns` command the current namespace. Click remembers these settings and reflects them in your prompt.

To search for a resource, there are commands like `pods` or `nodes`. These return a list of all the resources that match in the currently set scope. Selecting an object is done by simply specifying its number in the returned list. Again, Click will reflect this selection in its prompt.

Once a resource is selected, we can run more active commands against that resource. For instance, the `logs` command will fetch logs from the selected pod, or the `describe` command will return an output similar to `kubectl describe`.

Click can pass any output to the shell via standard shell operators like `|, >, or >>`. This enables the above log line counting command to be issued as: `logs -c container | grep alertName | wc -c`, much as one would in your favorite shell.

### Quick Iteration

The above model allows for quick iteration on a particular Kubernetes resource. You can quickly find the resource you care about, and then issue multiple commands against it. For instance, from the current scope, you could select a pod, get its description, see any recent events related to the pod, pull the logs from the foo container to a file, and then delete the pod as follows:

1. `pods` // search for pods in the current context and namespace
2. `2` // select the second pod returned (assuming it's the one you want)
3. `describe` // this will output a description of the pod
4. `events` // see recent events
5. `logs -c foo > /tmp/podfoo.log` // save logs to specified file
6. `delete // delete the pod` (this is ask for confirmation)

### Screencast

In the spirit of pictures being worth more than words, here is a screencast that shows off a few (but by no means all) of clicks features.

> [image 2 not annotated: download failed: could not fetch https://camo.githubusercontent.com/5530b1aad49711e3899be326c169ca16cff726fd/68747470733a2f2f696d6775722e636f6d2f6674345748634c2e676966: HTTP Error 403: Forbidden. source: https://camo.githubusercontent.com/5530b1aad49711e3899be326c169ca16cff726fd/68747470733a2f2f696d6775722e636f6d2f6674345748634c2e676966]

[[Screencast]](https://camo.githubusercontent.com/5530b1aad49711e3899be326c169ca16cff726fd/68747470733a2f2f696d6775722e636f6d2f6674345748634c2e676966)

## Getting Click

Click is open source! You can get the code here: [https://github.com/databricks/click](https://github.com/databricks/click)

You can install click via Rust's package manager tool `cargo` by running `cargo install click`. To get `cargo` if you don't have it, check out [(rustup)](https://rustup.rs/)

### Technical Details

This sections covers some of the details regarding Click's implementation. You can safely skip it if you're mostly just interested in using Click.

### Rust

Click is implemented in [Rust](https://www.rust-lang.org/). This was partly because the author just likes writing code in Rust, but also because Click is designed to stay running for a long time and leaking memory would be unacceptable. I also wanted a fast (read instant) start-up time, so people wouldn't be tempted to reach for kubectl to "just run one quick command". Finally, I wanted Click to crash as little as possible. To that end, Rust is a pretty good choice.

### The allure of unwrap

There's been an effort made to remove as many references to unwrap from the Click codebase as possible (or to notate why it's okay when we do use it). This is because unwrap can cause your Rust program to panic and exit in a rather user-unfriendly manner.

Rust without `unwrap` leads to code that has to explicitly handle most error cases, and in turn leads to a system that doesn't die unexpectedly and that generally reports errors in a clean way to the user. Click is not perfect in this regard, but it's quite good, and will continue to get better.

### Communicating with Kubernetes

For most operations Click talks directly to the Kubernetes API server using the api. The `port-forward` and `exec` commands currently leverage `kubectl`, as that functionality has not been replicated in Click. These commands may at some point become self contained, but so far there hasn't been a strong motivation to do so.

## Future

Click is in beta, and as such it's experimental. Over time, with community contributions and feedback, we will continue to improve it and make it more robust. Additionally, at Databricks we use it on a daily basis, and continually fix any issues. Features we plan to add include:

- The ability to apply commands to sets of resources all at once. This would make it trivial, for instance, to pull the logs for all pods in a particular deployment all at once.
- Auto-complete for lots more commands
- Support for all types of Kubernetes resources, including Custom resources
- Support for patching and applying to modify your deployed resources
- The ability to specify what colors click uses, or to turn of color completely.
- Upgrading to the latest version of [Hyper](https://hyper.rs/) (or possibly switching to [Reqwest](https://github.com/seanmonstar/reqwest)).

## Conclusion

We are excited to release this tool to Kubernetes community and hope many of you find it useful. Please file issues at [https://github.com/databricks/click/issues](https://github.com/databricks/click/issues) and make a PR request for your future feature. We are eager to see Click grow and improve based on community feedback.
