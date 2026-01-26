# Claude Code Guidelines: React

> **Extends:** [CLAUDE-javascript.md](../CLAUDE-javascript.md)

## React Patterns

### Component Structure

- **Functional components only** — no class components
- **One component per file** — file name matches component name
- **Colocate related files**: `Button.tsx`, `Button.test.tsx`, `Button.module.css`

```
components/
├── Button/
│   ├── index.ts          # Re-export
│   ├── Button.tsx        # Component
│   ├── Button.test.tsx   # Tests
│   └── Button.module.css # Styles
```

### Component Definition

```tsx
interface ButtonProps {
  variant: 'primary' | 'secondary';
  children: React.ReactNode;
  onClick?: () => void;
  disabled?: boolean;
}

export function Button({ variant, children, onClick, disabled = false }: ButtonProps) {
  return (
    <button
      className={styles[variant]}
      onClick={onClick}
      disabled={disabled}
    >
      {children}
    </button>
  );
}
```

### Hooks

- Extract complex logic into custom hooks
- Prefix custom hooks with `use`
- Keep hooks at the top of the component
- Follow Rules of Hooks strictly

```tsx
function useUser(userId: string) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    let cancelled = false;

    fetchUser(userId)
      .then((data) => !cancelled && setUser(data))
      .catch((err) => !cancelled && setError(err))
      .finally(() => !cancelled && setLoading(false));

    return () => { cancelled = true; };
  }, [userId]);

  return { user, loading, error };
}
```

### State Management

- **Local state**: `useState` for component-specific state
- **Shared state**: React Context for app-wide state (auth, theme)
- **Server state**: React Query or SWR for API data
- **Complex state**: `useReducer` for state with multiple sub-values

```tsx
// Server state with React Query
function UserProfile({ userId }: { userId: string }) {
  const { data: user, isLoading, error } = useQuery({
    queryKey: ['user', userId],
    queryFn: () => fetchUser(userId),
  });

  if (isLoading) return <Skeleton />;
  if (error) return <ErrorMessage error={error} />;
  return <ProfileCard user={user} />;
}
```

### Performance

- Use `React.memo` only when profiling shows benefit
- Use `useMemo`/`useCallback` for expensive computations or stable references
- Avoid inline object/array creation in render when passed as props
- Use `key` prop correctly — stable, unique identifiers

```tsx
// Memoize expensive computation
const sortedItems = useMemo(
  () => items.sort((a, b) => a.name.localeCompare(b.name)),
  [items]
);

// Stable callback reference
const handleClick = useCallback((id: string) => {
  setSelected(id);
}, []);
```

### Forms

- Use controlled components for form inputs
- Use form libraries (React Hook Form) for complex forms
- Validate on blur and submit
- Show inline validation errors

```tsx
function LoginForm() {
  const { register, handleSubmit, formState: { errors } } = useForm<LoginData>();

  const onSubmit = async (data: LoginData) => {
    await login(data);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <input {...register('email', { required: true })} />
      {errors.email && <span>Email is required</span>}
      <button type="submit">Login</button>
    </form>
  );
}
```

### Error Boundaries

- Wrap major sections with Error Boundaries
- Provide fallback UI for errors
- Log errors to monitoring service

```tsx
<ErrorBoundary fallback={<ErrorPage />}>
  <MainContent />
</ErrorBoundary>
```

## Styling

- **CSS Modules** for component-scoped styles
- **Tailwind CSS** for utility-first approach
- Avoid inline styles except for dynamic values
- Use CSS custom properties for theming

## Testing

- Use React Testing Library
- Test behavior, not implementation
- Query by role, label, or text — avoid test IDs when possible
- Test user interactions and accessibility

```tsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

it('should submit form with valid data', async () => {
  const onSubmit = vi.fn();
  render(<LoginForm onSubmit={onSubmit} />);

  await userEvent.type(screen.getByLabelText('Email'), 'test@example.com');
  await userEvent.click(screen.getByRole('button', { name: 'Login' }));

  expect(onSubmit).toHaveBeenCalledWith({ email: 'test@example.com' });
});
```

## Project Structure

```
src/
├── components/           # Reusable UI components
├── features/             # Feature-specific components and logic
├── hooks/                # Custom hooks
├── pages/                # Route components
├── services/             # API clients
├── stores/               # State management
├── types/                # TypeScript types
└── utils/                # Utility functions
```
