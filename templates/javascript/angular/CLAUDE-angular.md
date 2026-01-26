# Claude Code Guidelines: Angular

> **Extends:** [CLAUDE-javascript.md](../CLAUDE-javascript.md)

## Angular Patterns

### Component Architecture

- **Standalone components** preferred over NgModules
- **Smart/Container** components handle data, **Dumb/Presentational** components display it
- Use signals for reactive state (Angular 16+)
- Use OnPush change detection for performance

```typescript
@Component({
  selector: 'app-user-profile',
  standalone: true,
  imports: [CommonModule, UserCardComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <app-user-card
      [user]="user()"
      [loading]="loading()"
      (edit)="onEdit($event)"
    />
  `,
})
export class UserProfileComponent {
  private userService = inject(UserService);

  userId = input.required<string>();
  user = signal<User | null>(null);
  loading = signal(true);

  constructor() {
    effect(() => {
      this.loading.set(true);
      this.userService.getUser(this.userId()).subscribe({
        next: (user) => this.user.set(user),
        complete: () => this.loading.set(false),
      });
    });
  }

  onEdit(user: User) {
    // Handle edit
  }
}
```

### Services and Dependency Injection

- Use `inject()` function over constructor injection
- Provide services at appropriate level (root, component, route)
- Use `providedIn: 'root'` for singletons

```typescript
@Injectable({ providedIn: 'root' })
export class UserService {
  private http = inject(HttpClient);
  private apiUrl = inject(API_URL);

  getUser(id: string): Observable<User> {
    return this.http.get<User>(`${this.apiUrl}/users/${id}`);
  }

  createUser(data: CreateUserDto): Observable<User> {
    return this.http.post<User>(`${this.apiUrl}/users`, data);
  }
}
```

### Signals (Angular 16+)

- Use `signal()` for component state
- Use `computed()` for derived state
- Use `effect()` for side effects
- Prefer signals over BehaviorSubject for new code

```typescript
// Component state with signals
export class CounterComponent {
  count = signal(0);
  doubled = computed(() => this.count() * 2);

  increment() {
    this.count.update(c => c + 1);
  }
}
```

### RxJS Patterns

- Use `async` pipe in templates — avoid manual subscriptions
- Use `takeUntilDestroyed()` for cleanup when subscribing
- Prefer declarative streams over imperative code
- Use appropriate operators: `switchMap`, `mergeMap`, `exhaustMap`

```typescript
@Component({
  template: `
    <div *ngIf="user$ | async as user">
      {{ user.name }}
    </div>
  `,
})
export class UserComponent {
  private route = inject(ActivatedRoute);
  private userService = inject(UserService);

  user$ = this.route.params.pipe(
    map(params => params['id']),
    switchMap(id => this.userService.getUser(id)),
  );
}
```

### Forms

- Use Reactive Forms for complex forms
- Use typed forms (FormGroup, FormControl with generics)
- Create form in component, not template

```typescript
interface LoginForm {
  email: FormControl<string>;
  password: FormControl<string>;
  rememberMe: FormControl<boolean>;
}

@Component({...})
export class LoginComponent {
  form = new FormGroup<LoginForm>({
    email: new FormControl('', { nonNullable: true, validators: [Validators.required, Validators.email] }),
    password: new FormControl('', { nonNullable: true, validators: [Validators.required] }),
    rememberMe: new FormControl(false, { nonNullable: true }),
  });

  onSubmit() {
    if (this.form.valid) {
      const { email, password, rememberMe } = this.form.getRawValue();
      this.authService.login(email, password, rememberMe);
    }
  }
}
```

### Routing

- Use lazy loading for feature modules/routes
- Use route guards for access control
- Use resolvers for data prefetching

```typescript
export const routes: Routes = [
  {
    path: 'dashboard',
    loadComponent: () => import('./dashboard/dashboard.component'),
    canActivate: [authGuard],
    resolve: { user: userResolver },
  },
];

// Functional guard
export const authGuard: CanActivateFn = () => {
  const authService = inject(AuthService);
  const router = inject(Router);

  return authService.isLoggedIn() || router.createUrlTree(['/login']);
};
```

### HTTP and API

- Use HttpClient with typed responses
- Create interceptors for auth, error handling, logging
- Use functional interceptors (Angular 15+)

```typescript
export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const authService = inject(AuthService);
  const token = authService.getToken();

  if (token) {
    req = req.clone({
      setHeaders: { Authorization: `Bearer ${token}` },
    });
  }

  return next(req);
};
```

## Project Structure

```
src/app/
├── core/                 # Singleton services, guards, interceptors
├── shared/               # Shared components, directives, pipes
├── features/             # Feature modules/components
│   ├── dashboard/
│   ├── users/
│   └── settings/
└── app.routes.ts         # Root routing config
```

## Testing

- Use Angular Testing Library for component tests
- Use `TestBed` for integration tests
- Mock services with `jasmine.createSpyObj` or jest mocks

```typescript
describe('UserProfileComponent', () => {
  it('should display user name', async () => {
    const userService = jasmine.createSpyObj('UserService', ['getUser']);
    userService.getUser.and.returnValue(of({ name: 'John' }));

    await render(UserProfileComponent, {
      providers: [{ provide: UserService, useValue: userService }],
      componentInputs: { userId: '123' },
    });

    expect(screen.getByText('John')).toBeInTheDocument();
  });
});
```
