# Claude Code Guidelines: C++

> **Extends:** [CLAUDE-base.md](../CLAUDE-base.md)

## Language Standards

- **C++20** or later
- Use modern C++ idioms
- Follow [C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/)
- Use `clang-format` for formatting
- Use `clang-tidy` for static analysis

## Project Structure

```
project/
├── CMakeLists.txt
├── include/
│   └── myapp/
│       ├── core/
│       ├── services/
│       └── utils/
├── src/
│   ├── core/
│   ├── services/
│   └── main.cpp
├── tests/
│   ├── unit/
│   └── integration/
├── third_party/          # External dependencies
└── docs/
```

## Code Style

### Naming Conventions

- `PascalCase` for types, classes, structs, enums
- `camelCase` for functions, methods, variables
- `SCREAMING_SNAKE_CASE` for macros and constants
- `snake_case` for namespaces and file names
- Prefix member variables with `m_`
- Prefix static members with `s_`

### Modern C++ Practices

```cpp
// Use auto for complex types
auto users = repository.findAll();
auto it = std::find_if(users.begin(), users.end(), predicate);

// Use structured bindings
auto [user, created] = repository.findOrCreate(email);
for (const auto& [key, value] : map) { }

// Use constexpr for compile-time computation
constexpr int maxConnections = 100;
constexpr auto calculateHash(std::string_view input) -> std::size_t;

// Use std::optional for nullable returns
std::optional<User> findById(const std::string& id);

// Use std::variant for type-safe unions
using Result = std::variant<User, Error>;

// Use std::span for non-owning views
void processItems(std::span<const Item> items);

// Use concepts for constraints
template<typename T>
concept Serializable = requires(T t) {
    { t.serialize() } -> std::convertible_to<std::string>;
};

template<Serializable T>
void save(const T& item);
```

### Resource Management (RAII)

```cpp
// Smart pointers for ownership
std::unique_ptr<Resource> createResource();
std::shared_ptr<Service> getSharedService();

// Never use raw new/delete
// Bad
auto* ptr = new MyClass();
delete ptr;

// Good
auto ptr = std::make_unique<MyClass>();

// Use custom deleters when needed
auto file = std::unique_ptr<FILE, decltype(&fclose)>(
    fopen("file.txt", "r"),
    &fclose
);

// RAII wrapper for resources
class DatabaseConnection {
public:
    explicit DatabaseConnection(const std::string& connectionString)
        : m_connection(connect(connectionString)) {}

    ~DatabaseConnection() {
        if (m_connection) {
            disconnect(m_connection);
        }
    }

    // Delete copy, enable move
    DatabaseConnection(const DatabaseConnection&) = delete;
    DatabaseConnection& operator=(const DatabaseConnection&) = delete;
    DatabaseConnection(DatabaseConnection&&) noexcept = default;
    DatabaseConnection& operator=(DatabaseConnection&&) noexcept = default;

private:
    ConnectionHandle m_connection;
};
```

### Error Handling

```cpp
// Use exceptions for exceptional conditions
class AppException : public std::exception {
public:
    explicit AppException(std::string message)
        : m_message(std::move(message)) {}

    const char* what() const noexcept override {
        return m_message.c_str();
    }

private:
    std::string m_message;
};

class NotFoundException : public AppException {
public:
    explicit NotFoundException(const std::string& resource, const std::string& id)
        : AppException(resource + " with ID " + id + " not found") {}
};

// Use std::expected (C++23) or Result type for expected failures
template<typename T, typename E = std::string>
using Result = std::expected<T, E>;

Result<User> findUser(const std::string& id) {
    auto user = repository.findById(id);
    if (!user) {
        return std::unexpected("User not found");
    }
    return *user;
}

// Use noexcept appropriately
void swap(MyClass& other) noexcept;
```

### Classes and Interfaces

```cpp
// Abstract interface
class IUserRepository {
public:
    virtual ~IUserRepository() = default;

    virtual std::optional<User> findById(const std::string& id) = 0;
    virtual std::vector<User> findAll() = 0;
    virtual void save(const User& user) = 0;
    virtual void remove(const std::string& id) = 0;
};

// Implementation
class PostgresUserRepository : public IUserRepository {
public:
    explicit PostgresUserRepository(std::shared_ptr<DatabaseConnection> connection)
        : m_connection(std::move(connection)) {}

    std::optional<User> findById(const std::string& id) override;
    std::vector<User> findAll() override;
    void save(const User& user) override;
    void remove(const std::string& id) override;

private:
    std::shared_ptr<DatabaseConnection> m_connection;
};

// Value types with comparison
struct UserId {
    std::string value;

    auto operator<=>(const UserId&) const = default;
};
```

### Concurrency

```cpp
#include <thread>
#include <mutex>
#include <future>

// Use std::jthread for automatic joining
std::jthread worker([](std::stop_token token) {
    while (!token.stop_requested()) {
        processNextItem();
    }
});

// Protect shared state with mutex
class ThreadSafeCache {
public:
    std::optional<Value> get(const Key& key) const {
        std::shared_lock lock(m_mutex);
        auto it = m_cache.find(key);
        return it != m_cache.end() ? std::optional(it->second) : std::nullopt;
    }

    void set(const Key& key, Value value) {
        std::unique_lock lock(m_mutex);
        m_cache[key] = std::move(value);
    }

private:
    mutable std::shared_mutex m_mutex;
    std::unordered_map<Key, Value> m_cache;
};

// Use std::async for simple async operations
auto future = std::async(std::launch::async, [] {
    return computeExpensiveResult();
});
auto result = future.get();
```

### Templates

```cpp
// Function templates
template<typename Container>
auto findFirst(const Container& container, auto predicate) {
    auto it = std::find_if(container.begin(), container.end(), predicate);
    if (it == container.end()) {
        return std::optional<typename Container::value_type>{};
    }
    return std::optional(*it);
}

// Class templates
template<typename T>
class Repository {
public:
    virtual ~Repository() = default;
    virtual std::optional<T> findById(const std::string& id) = 0;
    virtual void save(const T& entity) = 0;
};

// CRTP for static polymorphism
template<typename Derived>
class Serializable {
public:
    std::string toJson() const {
        return static_cast<const Derived*>(this)->serializeImpl();
    }
};

class User : public Serializable<User> {
    friend class Serializable<User>;
    std::string serializeImpl() const;
};
```

### STL Usage

```cpp
#include <algorithm>
#include <ranges>

// Use ranges (C++20)
auto activeUsers = users
    | std::views::filter([](const User& u) { return u.isActive(); })
    | std::views::transform([](const User& u) { return u.name(); });

// Use algorithms
std::sort(users.begin(), users.end(), [](const User& a, const User& b) {
    return a.createdAt() < b.createdAt();
});

bool allActive = std::all_of(users.begin(), users.end(),
    [](const User& u) { return u.isActive(); });

// Prefer emplace over push
std::vector<User> users;
users.emplace_back("id", "email@example.com", "Name");
```

## CMake Configuration

```cmake
cmake_minimum_required(VERSION 3.20)
project(MyApp VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Compiler warnings
add_compile_options(
    -Wall -Wextra -Wpedantic
    -Werror
    -Wnon-virtual-dtor
    -Wold-style-cast
)

# Main library
add_library(myapp_lib
    src/core/user.cpp
    src/services/user_service.cpp
)

target_include_directories(myapp_lib PUBLIC include)

# Executable
add_executable(myapp src/main.cpp)
target_link_libraries(myapp PRIVATE myapp_lib)

# Tests
enable_testing()
add_subdirectory(tests)
```

## Testing

```cpp
#include <gtest/gtest.h>
#include <gmock/gmock.h>

class MockUserRepository : public IUserRepository {
public:
    MOCK_METHOD(std::optional<User>, findById, (const std::string&), (override));
    MOCK_METHOD(std::vector<User>, findAll, (), (override));
    MOCK_METHOD(void, save, (const User&), (override));
    MOCK_METHOD(void, remove, (const std::string&), (override));
};

class UserServiceTest : public ::testing::Test {
protected:
    void SetUp() override {
        m_repository = std::make_shared<MockUserRepository>();
        m_service = std::make_unique<UserService>(m_repository);
    }

    std::shared_ptr<MockUserRepository> m_repository;
    std::unique_ptr<UserService> m_service;
};

TEST_F(UserServiceTest, FindById_ReturnsUser_WhenExists) {
    User expectedUser{"123", "test@example.com", "Test"};
    EXPECT_CALL(*m_repository, findById("123"))
        .WillOnce(::testing::Return(expectedUser));

    auto result = m_service->findById("123");

    ASSERT_TRUE(result.has_value());
    EXPECT_EQ(result->email(), "test@example.com");
}

TEST_F(UserServiceTest, FindById_ReturnsEmpty_WhenNotFound) {
    EXPECT_CALL(*m_repository, findById("999"))
        .WillOnce(::testing::Return(std::nullopt));

    auto result = m_service->findById("999");

    EXPECT_FALSE(result.has_value());
}
```
