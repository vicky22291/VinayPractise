# Restricting Libraries in JVM Compute Platforms

*Learn how Databricks restricts third party libraries in JVM compute platforms, including Scala, Java, and others.*

- Source: https://www.databricks.com/blog/2022/08/23/restricting-libraries-in-jvm-compute-platforms.html
- Published: 2022-08-23
- Authors: Thomas Garnier
- Categories: tutorials, security-and-trust
- Images: 0 total, 0 extracted as architecture

## Security challenges with Scala and Java libraries

Open source communities have built incredibly useful libraries. They simplify many common development scenarios. Through our [open-source projects](https://www.databricks.com/product/open-source) like Apache Spark, we have learned the challenges of both building projects for everyone and ensuring they work securely. Databricks products benefit from third party libraries and use them to extend existing functionalities. This blog post explores the challenges of using such third party libraries in the Scala and Java languages and proposes solutions to isolate them when needed.

Third-party libraries often provide a wide variety of features. Developers might not be aware of the complexity behind a particular functionality, or know how to disable feature sets easily. In this context, attackers can often leverage unexpected features to gain access to or steal information from a system. For example, a JSON library might use custom tags as a means to inappropriately allow inspecting the contents of local files. Along the same lines, a HTTP library might not think about the risk of local network access or only provide partial restrictions for certain cloud providers.

The security of a third party package goes beyond the code. Open source projects rely on the security of their infrastructure and dependencies. For example, Python and PHP packages were recently [compromised](https://www.bleepingcomputer.com/news/security/popular-python-and-php-libraries-hijacked-to-steal-aws-keys/) to steal AWS keys. Log4j also [highlighted](https://www.databricks.com/blog/2021/12/23/log4j2-vulnerability-cve-2021-44228-research-and-assessment.html) the web of dependencies exploited during security vulnerabilities.

Isolation is often a useful tool to mitigate attacks in this area. Note that isolation can help enhance security for defense-in-depth but it is not a replacement for security patching and open-source contributions.

## Proposed solution

The Databricks security team aims to make secure development simple and straightforward by default. As part of this effort, the team built an isolation framework and integrated it with multiple third party packages. This section explains how it was designed and shares a small part of the implementation. Interested readers can find code samples in [this notebook](https://www.databricks.com/wp-content/uploads/notebooks/db-306-security-restriction-example-notebook.html).

### Per-thread Java SecurityManager

The Java [SecurityManager](https://docs.oracle.com/javase/7/docs/api/java/lang/SecurityManager.html) allows an application to restrict access to resources or privileges through callbacks in the Java source code. It was originally designed to restrict Java applets in the Java 1.0 version. The open-source community uses it for security monitoring, isolation and diagnostics.

The SecurityManager policies apply globally for the entire application. For third party restrictions, we want security policies to apply only for specific code. Our proposed solution attaches a policy to a specific thread and manages the SecurityManager separately.

*Figure 1. Per-thread SecurityManager implementation.*

 

Constantly changing the SecurityManager can introduce [race conditions](https://en.wikipedia.org/wiki/Race_condition). The proposed solution uses reentrant locks to manage setting and removing the SecurityManager. If multiple parts of the code need to change the SecurityManager, it is safer to set the SecurityManager once and never remove it.

The code also respects any pre-installed SecurityManager by forwarding calls that are allowed.

*Figure 2. Forwarding calls to existing SecurityManager.*

### Security policy and rule system

The security policy engine decides if a specific security access is allowed. To ease usage of the engine, accesses are organized into different types. These types of accesses are called PolicyCheck and look like the following:

*Figure 3. Policy access types.*

For brevity, network access, system properties, and other properties are elided from the example.

The security policy engine allows attaching a ruleset to each access check. Each rule in the set is attached to a possible action. If the rule matches, the action is taken. The code uses three types of rules: Caller, Caller regex and default. Caller rules look at the thread call stack for a known function name. The default configuration always matches. If no rule matches, the security policy engine defaults to a global action.

*Figure 4. Basic for the Policy engine to filter SecurityManager calls.*

This engine represents basic building blocks for creating more complicated policies suited to your usage. It supports adding additional rules specific to a new type of access check to filter paths, network IPs or others.

### Example of restrictions

This is a simple security policy to block creation of processes and allow anything else.

*Figure 5. Example to block process creation.*

Here we leverage the rule system to block file read access only to a specific function.

*Figure 6. Example to block access to a file based on regex.*

Here we log the process created by the restricted code.

*Figure 7. Example to log process creation including callstack.*

### JDK17 to deprecate Java SecurityManager and future alternatives

The Java team [decided](https://openjdk.org/jeps/411) to deprecate the SecurityManager in JDK17 and eventually consider removing it. This change will affect the proposal in this blog post. The Java team has multiple projects to support previous usage of the SecurityManager but none so far that will allow similar isolation primitives.

The most viable alternative approach is to inject code in Java core functions using a [Java agent](https://docs.oracle.com/javase/7/docs/api/java/lang/instrument/package-summary.html). The result is similar to the current SecurityManager. The challenge is ensuring accurate coverage for common primitives like file or network access. The first implementation can start with existing SecurityManager callbacks but requires significant testing investments to reduce chances of regression.

Another alternative approach is to use operating system sandboxing primitives for similar results. For example, on Linux we can use [namespaces](https://en.wikipedia.org/wiki/Linux_namespaces) and [seccomp-bpf](https://www.kernel.org/doc/html/v4.19/userspace-api/seccomp_filter.html) to limit resource access. However, this approach requires significant changes in existing applications and may impact performance.
