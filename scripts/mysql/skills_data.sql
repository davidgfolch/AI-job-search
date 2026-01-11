-- Migration SQL for job_skills table
INSERT INTO job_skills (name, description, learning_path, disabled) VALUES 
('PostgreSQL', 'Advanced open-source relational database management system with ACID compliance, extensive SQL support, and powerful extensibility features', '["https://www.postgresql.org/docs/","https://www.coursera.org/postgresql","https://youtube.com/@PostgreSQL"]', 0),
('Spring Batch', 'Lightweight batch processing framework for Spring that enables robust job execution, transaction management, and batch operations for enterprise systems', '["https://spring.io/projects/spring-batch","https://www.coursera.org/spring-batch","https://youtube.com/@SpringBootPro"]', 0),
('Quarkus', 'Full-stack, Kubernetes-native Java framework optimized for cloud-native development with fast startup times, low memory usage, and support for both JVM and native compilation using GraalVM', '["https://quarkus.io","https://www.coursera.org/quarkus","https://youtube.com/@QuarkusTutorials"]', 0),
('Apache Camel', 'Versatile open-source integration framework based on Enterprise Integration Patterns for routing, mediation, and connecting disparate systems', '["https://camel.apache.org/","https://www.coursera.org/camel","https://youtube.com/@ApacheCamel"]', 0),
('Kubernetes', 'Open-source container orchestration platform that automates deployment, scaling, and management of containerized applications across clusters', '["https://kubernetes.io/docs/","https://www.coursera.org/kubernetes","https://youtube.com/@KubernetesOfficial"]', 0),
('AWS', 'Cloud computing platform offering on-demand IT services including computing, storage, networking, and databases with pay-as-you-go pricing', '["https://aws.amazon.com/training/","https://www.coursera.org/aws","https://youtube.com/@aws"]', 0),
('Terraform', 'Infrastructure as Code tool that enables defining and managing cloud infrastructure through declarative configuration files', '["https://www.terraform.io/docs","https://www.coursera.org/learn/terraform","https://youtube.com/@TerraformByHashiCorp"]', 0),
('OpenShift', 'Open-source container orchestration platform developed by Red Hat that combines Kubernetes with enterprise features for building, deploying, and managing containerized applications in hybrid cloud environments', '["https://docs.openshift.com/","https://www.coursera.org/learn/openshift","https://youtube.com/@OpenShift"]', 0),
('Jenkins', 'Open-source automation server that facilitates continuous integration and continuous deployment through configurable pipelines and extensive plugin ecosystem', '["https://www.jenkins.io/doc/","https://www.coursera.org/jenkins","https://youtube.com/@CdacZone"]', 0),
('Golang', 'Statically-typed, compiled programming language designed for simplicity, concurrency, and efficient system and network software development', '["https://golang.org/doc/","https://www.coursera.org/golang","https://youtube.com/@GolangDailies"]', 0),
('Grafana', 'Open-source visualization and monitoring platform for creating interactive dashboards and real-time alerts from diverse data sources', '["https://grafana.com/docs/","https://www.coursera.org/grafana","https://youtube.com/@Grafana"]', 0),
('Prometheus', 'Open-source monitoring and alerting toolkit that collects and stores metrics as time-series data with a flexible query language', '["https://prometheus.io/docs/","https://www.coursera.org/prometheus","https://youtube.com/@PrometheusMonitoring"]', 0),
('Graphite', 'Time-series database and visualization tool for storing, processing, and graphing numeric metrics with flexible querying and aggregation', '["https://graphite.readthedocs.io/","https://www.coursera.org/graphite","https://youtube.com/@GraphiteProject"]', 0),
('Mustache', 'Logic-less template system for HTML, config files, and other content using simple syntax with double braces for variable expansion', '["https://mustache.github.io/","https://www.coursera.org/mustache","https://youtube.com/@MustacheTemplates"]', 1),
('Quasar', 'Open-source Vue.js based framework for building cross-platform applications with a single codebase for web, PWA, mobile, desktop, and browser extensions', '["https://quasar.dev/","https://www.coursera.org/quasar","https://youtube.com/@QuasarFramework"]', 0),
('Remedy', 'Comprehensive IT Service Management suite for managing incidents, problems, changes, and assets while automating ITIL processes to streamline IT operations and improve service delivery', '["https://docs.bmc.com/docs/remedy","https://www.coursera.org/learn/itil-remedyforce","https://youtube.com/@BMCRemedyOnDemand"]', 0),
('React', 'JavaScript library for building reusable user interface components and managing state efficiently in single-page and complex web applications.', '[]', 0),
('Ansible', 'Open-source automation tool for configuration management, application deployment, and orchestration using simple, agentless YAML playbooks.
', '[]', 0),
('Oracle Exadata', 'Engineered database appliance optimized for running Oracle Database with high performance, scalability, and integrated storage and compute resources.
', '[]', 0),
('Spark', 'Distributed data processing engine for large-scale analytics, offering in-memory computation and high-level APIs for batch, streaming, and machine learning workloads.', '[]', 0),
('Hugging Face Transformers', 'Library providing state-of-the-art transformer-based models for natural language processing, computer vision, and audio tasks with easy deployment.', '[]', 0),
('LangChain', 'Framework for building applications powered by large language models, focusing on chaining prompts, tools, memory, and data sources.
', '[]', 0),
('Rust', 'Systems programming language focused on memory safety, performance, and concurrency without a garbage collector, suitable for low-level and high-reliability software.', '[]', 0),
('React Native', 'Framework for building mobile applications using React and JavaScript that compile to native components for iOS and Android.
', '[]', 0),
('Kotlin', 'Modern, statically typed language interoperable with Java, used for Android, backend, and multiplatform development with concise syntax and strong type-safety.', '[]', 0),
('Zapier', NULL, '[]', 0),
('Make', NULL, '[]', 0),
('n8n', NULL, '[]', 0);
