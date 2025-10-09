# Hello World Quickstart

A simple Spring Boot quickstart application demonstrating RESTful API development with a clean layered architecture.

---

## What you will build

This quickstart provides the basics of building a Spring Boot application. The key topics covered include:

- Starting the application and sending your first request
- The simple architecture that makes up all applications: Controllers, Services & Repositories
- How to package the application

---

## What you will learn

This quickstart will provide the basics of building a Spring Boot application.

### How to get the most out of this quickstart

The sections below describe the best pathway for using this quickstart depending on your situation.

#### I am starting from scratch, I need to build a Spring Boot application with the HelloWorld template

This quickstart will accompany you through the steps of getting a Spring Boot application using the HelloWorld quickstart running locally on your machine. From here, you will need to ensure your machine configuration meets the prerequisites. The next step is to configure your machine by following the Building and Running your application instructions. Use the instructions and guidance in this lab to explore the codebase and understand the implementation.

---

## Prerequisites

To complete this sample app, you need:

- Less than 10 mins
- Java 17 installed with JAVA_HOME configured
- An IDE (IntelliJ IDEA, Eclipse, VS Code, etc.)
- Maven or Gradle installed
- Docker installed (if running with containers)

### Verify that you have all the tools installed

#### Java

```bash
java -version
```

Expected output: Java version 17.x.x

---

## Getting Started - Quickstart Lab

### Quickstart Setup

This section details the configuration for the quickstart HelloWorld Template.

#### API Interface (Swagger)

Service interfaces are defined using Swagger. Refer to the [Swagger documentation](https://swagger.io/) to know more about Swagger.

Refer to the swagger file for this sample application: [api.swagger.yaml](src/main/java/com/example/hello/world/api/api.swagger.yaml)

The Hello service exposes a simple HTTP GET endpoint:

**Endpoint**: `GET /api/hello`

**Response**:
```json
{
  "message": "Hello World!"
}
```

---

## Building and Running

### Build the application

```bash
mvn clean install
```

Or with Gradle:

```bash
gradle build
```

### Run the application

```bash
mvn spring-boot:run
```

Or with Gradle:

```bash
gradle bootRun
```

### Test the endpoint

```bash
curl http://localhost:8080/api/hello
```

Expected response:
```json
{
  "message": "Hello World!"
}
```

---

## Project Structure

```
src/main/java/com/example/hello/world/
├── api/                    # API definitions and DTOs
│   ├── SampleResponse.java
│   └── api.swagger.yaml
├── application/            # Business logic layer
│   └── SampleService.java
├── controller/             # REST controllers
│   └── SampleController.java
├── repository/             # Data access layer
│   └── sample/
│       └── SampleRepository.java
└── Application.java        # Main Spring Boot application
```

---

## Architecture

This application follows a clean layered architecture:

1. **Controller Layer**: Handles HTTP requests and responses
2. **Application/Service Layer**: Contains business logic
3. **Repository Layer**: Manages data access and persistence
4. **API Layer**: Defines DTOs and contracts

---

## Next Steps

- Add database integration
- Implement additional REST endpoints
- Add unit and integration tests
- Configure application properties
- Add logging and monitoring
- Set up CI/CD pipeline

---

## References

- [Spring Boot Documentation](https://spring.io/projects/spring-boot)
- [Spring Web MVC](https://docs.spring.io/spring-framework/reference/web/webmvc.html)
- [Swagger/OpenAPI](https://swagger.io/)
