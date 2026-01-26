# Claude Code Guidelines: Ruby

> **Extends:** [CLAUDE-base.md](../CLAUDE-base.md)

## Language Standards

- **Ruby 3.2+** for modern features
- Follow **Ruby Style Guide**
- Use **RuboCop** for linting
- Use **Bundler** for dependency management

## Project Structure

```
project/
├── Gemfile
├── Gemfile.lock
├── lib/
│   ├── my_app.rb             # Main entry point
│   ├── my_app/
│   │   ├── version.rb
│   │   ├── configuration.rb
│   │   ├── models/
│   │   ├── services/
│   │   ├── repositories/
│   │   └── errors.rb
├── spec/
│   ├── spec_helper.rb
│   ├── models/
│   └── services/
└── bin/
```

## Code Style

### Naming Conventions

- `snake_case` for methods, variables, files
- `PascalCase` for classes and modules
- `SCREAMING_SNAKE_CASE` for constants
- Predicate methods end with `?`
- Dangerous methods end with `!`

### Modern Ruby Features

```ruby
# frozen_string_literal: true

# Pattern matching (Ruby 3.0+)
case user
in { role: 'admin', active: true }
  grant_admin_access
in { role: 'user', active: true }
  grant_user_access
in { active: false }
  deny_access
end

# Endless method definition
def full_name = "#{first_name} #{last_name}"

# Hash shorthand (Ruby 3.1+)
def create_user(name:, email:)
  User.new(name:, email:)  # Same as name: name, email: email
end

# Data class (Ruby 3.2+)
User = Data.define(:id, :name, :email) do
  def display_name
    "#{name} <#{email}>"
  end
end

# Numbered block parameters
users.map { _1.name.upcase }
users.each { puts "#{_1.name}: #{_2}" }  # With index
```

### Classes and Modules

```ruby
# frozen_string_literal: true

module MyApp
  class User
    attr_reader :id, :email, :name, :created_at

    def initialize(id:, email:, name:, created_at: Time.now)
      @id = id
      @email = email
      @name = name
      @created_at = created_at
    end

    def active?
      @active
    end

    def activate!
      @active = true
      self
    end

    def to_h
      { id:, email:, name:, created_at: }
    end
  end
end

# Concerns/Mixins
module Timestampable
  def touch
    @updated_at = Time.now
  end

  def created_ago
    Time.now - created_at
  end
end

class Post
  include Timestampable
end
```

### Error Handling

```ruby
# frozen_string_literal: true

module MyApp
  class Error < StandardError; end

  class NotFoundError < Error
    attr_reader :resource, :id

    def initialize(resource, id)
      @resource = resource
      @id = id
      super("#{resource} with ID #{id} not found")
    end
  end

  class ValidationError < Error
    attr_reader :errors

    def initialize(errors)
      @errors = errors
      super("Validation failed: #{errors.join(', ')}")
    end
  end
end

# Usage
def find_user!(id)
  users.find { _1.id == id } || raise(NotFoundError.new('User', id))
end

begin
  user = find_user!(id)
rescue NotFoundError => e
  logger.warn("User not found: #{e.id}")
  nil
end
```

### Service Objects

```ruby
# frozen_string_literal: true

module MyApp
  module Services
    class CreateUser
      def initialize(repository:, notifier:)
        @repository = repository
        @notifier = notifier
      end

      def call(params)
        validate!(params)

        user = User.new(
          id: SecureRandom.uuid,
          email: params[:email],
          name: params[:name]
        )

        @repository.save(user)
        @notifier.send_welcome_email(user)

        Result.success(user)
      rescue ValidationError => e
        Result.failure(e.errors)
      end

      private

      def validate!(params)
        errors = []
        errors << 'Email is required' if params[:email].nil? || params[:email].empty?
        errors << 'Name is required' if params[:name].nil? || params[:name].empty?
        raise ValidationError, errors unless errors.empty?
      end
    end
  end
end
```

### Result Objects

```ruby
# frozen_string_literal: true

module MyApp
  class Result
    attr_reader :value, :error

    def self.success(value)
      new(value:, success: true)
    end

    def self.failure(error)
      new(error:, success: false)
    end

    def initialize(value: nil, error: nil, success:)
      @value = value
      @error = error
      @success = success
    end

    def success? = @success
    def failure? = !@success

    def and_then(&block)
      return self if failure?

      block.call(value)
    end

    def or_else(&block)
      return self if success?

      block.call(error)
    end

    def unwrap!
      raise error if failure?

      value
    end
  end
end

# Usage
result = create_user.call(params)
  .and_then { |user| send_notification.call(user) }
  .and_then { |user| Result.success(user.to_h) }

if result.success?
  render json: result.value
else
  render json: { errors: result.error }, status: :unprocessable_entity
end
```

### Dependency Injection

```ruby
# frozen_string_literal: true

module MyApp
  class Container
    class << self
      def repository
        @repository ||= Repositories::PostgresUserRepository.new(database)
      end

      def user_service
        @user_service ||= Services::UserService.new(
          repository:,
          notifier:
        )
      end

      def database
        @database ||= Database.connect(ENV.fetch('DATABASE_URL'))
      end

      def notifier
        @notifier ||= Notifiers::EmailNotifier.new
      end
    end
  end
end

# Usage
user_service = MyApp::Container.user_service
```

### Configuration

```ruby
# frozen_string_literal: true

module MyApp
  class Configuration
    attr_accessor :database_url, :redis_url, :log_level

    def initialize
      @database_url = ENV.fetch('DATABASE_URL', nil)
      @redis_url = ENV.fetch('REDIS_URL', nil)
      @log_level = ENV.fetch('LOG_LEVEL', 'info').to_sym
    end

    def validate!
      raise 'DATABASE_URL is required' unless database_url
    end
  end

  class << self
    def configuration
      @configuration ||= Configuration.new
    end

    def configure
      yield(configuration)
      configuration.validate!
    end
  end
end

# Usage
MyApp.configure do |config|
  config.log_level = :debug
end
```

## Testing (RSpec)

```ruby
# frozen_string_literal: true

RSpec.describe MyApp::Services::CreateUser do
  subject(:service) { described_class.new(repository:, notifier:) }

  let(:repository) { instance_double(MyApp::Repositories::UserRepository) }
  let(:notifier) { instance_double(MyApp::Notifiers::EmailNotifier) }

  describe '#call' do
    let(:params) { { email: 'test@example.com', name: 'Test User' } }

    before do
      allow(repository).to receive(:save)
      allow(notifier).to receive(:send_welcome_email)
    end

    context 'with valid params' do
      it 'returns success result' do
        result = service.call(params)

        expect(result).to be_success
        expect(result.value).to be_a(MyApp::User)
      end

      it 'saves user to repository' do
        service.call(params)

        expect(repository).to have_received(:save).with(
          an_instance_of(MyApp::User)
        )
      end

      it 'sends welcome email' do
        service.call(params)

        expect(notifier).to have_received(:send_welcome_email)
      end
    end

    context 'with missing email' do
      let(:params) { { name: 'Test User' } }

      it 'returns failure result' do
        result = service.call(params)

        expect(result).to be_failure
        expect(result.error).to include('Email is required')
      end
    end
  end
end
```

## Gemfile

```ruby
# frozen_string_literal: true

source 'https://rubygems.org'

ruby '~> 3.2'

gem 'pg'
gem 'sequel'
gem 'dry-validation'
gem 'zeitwerk'

group :development, :test do
  gem 'rspec'
  gem 'rubocop'
  gem 'rubocop-rspec'
  gem 'pry'
end

group :test do
  gem 'factory_bot'
  gem 'faker'
  gem 'simplecov', require: false
end
```
