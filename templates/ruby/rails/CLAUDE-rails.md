# Claude Code Guidelines: Ruby on Rails

> **Extends:** [CLAUDE-ruby.md](../CLAUDE-ruby.md)

## Rails Patterns

### Project Structure

```
app/
├── controllers/
│   └── api/
│       └── v1/
├── models/
├── services/                 # Business logic
├── queries/                  # Complex queries
├── serializers/              # JSON serialization
├── policies/                 # Authorization (Pundit)
├── jobs/
├── mailers/
└── views/
config/
db/
├── migrate/
└── seeds.rb
lib/
spec/
├── factories/
├── models/
├── requests/
└── services/
```

### Controllers

```ruby
# frozen_string_literal: true

module Api
  module V1
    class UsersController < ApplicationController
      before_action :authenticate_user!
      before_action :set_user, only: %i[show update destroy]

      def index
        users = User.active.page(params[:page]).per(20)
        render json: UserSerializer.new(users).serializable_hash
      end

      def show
        render json: UserSerializer.new(@user).serializable_hash
      end

      def create
        result = Users::CreateService.call(user_params)

        if result.success?
          render json: UserSerializer.new(result.user).serializable_hash,
                 status: :created
        else
          render json: { errors: result.errors }, status: :unprocessable_entity
        end
      end

      def update
        authorize @user

        result = Users::UpdateService.call(@user, user_params)

        if result.success?
          render json: UserSerializer.new(result.user).serializable_hash
        else
          render json: { errors: result.errors }, status: :unprocessable_entity
        end
      end

      def destroy
        authorize @user
        @user.destroy!
        head :no_content
      end

      private

      def set_user
        @user = User.find(params[:id])
      end

      def user_params
        params.require(:user).permit(:name, :email, :password)
      end
    end
  end
end
```

### Models

```ruby
# frozen_string_literal: true

class User < ApplicationRecord
  # Associations
  has_one :profile, dependent: :destroy
  has_many :posts, dependent: :destroy
  has_many :comments, dependent: :destroy

  # Validations
  validates :email, presence: true,
                    uniqueness: { case_sensitive: false },
                    format: { with: URI::MailTo::EMAIL_REGEXP }
  validates :name, presence: true, length: { minimum: 2, maximum: 100 }
  validates :password, length: { minimum: 8 }, if: :password_required?

  # Scopes
  scope :active, -> { where(active: true) }
  scope :created_after, ->(date) { where('created_at > ?', date) }
  scope :with_profile, -> { includes(:profile) }

  # Callbacks
  before_save :downcase_email

  # Enums
  enum :role, { user: 0, admin: 1, moderator: 2 }, prefix: true

  # Class methods
  def self.find_by_email!(email)
    find_by!(email: email.downcase)
  end

  # Instance methods
  def full_name
    "#{first_name} #{last_name}".strip
  end

  def admin?
    role_admin?
  end

  private

  def downcase_email
    self.email = email.downcase
  end

  def password_required?
    new_record? || password.present?
  end
end
```

### Services

```ruby
# frozen_string_literal: true

module Users
  class CreateService
    include ActiveModel::Model

    attr_accessor :user, :errors

    def self.call(...)
      new(...).call
    end

    def initialize(params)
      @params = params
      @errors = []
    end

    def call
      ActiveRecord::Base.transaction do
        create_user
        create_profile
        send_welcome_email
      end

      self
    rescue ActiveRecord::RecordInvalid => e
      @errors = e.record.errors.full_messages
      self
    end

    def success?
      errors.empty?
    end

    private

    attr_reader :params

    def create_user
      @user = User.create!(
        email: params[:email],
        name: params[:name],
        password: params[:password]
      )
    end

    def create_profile
      @user.create_profile!(bio: params[:bio])
    end

    def send_welcome_email
      UserMailer.welcome(@user).deliver_later
    end
  end
end
```

### Query Objects

```ruby
# frozen_string_literal: true

module Users
  class SearchQuery
    def initialize(relation = User.all)
      @relation = relation
    end

    def call(params)
      @relation = filter_by_name(params[:name])
      @relation = filter_by_email(params[:email])
      @relation = filter_by_role(params[:role])
      @relation = filter_by_status(params[:status])
      @relation = order_by(params[:sort])
      @relation
    end

    private

    def filter_by_name(name)
      return @relation if name.blank?

      @relation.where('name ILIKE ?', "%#{name}%")
    end

    def filter_by_email(email)
      return @relation if email.blank?

      @relation.where('email ILIKE ?', "%#{email}%")
    end

    def filter_by_role(role)
      return @relation if role.blank?

      @relation.where(role:)
    end

    def filter_by_status(status)
      case status
      when 'active' then @relation.active
      when 'inactive' then @relation.where(active: false)
      else @relation
      end
    end

    def order_by(sort)
      case sort
      when 'name' then @relation.order(:name)
      when 'newest' then @relation.order(created_at: :desc)
      when 'oldest' then @relation.order(created_at: :asc)
      else @relation.order(created_at: :desc)
      end
    end
  end
end
```

### Serializers (jsonapi-serializer)

```ruby
# frozen_string_literal: true

class UserSerializer
  include JSONAPI::Serializer

  attributes :id, :email, :name, :role, :created_at

  attribute :full_name do |user|
    user.full_name
  end

  has_one :profile, serializer: ProfileSerializer
  has_many :posts, serializer: PostSerializer

  meta do |user|
    { posts_count: user.posts.count }
  end
end
```

### Policies (Pundit)

```ruby
# frozen_string_literal: true

class UserPolicy < ApplicationPolicy
  def index?
    true
  end

  def show?
    true
  end

  def create?
    user.admin?
  end

  def update?
    user.admin? || record == user
  end

  def destroy?
    user.admin? && record != user
  end

  class Scope < Scope
    def resolve
      if user.admin?
        scope.all
      else
        scope.active
      end
    end
  end
end
```

### Background Jobs

```ruby
# frozen_string_literal: true

class ProcessOrderJob < ApplicationJob
  queue_as :default
  retry_on ActiveRecord::Deadlocked, wait: 5.seconds, attempts: 3
  discard_on ActiveJob::DeserializationError

  def perform(order_id)
    order = Order.find(order_id)

    Orders::ProcessService.call(order)
  rescue Orders::ProcessingError => e
    Rails.logger.error("Order processing failed: #{e.message}")
    raise
  end
end
```

### Error Handling

```ruby
# frozen_string_literal: true

class ApplicationController < ActionController::API
  include Pundit::Authorization

  rescue_from ActiveRecord::RecordNotFound, with: :not_found
  rescue_from ActiveRecord::RecordInvalid, with: :unprocessable_entity
  rescue_from Pundit::NotAuthorizedError, with: :forbidden
  rescue_from ActionController::ParameterMissing, with: :bad_request

  private

  def not_found(exception)
    render json: { error: exception.message }, status: :not_found
  end

  def unprocessable_entity(exception)
    render json: { errors: exception.record.errors.full_messages },
           status: :unprocessable_entity
  end

  def forbidden
    render json: { error: 'Forbidden' }, status: :forbidden
  end

  def bad_request(exception)
    render json: { error: exception.message }, status: :bad_request
  end
end
```

## Testing

```ruby
# frozen_string_literal: true

RSpec.describe 'Users API', type: :request do
  describe 'GET /api/v1/users' do
    let!(:users) { create_list(:user, 3) }
    let(:admin) { create(:user, :admin) }

    it 'returns all users' do
      get '/api/v1/users', headers: auth_headers(admin)

      expect(response).to have_http_status(:ok)
      expect(json_response['data'].size).to eq(3)
    end
  end

  describe 'POST /api/v1/users' do
    let(:admin) { create(:user, :admin) }
    let(:valid_params) do
      {
        user: {
          email: 'new@example.com',
          name: 'New User',
          password: 'password123'
        }
      }
    end

    it 'creates a new user' do
      expect {
        post '/api/v1/users', params: valid_params, headers: auth_headers(admin)
      }.to change(User, :count).by(1)

      expect(response).to have_http_status(:created)
      expect(json_response['data']['attributes']['email']).to eq('new@example.com')
    end

    context 'with invalid params' do
      let(:invalid_params) { { user: { email: '' } } }

      it 'returns validation errors' do
        post '/api/v1/users', params: invalid_params, headers: auth_headers(admin)

        expect(response).to have_http_status(:unprocessable_entity)
        expect(json_response['errors']).to be_present
      end
    end
  end
end

# spec/services/users/create_service_spec.rb
RSpec.describe Users::CreateService do
  describe '.call' do
    let(:params) do
      { email: 'test@example.com', name: 'Test User', password: 'password123' }
    end

    it 'creates user and profile' do
      result = described_class.call(params)

      expect(result).to be_success
      expect(result.user).to be_persisted
      expect(result.user.profile).to be_present
    end

    it 'sends welcome email' do
      expect {
        described_class.call(params)
      }.to have_enqueued_mail(UserMailer, :welcome)
    end
  end
end
```
