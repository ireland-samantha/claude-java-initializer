# Claude Code Guidelines: Kotlin

> **Extends:** [CLAUDE-base.md](../CLAUDE-base.md)

## Language Standards

- **Kotlin 1.9+** for modern features
- Follow **Kotlin Coding Conventions**
- Use **ktlint** for formatting
- Use **Gradle Kotlin DSL** for build scripts

## Project Structure

```
project/
├── build.gradle.kts
├── settings.gradle.kts
├── src/
│   ├── main/kotlin/
│   │   └── com/example/
│   │       ├── Application.kt
│   │       ├── config/
│   │       ├── domain/
│   │       ├── service/
│   │       ├── repository/
│   │       ├── controller/
│   │       └── dto/
│   └── test/kotlin/
│       └── com/example/
└── gradle/
```

## Code Style

### Naming Conventions

- `PascalCase` for classes, interfaces, enums, objects
- `camelCase` for functions, properties, variables
- `SCREAMING_SNAKE_CASE` for constants
- Backing properties: prefix with `_`

### Modern Kotlin Features

```kotlin
// Data classes
data class User(
    val id: String,
    val email: String,
    val name: String,
    val createdAt: Instant = Instant.now()
)

// Sealed classes for exhaustive when
sealed class Result<out T> {
    data class Success<T>(val value: T) : Result<T>()
    data class Failure(val error: AppError) : Result<Nothing>()

    fun <R> map(transform: (T) -> R): Result<R> = when (this) {
        is Success -> Success(transform(value))
        is Failure -> this
    }

    fun <R> flatMap(transform: (T) -> Result<R>): Result<R> = when (this) {
        is Success -> transform(value)
        is Failure -> this
    }
}

// Value classes for type safety
@JvmInline
value class UserId(val value: String)

@JvmInline
value class Email(val value: String) {
    init {
        require(value.contains("@")) { "Invalid email format" }
    }
}

// Context receivers (Kotlin 1.6.20+)
context(LoggingContext, TransactionContext)
fun createUser(request: CreateUserRequest): User {
    log.info("Creating user: ${request.email}")
    return transaction {
        userRepository.save(User(email = request.email, name = request.name))
    }
}

// Scope functions
fun processUser(userId: String): User? {
    return userRepository.findById(userId)
        ?.also { log.info("Found user: ${it.email}") }
        ?.let { enrichUser(it) }
        ?.takeIf { it.isActive }
}
```

### Null Safety

```kotlin
// Use nullable types explicitly
fun findUser(id: String): User? {
    return userRepository.findById(id)
}

// Safe calls and elvis operator
fun getUserName(id: String): String {
    return findUser(id)?.name ?: "Unknown"
}

// Require non-null with message
fun getUser(id: String): User {
    return findUser(id) ?: throw NotFoundException("User", id)
}

// Let for null checking
fun processUser(id: String) {
    findUser(id)?.let { user ->
        sendNotification(user)
        updateLastLogin(user)
    }
}

// requireNotNull and checkNotNull
fun process(input: String?) {
    val nonNullInput = requireNotNull(input) { "Input cannot be null" }
    // Use nonNullInput safely
}
```

### Coroutines

```kotlin
import kotlinx.coroutines.*

// Suspend functions
suspend fun fetchUser(id: String): User {
    return withContext(Dispatchers.IO) {
        userRepository.findById(id)
            ?: throw NotFoundException("User", id)
    }
}

// Concurrent execution
suspend fun fetchUserData(id: String): UserData = coroutineScope {
    val profile = async { fetchProfile(id) }
    val preferences = async { fetchPreferences(id) }

    UserData(
        profile = profile.await(),
        preferences = preferences.await()
    )
}

// Flow for reactive streams
fun observeUsers(): Flow<List<User>> = flow {
    while (true) {
        emit(userRepository.findAll())
        delay(5000)
    }
}.flowOn(Dispatchers.IO)

// Exception handling
suspend fun safeOperation(): Result<User> {
    return try {
        Result.Success(fetchUser("123"))
    } catch (e: Exception) {
        Result.Failure(AppError.fromException(e))
    }
}
```

### Extensions

```kotlin
// Extension functions
fun String.toSlug(): String {
    return this.lowercase()
        .replace(Regex("[^a-z0-9\\s-]"), "")
        .replace(Regex("\\s+"), "-")
}

// Extension properties
val String.isValidEmail: Boolean
    get() = this.matches(Regex("^[A-Za-z0-9+_.-]+@[A-Za-z0-9.-]+$"))

// Generic extensions
inline fun <T, R> T.runIf(condition: Boolean, block: T.() -> R): R? {
    return if (condition) block() else null
}

// Collection extensions
fun <T> List<T>.second(): T? = this.getOrNull(1)

inline fun <T, R : Comparable<R>> Iterable<T>.maxByOrThrow(
    selector: (T) -> R
): T = maxByOrNull(selector) ?: throw NoSuchElementException()
```

### Interfaces and Classes

```kotlin
// Interface with default implementation
interface UserRepository {
    suspend fun findById(id: String): User?
    suspend fun findAll(): List<User>
    suspend fun save(user: User): User
    suspend fun delete(id: String)

    suspend fun findOrFail(id: String): User {
        return findById(id) ?: throw NotFoundException("User", id)
    }
}

// Implementation
class PostgresUserRepository(
    private val database: Database
) : UserRepository {

    override suspend fun findById(id: String): User? = withContext(Dispatchers.IO) {
        database.query("SELECT * FROM users WHERE id = ?", id)
            .firstOrNull()
            ?.toUser()
    }

    override suspend fun save(user: User): User = withContext(Dispatchers.IO) {
        database.execute(
            "INSERT INTO users (id, email, name) VALUES (?, ?, ?)",
            user.id, user.email, user.name
        )
        user
    }
}

// Service with dependency injection
class UserService(
    private val repository: UserRepository,
    private val notificationService: NotificationService
) {
    suspend fun createUser(request: CreateUserRequest): User {
        val user = User(
            id = UUID.randomUUID().toString(),
            email = request.email,
            name = request.name
        )

        repository.save(user)
        notificationService.sendWelcomeEmail(user)

        return user
    }
}
```

### Error Handling

```kotlin
// Sealed error hierarchy
sealed class AppError(message: String) : Exception(message) {
    data class NotFound(val resource: String, val id: String) :
        AppError("$resource with ID $id not found")

    data class Validation(val errors: List<String>) :
        AppError("Validation failed: ${errors.joinToString()}")

    data class Unauthorized(override val message: String = "Unauthorized") :
        AppError(message)

    companion object {
        fun fromException(e: Exception): AppError = when (e) {
            is AppError -> e
            else -> object : AppError(e.message ?: "Unknown error") {}
        }
    }
}

// Throwing custom exceptions
fun getUser(id: String): User {
    return userRepository.findById(id)
        ?: throw AppError.NotFound("User", id)
}

// Result-based error handling
suspend fun createUser(request: CreateUserRequest): Result<User> {
    val errors = validate(request)
    if (errors.isNotEmpty()) {
        return Result.Failure(AppError.Validation(errors))
    }

    return try {
        val user = userService.create(request)
        Result.Success(user)
    } catch (e: Exception) {
        Result.Failure(AppError.fromException(e))
    }
}
```

### DSL Building

```kotlin
// Type-safe builders
class QueryBuilder {
    private val conditions = mutableListOf<String>()
    private val orderClauses = mutableListOf<String>()

    fun where(condition: String) {
        conditions.add(condition)
    }

    fun orderBy(column: String, direction: String = "ASC") {
        orderClauses.add("$column $direction")
    }

    fun build(): String {
        val whereClause = if (conditions.isNotEmpty()) {
            "WHERE ${conditions.joinToString(" AND ")}"
        } else ""

        val orderClause = if (orderClauses.isNotEmpty()) {
            "ORDER BY ${orderClauses.joinToString(", ")}"
        } else ""

        return "$whereClause $orderClause".trim()
    }
}

fun query(block: QueryBuilder.() -> Unit): String {
    return QueryBuilder().apply(block).build()
}

// Usage
val sql = query {
    where("active = true")
    where("role = 'user'")
    orderBy("created_at", "DESC")
}
```

## Testing

```kotlin
import io.kotest.core.spec.style.DescribeSpec
import io.kotest.matchers.shouldBe
import io.kotest.matchers.types.shouldBeInstanceOf
import io.mockk.coEvery
import io.mockk.coVerify
import io.mockk.mockk

class UserServiceTest : DescribeSpec({

    val repository = mockk<UserRepository>()
    val notificationService = mockk<NotificationService>(relaxed = true)
    val service = UserService(repository, notificationService)

    describe("createUser") {
        it("should create user and send welcome email") {
            // Given
            val request = CreateUserRequest(email = "test@example.com", name = "Test")
            coEvery { repository.save(any()) } answers { firstArg() }

            // When
            val result = service.createUser(request)

            // Then
            result.email shouldBe "test@example.com"
            coVerify { repository.save(any()) }
            coVerify { notificationService.sendWelcomeEmail(any()) }
        }
    }

    describe("getUser") {
        context("when user exists") {
            it("should return the user") {
                val user = User(id = "123", email = "test@example.com", name = "Test")
                coEvery { repository.findById("123") } returns user

                val result = service.getUser("123")

                result shouldBe user
            }
        }

        context("when user does not exist") {
            it("should throw NotFoundException") {
                coEvery { repository.findById("999") } returns null

                val exception = shouldThrow<AppError.NotFound> {
                    service.getUser("999")
                }

                exception.resource shouldBe "User"
                exception.id shouldBe "999"
            }
        }
    }
})
```

## Gradle Configuration

```kotlin
// build.gradle.kts
plugins {
    kotlin("jvm") version "1.9.20"
    kotlin("plugin.serialization") version "1.9.20"
}

dependencies {
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-core:1.7.3")
    implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.6.0")

    testImplementation("io.kotest:kotest-runner-junit5:5.8.0")
    testImplementation("io.kotest:kotest-assertions-core:5.8.0")
    testImplementation("io.mockk:mockk:1.13.8")
}

kotlin {
    jvmToolchain(21)
}

tasks.withType<Test>().configureEach {
    useJUnitPlatform()
}
```
