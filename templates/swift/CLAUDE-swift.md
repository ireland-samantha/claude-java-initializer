# Claude Code Guidelines: Swift

> **Extends:** [CLAUDE-base.md](../CLAUDE-base.md)

## Language Standards

- **Swift 5.9+** for modern features
- Follow **Swift API Design Guidelines**
- Use **SwiftLint** for linting
- Use **Swift Package Manager** for dependencies

## Project Structure

```
MyApp/
├── Package.swift
├── Sources/
│   └── MyApp/
│       ├── App/
│       ├── Models/
│       ├── Services/
│       ├── Repositories/
│       ├── Views/
│       ├── ViewModels/
│       └── Utilities/
└── Tests/
    └── MyAppTests/
```

## Code Style

### Naming Conventions

- `PascalCase` for types, protocols, enum cases
- `camelCase` for functions, properties, variables
- Boolean properties: use `is`, `has`, `should` prefixes
- Factory methods: use `make` prefix

### Modern Swift Features

```swift
// Actors for thread-safe state
actor UserCache {
    private var users: [String: User] = [:]

    func get(_ id: String) -> User? {
        users[id]
    }

    func set(_ user: User) {
        users[user.id] = user
    }
}

// Async/await
func fetchUser(id: String) async throws -> User {
    let data = try await networkClient.get("/users/\(id)")
    return try JSONDecoder().decode(User.self, from: data)
}

// Structured concurrency
func fetchUserData(id: String) async throws -> UserData {
    async let profile = fetchProfile(id: id)
    async let preferences = fetchPreferences(id: id)

    return try await UserData(
        profile: profile,
        preferences: preferences
    )
}

// Result builders
@resultBuilder
struct ArrayBuilder<Element> {
    static func buildBlock(_ components: Element...) -> [Element] {
        components
    }
}

// Property wrappers
@propertyWrapper
struct Trimmed {
    private var value: String = ""

    var wrappedValue: String {
        get { value }
        set { value = newValue.trimmingCharacters(in: .whitespaces) }
    }
}

struct User {
    @Trimmed var name: String
}

// Macros (Swift 5.9+)
@Observable
class UserViewModel {
    var user: User?
    var isLoading = false
}
```

### Protocols and Extensions

```swift
// Protocol with associated types
protocol Repository {
    associatedtype Entity: Identifiable

    func findById(_ id: Entity.ID) async throws -> Entity?
    func findAll() async throws -> [Entity]
    func save(_ entity: Entity) async throws
    func delete(_ id: Entity.ID) async throws
}

// Protocol extension with default implementation
extension Repository {
    func findOrFail(_ id: Entity.ID) async throws -> Entity {
        guard let entity = try await findById(id) else {
            throw RepositoryError.notFound(id: String(describing: id))
        }
        return entity
    }
}

// Conditional conformance
extension Array: Identifiable where Element: Identifiable {
    public var id: [Element.ID] {
        map(\.id)
    }
}
```

### Error Handling

```swift
// Define domain errors
enum AppError: Error, LocalizedError {
    case notFound(resource: String, id: String)
    case validation(message: String)
    case network(underlying: Error)
    case unauthorized

    var errorDescription: String? {
        switch self {
        case .notFound(let resource, let id):
            return "\(resource) with ID \(id) not found"
        case .validation(let message):
            return message
        case .network(let underlying):
            return "Network error: \(underlying.localizedDescription)"
        case .unauthorized:
            return "Unauthorized access"
        }
    }
}

// Result type for expected failures
enum Result<Success, Failure: Error> {
    case success(Success)
    case failure(Failure)

    func map<T>(_ transform: (Success) -> T) -> Result<T, Failure> {
        switch self {
        case .success(let value):
            return .success(transform(value))
        case .failure(let error):
            return .failure(error)
        }
    }

    func flatMap<T>(_ transform: (Success) -> Result<T, Failure>) -> Result<T, Failure> {
        switch self {
        case .success(let value):
            return transform(value)
        case .failure(let error):
            return .failure(error)
        }
    }
}
```

### Dependency Injection

```swift
// Protocol-based DI
protocol UserServiceProtocol {
    func getUser(id: String) async throws -> User
    func createUser(_ request: CreateUserRequest) async throws -> User
}

final class UserService: UserServiceProtocol {
    private let repository: UserRepository
    private let notificationService: NotificationServiceProtocol

    init(
        repository: UserRepository,
        notificationService: NotificationServiceProtocol
    ) {
        self.repository = repository
        self.notificationService = notificationService
    }

    func getUser(id: String) async throws -> User {
        try await repository.findOrFail(id)
    }

    func createUser(_ request: CreateUserRequest) async throws -> User {
        let user = User(
            id: UUID().uuidString,
            email: request.email,
            name: request.name
        )
        try await repository.save(user)
        try await notificationService.sendWelcomeEmail(to: user)
        return user
    }
}

// Container
final class Container {
    static let shared = Container()

    private init() {}

    lazy var userRepository: UserRepository = PostgresUserRepository()

    lazy var notificationService: NotificationServiceProtocol = EmailNotificationService()

    lazy var userService: UserServiceProtocol = UserService(
        repository: userRepository,
        notificationService: notificationService
    )
}
```

### SwiftUI Patterns

```swift
import SwiftUI

// View with ViewModel
struct UserListView: View {
    @StateObject private var viewModel = UserListViewModel()

    var body: some View {
        List {
            ForEach(viewModel.users) { user in
                UserRow(user: user)
            }
        }
        .overlay {
            if viewModel.isLoading {
                ProgressView()
            }
        }
        .alert("Error", isPresented: $viewModel.showError) {
            Button("OK") {}
        } message: {
            Text(viewModel.errorMessage)
        }
        .task {
            await viewModel.loadUsers()
        }
        .refreshable {
            await viewModel.loadUsers()
        }
    }
}

// ViewModel with @Observable (Swift 5.9+)
@Observable
final class UserListViewModel {
    private(set) var users: [User] = []
    private(set) var isLoading = false
    var showError = false
    var errorMessage = ""

    private let userService: UserServiceProtocol

    init(userService: UserServiceProtocol = Container.shared.userService) {
        self.userService = userService
    }

    func loadUsers() async {
        isLoading = true
        defer { isLoading = false }

        do {
            users = try await userService.getAllUsers()
        } catch {
            errorMessage = error.localizedDescription
            showError = true
        }
    }
}

// Reusable component
struct UserRow: View {
    let user: User

    var body: some View {
        HStack {
            AsyncImage(url: user.avatarURL) { image in
                image.resizable()
            } placeholder: {
                Color.gray
            }
            .frame(width: 40, height: 40)
            .clipShape(Circle())

            VStack(alignment: .leading) {
                Text(user.name)
                    .font(.headline)
                Text(user.email)
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        }
    }
}
```

### Codable

```swift
struct User: Codable, Identifiable, Equatable {
    let id: String
    let email: String
    let name: String
    let createdAt: Date

    enum CodingKeys: String, CodingKey {
        case id
        case email
        case name
        case createdAt = "created_at"
    }
}

// Custom decoding
extension User {
    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        id = try container.decode(String.self, forKey: .id)
        email = try container.decode(String.self, forKey: .email)
        name = try container.decode(String.self, forKey: .name)

        let dateString = try container.decode(String.self, forKey: .createdAt)
        guard let date = ISO8601DateFormatter().date(from: dateString) else {
            throw DecodingError.dataCorrupted(
                .init(codingPath: [CodingKeys.createdAt], debugDescription: "Invalid date format")
            )
        }
        createdAt = date
    }
}
```

## Testing

```swift
import XCTest
@testable import MyApp

final class UserServiceTests: XCTestCase {
    var sut: UserService!
    var mockRepository: MockUserRepository!
    var mockNotificationService: MockNotificationService!

    override func setUp() {
        super.setUp()
        mockRepository = MockUserRepository()
        mockNotificationService = MockNotificationService()
        sut = UserService(
            repository: mockRepository,
            notificationService: mockNotificationService
        )
    }

    func testGetUser_ReturnsUser_WhenExists() async throws {
        // Given
        let expectedUser = User(id: "123", email: "test@example.com", name: "Test")
        mockRepository.stubbedUser = expectedUser

        // When
        let user = try await sut.getUser(id: "123")

        // Then
        XCTAssertEqual(user, expectedUser)
    }

    func testGetUser_ThrowsNotFound_WhenNotExists() async {
        // Given
        mockRepository.stubbedUser = nil

        // When/Then
        do {
            _ = try await sut.getUser(id: "999")
            XCTFail("Expected error to be thrown")
        } catch let error as AppError {
            guard case .notFound = error else {
                XCTFail("Expected notFound error")
                return
            }
        } catch {
            XCTFail("Unexpected error: \(error)")
        }
    }

    func testCreateUser_SendsWelcomeEmail() async throws {
        // Given
        let request = CreateUserRequest(email: "new@example.com", name: "New User")

        // When
        _ = try await sut.createUser(request)

        // Then
        XCTAssertTrue(mockNotificationService.welcomeEmailSent)
    }
}

// Mock
final class MockUserRepository: UserRepository {
    var stubbedUser: User?
    var savedUsers: [User] = []

    func findById(_ id: String) async throws -> User? {
        stubbedUser
    }

    func save(_ user: User) async throws {
        savedUsers.append(user)
    }
}
```

## Package.swift

```swift
// swift-tools-version: 5.9

import PackageDescription

let package = Package(
    name: "MyApp",
    platforms: [
        .macOS(.v14),
        .iOS(.v17)
    ],
    products: [
        .library(name: "MyApp", targets: ["MyApp"])
    ],
    dependencies: [
        .package(url: "https://github.com/apple/swift-log.git", from: "1.5.0"),
    ],
    targets: [
        .target(
            name: "MyApp",
            dependencies: [
                .product(name: "Logging", package: "swift-log"),
            ]
        ),
        .testTarget(
            name: "MyAppTests",
            dependencies: ["MyApp"]
        )
    ]
)
```
