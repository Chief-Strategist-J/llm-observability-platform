# Java Spring Boot Example Project

This is a standalone Spring Boot project designed for testing compiler diagnostics, runtime instrumentation, and tracing with `pylow`.

## Project Scaffolding (How to Create From Scratch)
To bootstrap this default Maven project structure from the command line, run:
```bash
# Generate the quickstart project structure
mvn archetype:generate \
  -DgroupId=com.example \
  -DartifactId=java-springboot \
  -DarchetypeArtifactId=maven-archetype-quickstart \
  -DinteractiveMode=false
```
Then, update `pom.xml` to include Spring Boot dependencies and write your application classes.

## How to Run, Debug, and Code


### How to Run
* **Native Toolchain:** Run the Spring Boot application using Maven:
  ```bash
  mvn spring-boot:run
  ```
* **Via pylow:** Run via the unified toolchain front-door:
  ```bash
  pylow uni run src/main/java/com/example/DemoApplication.java
  ```

### How to Debug
* **Native Toolchain:** Start the application in debug mode and attach using Java Debugger (`jdb`):
  ```bash
  mvn spring-boot:run -Dspring-boot.run.jvmArguments="-Xdebug -Xrunjdwp:transport=dt_socket,server=y,suspend=y,address=5005"
  jdb -attach 5005
  ```
* **Via pylow (Interactive):** Launch interactive debugging automatically:
  ```bash
  pylow uni debug src/main/java/com/example/DemoApplication.java
  ```
* **Via pylow (Step Debugging):** Capture step-by-step local variable snapshots:
  ```bash
  pylow debug-steps src/main/java/com/example/DemoApplication.java --break DemoApplication:6 --out jsteps
  ```

### How to Code
* Open [DemoApplication.java](file:///home/btpl-lap-22/live/obs/packages/python/pylow/examples/java-springboot/src/main/java/com/example/DemoApplication.java) to edit the main app entry.
* Open [HelloController.java](file:///home/btpl-lap-22/live/obs/packages/python/pylow/examples/java-springboot/src/main/java/com/example/controller/HelloController.java) to add or modify endpoints.
* Recompile and run using `mvn clean compile`.

---

## 35+ Critical Daily Java / Spring Boot Commands

### Maven Build & Lifecycle
1. `mvn clean` - Cleans target directory
2. `mvn compile` - Compiles production source code
3. `mvn test-compile` - Compiles test source code
4. `mvn test` - Runs unit tests
5. `mvn package` - Packages compiled code into JAR/WAR
6. `mvn install` - Installs package to local repository
7. `mvn dependency:tree` - Displays project dependency tree
8. `mvn dependency:analyze` - Analyzes unused/missing dependencies
9. `mvn spring-boot:run` - Runs Spring Boot app in-place
10. `mvn spring-boot:repackage` - Generates executable fat JAR
11. `mvn spring-boot:start` - Starts Spring Boot in background
12. `mvn spring-boot:stop` - Stops background Spring Boot app

### JVM Diagnostic Tools
13. `jps -lm` - List Java processes with main args
14. `jcmd <PID> Thread.print` - Print thread stack traces (thread dump)
15. `jcmd <PID> VM.version` - Print JVM version details
16. `jcmd <PID> GC.run` - Force garbage collection invocation
17. `jcmd <PID> GC.heap_info` - Display JVM heap statistics
18. `jstack <PID>` - Print Java stack traces of threads
19. `jmap -heap <PID>` - Print detailed heap summaries
20. `jmap -histo:live <PID>` - Print object histogram
21. `jstat -gcutil <PID> 1000` - Monitor garbage collection statistics
22. `jinfo -flags <PID>` - Print JVM flags and arguments
23. `jdb -attach <port>` - Attach CLI debugger to a running JVM

### Unified Dev commands (`pylow`)
24. `pylow uni doctor` - Verify installed toolchains (including Java)
25. `pylow uni detect .` - Detect language specs and toolchains
26. `pylow uni build pom.xml` - Compile Maven project and normalize errors
27. `pylow uni run pom.xml` - Run project via maven / spring-boot
28. `pylow uni debug pom.xml` - Launch interactive Java debugger
29. `pylow uni trace . --pid <PID>` - Auto-attach Java tracers
30. `pylow uni all pom.xml --trace` - Run build/run/trace pipeline

### Trace and Calltree Diagnostics
31. `pylow trace-java <PID> --duration 15` - Execute JFR/jstack Java trace
32. `pylow calltree DemoApplication.java --filter com.example` - Print method trace tree
33. `pylow calltree pom.xml --depth 5` - View high-level call hierarchy
34. `pylow debug-steps DemoApplication.java --break DemoApplication:6` - Start step capture
35. `pylow index-build .` - Index Java source symbols to SQLite database
36. `pylow index-search HelloController` - Locate controllers/classes instantly
