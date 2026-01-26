# Claude Code Guidelines: Java Spring Boot

Extends [CLAUDE-base.md](./CLAUDE-base.md) with Java and Spring Boot specific patterns.

## Development Approach: API-First (Autonomous Mode)

When building new features, follow API-first design principles autonomously. Do not wait for approval at each step—execute the full implementation unless I intervene.

### Autonomous Workflow

1. **Design the contract first** - Define service interfaces with full Javadoc
2. **Define DTOs and domain models** - Request/response records, validation annotations, entities
3. **Define exceptions** - Custom exceptions for all failure modes
4. **Implement** - Service, repository, controller, mappers
5. **Write tests** - Unit tests, integration tests
6. **Run build** - `mvn clean install` must pass before declaring done

Execute all steps without pausing for confirmation. I trust you to make good decisions.

### When I Intervene

If I say "stop", "wait", "hold on", or express concern about direction:
- Immediately stop what you're doing
- Do not commit or continue the current approach
- Explain your current plan and reasoning
- Wait for my feedback before proceeding

### Handling Ambiguity

When requirements are unclear:
- Make a reasonable assumption and document it
- Prefer the simpler solution
- Flag the assumption in your response so I can correct if needed

### Decision Documentation

When making non-obvious architectural decisions, document the rationale:
- In code: `// Decision: Using X because Y`
- In commits: Note trade-offs considered

## Java Conventions

### General

- Use Java 17+ features (records, sealed classes, pattern matching)
- Prefer immutability - use `final` fields, return unmodifiable collections
- Use `Optional` for nullable return values, never for parameters
- Avoid null - use `Optional`, empty collections, or throw exceptions

### DTOs and Method Parameters

- Use a DTO when a method has more than 3 parameters
- DTOs should be Java records for immutability
- Place DTOs in the appropriate `dto` package
```java
// Request DTO
public record CreateWorkflowRequest(
    @NotBlank String name,
    @Size(max = 500) String description,
    @NotNull WorkflowType type
) {}

// Response DTO
public record WorkflowResponse(
    UUID id,
    String name,
    String description,
    WorkflowStatus status,
    Instant createdAt
) {
    public static WorkflowResponse from(Workflow workflow) {
        return new WorkflowResponse(
            workflow.getId().value(),
            workflow.getName(),
            workflow.getDescription(),
            workflow.getStatus(),
            workflow.getCreatedAt()
        );
    }
}
```

### Domain Models

- Use strongly-typed IDs to prevent mixing up identifiers
- Use builders for complex objects
- Encapsulate business logic in domain models
```java
// Strongly-typed ID
public record WorkflowId(UUID value) {
    public WorkflowId {
        Objects.requireNonNull(value, "WorkflowId cannot be null");
    }
    
    public static WorkflowId generate() {
        return new WorkflowId(UUID.randomUUID());
    }
}

// Domain model with business logic
public class Workflow {
    private final WorkflowId id;
    private String name;
    private WorkflowStatus status;
    
    public void start() {
        if (status != WorkflowStatus.PENDING) {
            throw new InvalidWorkflowStateException(id, status, WorkflowStatus.RUNNING);
        }
        this.status = WorkflowStatus.RUNNING;
    }
}
```

## Spring Boot Specifics

### Decoupling from Spring

- All services MUST have a corresponding interface
- Interface methods should have no framework-specific annotations
- Spring annotations (`@Service`, `@Transactional`, `@Component`) on implementation classes only
- Event publishing should go through an interface, not directly via `ApplicationEventPublisher`
```java
// Interface - no Spring annotations
public interface WorkflowService {
    /**
     * Creates a new workflow.
     *
     * @param workflow the workflow to create
     * @return the created workflow with generated ID
     * @throws DuplicateWorkflowException if a workflow with the same name exists
     */
    Workflow create(Workflow workflow);
}

// Implementation - Spring annotations here
@Service
@Transactional
public class WorkflowServiceImpl implements WorkflowService {
    private final WorkflowRepository workflowRepository;
    
    public WorkflowServiceImpl(WorkflowRepository workflowRepository) {
        this.workflowRepository = workflowRepository;
    }
    
    @Override
    public Workflow create(Workflow workflow) {
        // implementation
    }
}
```

### Controllers

- Controllers live in `provider/spring/{component}/controller/`
- Handle HTTP concerns only - validation, conversion, status codes
- Never contain business logic
```java
@RestController
@RequestMapping("/api/v1/workflows")
public class WorkflowController {
    private final WorkflowService workflowService;
    private final WorkflowMapper workflowMapper;
    
    @PostMapping
    public ResponseEntity<WorkflowResponse> create(
            @Valid @RequestBody CreateWorkflowRequest request) {
        Workflow workflow = workflowMapper.toDomain(request);
        Workflow created = workflowService.create(workflow);
        return ResponseEntity
            .created(URI.create("/api/v1/workflows/" + created.getId().value()))
            .body(WorkflowResponse.from(created));
    }
}
```

### Repository Pattern
```
{component}/repository/
└── WorkflowRepository.java          # Interface using domain models

provider/postgres/{component}/
├── repository/
│   ├── WorkflowEntity.java          # JPA entity
│   ├── WorkflowJpaRepository.java   # Spring Data JPA interface
│   └── WorkflowRepositoryImpl.java  # Implements domain interface
└── mapper/
    └── WorkflowEntityMapper.java    # Entity ↔ Domain conversion
```
```java
// Domain repository interface - no JPA dependency
public interface WorkflowRepository {
    Workflow save(Workflow workflow);
    Optional<Workflow> findById(WorkflowId id);
    List<Workflow> findByStatus(WorkflowStatus status);
    void delete(WorkflowId id);
}

// JPA repository - Spring Data
public interface WorkflowJpaRepository extends JpaRepository<WorkflowEntity, UUID> {
    List<WorkflowEntity> findByStatus(String status);
}

// Implementation bridges domain and JPA
@Repository
public class WorkflowRepositoryImpl implements WorkflowRepository {
    private final WorkflowJpaRepository jpaRepository;
    private final WorkflowEntityMapper mapper;
    
    @Override
    public Workflow save(Workflow workflow) {
        WorkflowEntity entity = mapper.toEntity(workflow);
        WorkflowEntity saved = jpaRepository.save(entity);
        return mapper.toDomain(saved);
    }
}
```

### JPA Entities

- Entities are internal to the postgres provider - never exposed
- Separate from domain models
- Use appropriate JPA annotations for performance
```java
@Entity
@Table(name = "workflows")
public class WorkflowEntity {
    @Id
    private UUID id;
    
    @Column(nullable = false)
    private String name;
    
    @Enumerated(EnumType.STRING)
    private String status;
    
    @CreationTimestamp
    private Instant createdAt;
    
    // JPA requires default constructor
    protected WorkflowEntity() {}
}
```

### Exception Handling
```java
// Base exception
public abstract class BaseException extends RuntimeException {
    private final String code;
    
    protected BaseException(String code, String message) {
        super(message);
        this.code = code;
    }
}

// Domain-specific exception
public class WorkflowNotFoundException extends BaseException {
    public WorkflowNotFoundException(WorkflowId id) {
        super("WORKFLOW_NOT_FOUND", "Workflow not found: " + id.value());
    }
}

// Global exception handler
@RestControllerAdvice
public class GlobalExceptionHandler {
    
    @ExceptionHandler(WorkflowNotFoundException.class)
    public ResponseEntity<ErrorResponse> handleNotFound(WorkflowNotFoundException ex) {
        return ResponseEntity.status(HttpStatus.NOT_FOUND)
            .body(new ErrorResponse(ex.getCode(), ex.getMessage(), Instant.now()));
    }
    
    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ErrorResponse> handleValidation(MethodArgumentNotValidException ex) {
        List<FieldError> errors = ex.getBindingResult().getFieldErrors().stream()
            .map(e -> new FieldError(e.getField(), e.getDefaultMessage()))
            .toList();
        return ResponseEntity.badRequest()
            .body(new ErrorResponse("VALIDATION_ERROR", "Validation failed", errors));
    }
}
```

### Plugin Configuration
```java
// Plugin interface in core/
public interface AiBackend {
    AiResponse complete(AiRequest request);
}

// OpenAI implementation
@Service
@ConditionalOnProperty(name = "ai.backend", havingValue = "openai")
public class OpenAiBackend implements AiBackend {
    // implementation
}

// Anthropic implementation
@Service
@ConditionalOnProperty(name = "ai.backend", havingValue = "anthropic")
public class AnthropicBackend implements AiBackend {
    // implementation
}

// Composition decorator
@Service
@Primary
public class RetryingAiBackend implements AiBackend {
    private final AiBackend delegate;
    private final RetryTemplate retryTemplate;
    
    @Override
    public AiResponse complete(AiRequest request) {
        return retryTemplate.execute(ctx -> delegate.complete(request));
    }
}
```

## Naming Conventions

**Domain:**
- Domain model: `Workflow` (in `{component}/model/`)
- Domain model ID: `WorkflowId` (in `{component}/model/`)

**Services:**
- Service interface: `WorkflowService` (in `{component}/service/`)
- Service implementation: `WorkflowServiceImpl` (in `{component}/service/`)

**Repositories:**
- Repository interface: `WorkflowRepository` (in `{component}/repository/`)
- Repository implementation: `WorkflowRepositoryImpl` (in `provider/postgres/{component}/repository/`)
- JPA repository: `WorkflowJpaRepository` (in `provider/postgres/{component}/repository/`)
- JPA entity: `WorkflowEntity` (in `provider/postgres/{component}/repository/`)
- Entity mapper: `WorkflowEntityMapper` (in `provider/postgres/{component}/mapper/`)

**DTOs:**
- Request DTOs: `CreateWorkflowRequest`, `UpdateWorkflowRequest` (in `{component}/dto/`)
- Response DTOs: `WorkflowResponse` (in `{component}/dto/`)
- DTO mapper: `WorkflowMapper` (in `{component}/mapper/`)

**Controllers:**
- Controller: `WorkflowController` (in `provider/spring/{component}/controller/`)

**Exceptions:**
- Not found: `WorkflowNotFoundException` (in `{component}/exception/`)
- Invalid state: `InvalidWorkflowStateException` (in `{component}/exception/`)

**Plugins:**
- Plugin interface: `AiBackend` (in `core/ai/`)
- Plugin implementation: `OpenAiBackend` (in `provider/openai/`)

## Testing

### Unit Tests
```java
@ExtendWith(MockitoExtension.class)
class WorkflowServiceImplTest {
    @Mock
    private WorkflowRepository workflowRepository;
    
    @InjectMocks
    private WorkflowServiceImpl workflowService;
    
    @Test
    void create_withValidWorkflow_returnsCreatedWorkflow() {
        // Arrange
        Workflow workflow = WorkflowFixtures.pendingWorkflow();
        when(workflowRepository.save(any())).thenReturn(workflow);
        
        // Act
        Workflow result = workflowService.create(workflow);
        
        // Assert
        assertThat(result).isEqualTo(workflow);
        verify(workflowRepository).save(workflow);
    }
}
```

### Controller Tests
```java
@WebMvcTest(WorkflowController.class)
class WorkflowControllerTest {
    @Autowired
    private MockMvc mockMvc;
    
    @MockBean
    private WorkflowService workflowService;
    
    @Test
    void create_withValidRequest_returns201() throws Exception {
        Workflow workflow = WorkflowFixtures.pendingWorkflow();
        when(workflowService.create(any())).thenReturn(workflow);
        
        mockMvc.perform(post("/api/v1/workflows")
                .contentType(MediaType.APPLICATION_JSON)
                .content("""
                    {"name": "Test Workflow", "type": "SEQUENTIAL"}
                    """))
            .andExpect(status().isCreated())
            .andExpect(header().exists("Location"))
            .andExpect(jsonPath("$.name").value("Test Workflow"));
    }
}
```

### Integration Tests
```java
@SpringBootTest
@Testcontainers
class WorkflowRepositoryImplIntegrationTest {
    @Container
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:15");
    
    @Autowired
    private WorkflowRepository workflowRepository;
    
    @Test
    void save_persistsWorkflow() {
        Workflow workflow = WorkflowFixtures.pendingWorkflow();
        
        Workflow saved = workflowRepository.save(workflow);
        Optional<Workflow> found = workflowRepository.findById(saved.getId());
        
        assertThat(found).isPresent();
        assertThat(found.get().getName()).isEqualTo(workflow.getName());
    }
}
```

## Quality Gates (Self-Enforced)

Before declaring a feature complete, verify:

- [ ] Service interface has complete Javadoc
- [ ] DTOs use Java records with validation annotations
- [ ] Custom exceptions for all failure cases
- [ ] All layers implemented (controller → service → repository)
- [ ] New extension points are interface-based and pluggable
- [ ] Domain models encapsulate business logic
- [ ] Strongly-typed IDs for all entities
- [ ] Unit tests for all classes (>80% coverage)
- [ ] Integration tests with Testcontainers
- [ ] `mvn clean install` passes
