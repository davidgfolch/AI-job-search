# Architecture

## Monorepo structure

This project is a monorepo with the following structure:

- packages/*: common libraries used by apps.
- apps/*: business logic applications:
  - apps/scrapper: scrapper implementations for several job posting web pages, getting job information from online pages and saving in database.
  - apps/aiEnrich: module to enrich database job offers with AI, obtaining structure data from job offer markdown. Uses uv package manager.
  - apps/viewer: UI used to see and manage job offers in our local database.

## Best practices

- Use simpliest SOLID implementation possible.
- Follow repository pattern in data layer.
- Use dependency injection.
- Separate business logic from data access logic.
- Use services for business logic.
- Use repositories for data access logic.
- Use models/entities for data representation.
<!-- - Use controllers for handling requests and responses. -->
- Use DTOs for data transfer between layers.
- Follow clean architecture principles.
- Ensure high cohesion and low coupling between components.
- Write unit tests for all layers.
- Use interfaces to define contracts between layers.
- Follow single responsibility principle for classes and methods.
- Use meaningful names for classes, methods, and variables.
- Avoid code duplication by reusing components and methods.
- Document architecture decisions and patterns used in the project.
- Ensure scalability and maintainability of the architecture.
- Production scope and Test scope should be separated properly.
- Use test helpers to abstract duplicated code.
