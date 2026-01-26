# Claude Code Guidelines: Next.js

> **Extends:** [CLAUDE-javascript.md](../CLAUDE-javascript.md)

## Next.js Patterns (App Router)

### Project Structure

```
app/
├── layout.tsx            # Root layout
├── page.tsx              # Home page
├── error.tsx             # Error boundary
├── loading.tsx           # Loading UI
├── not-found.tsx         # 404 page
├── (auth)/               # Route group (no URL impact)
│   ├── login/page.tsx
│   └── register/page.tsx
├── dashboard/
│   ├── layout.tsx        # Nested layout
│   ├── page.tsx
│   └── [id]/page.tsx     # Dynamic route
└── api/                  # API routes
    └── users/route.ts

components/               # Shared components
lib/                      # Utilities, clients
types/                    # TypeScript types
```

### Server vs Client Components

- **Default to Server Components** — render on server, smaller bundles
- Use `'use client'` only when needed (interactivity, hooks, browser APIs)
- Keep client components small and at leaf nodes

```tsx
// Server Component (default) - can fetch data directly
async function UserProfile({ userId }: { userId: string }) {
  const user = await db.user.findUnique({ where: { id: userId } });

  return (
    <div>
      <h1>{user.name}</h1>
      <ClientInteractiveButton userId={userId} />
    </div>
  );
}

// Client Component - for interactivity
'use client';

function ClientInteractiveButton({ userId }: { userId: string }) {
  const [liked, setLiked] = useState(false);

  return (
    <button onClick={() => setLiked(!liked)}>
      {liked ? 'Unlike' : 'Like'}
    </button>
  );
}
```

### Data Fetching

- Fetch data in Server Components directly
- Use React `cache()` for request deduplication
- Use `unstable_cache()` for data caching

```tsx
import { cache } from 'react';

// Deduplicated within a single request
const getUser = cache(async (id: string) => {
  return db.user.findUnique({ where: { id } });
});

// Page component
async function Page({ params }: { params: { id: string } }) {
  const user = await getUser(params.id);
  return <UserProfile user={user} />;
}
```

### Server Actions

- Use for form submissions and mutations
- Define with `'use server'`
- Validate input, return typed responses

```tsx
// actions/user.ts
'use server';

import { revalidatePath } from 'next/cache';
import { z } from 'zod';

const CreateUserSchema = z.object({
  name: z.string().min(2),
  email: z.string().email(),
});

export async function createUser(formData: FormData) {
  const parsed = CreateUserSchema.safeParse({
    name: formData.get('name'),
    email: formData.get('email'),
  });

  if (!parsed.success) {
    return { error: parsed.error.flatten() };
  }

  const user = await db.user.create({ data: parsed.data });
  revalidatePath('/users');
  return { user };
}

// Component using the action
function CreateUserForm() {
  return (
    <form action={createUser}>
      <input name="name" required />
      <input name="email" type="email" required />
      <button type="submit">Create</button>
    </form>
  );
}
```

### Route Handlers (API Routes)

```tsx
// app/api/users/route.ts
import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const page = searchParams.get('page') ?? '1';

  const users = await db.user.findMany({
    skip: (parseInt(page) - 1) * 10,
    take: 10,
  });

  return NextResponse.json(users);
}

export async function POST(request: NextRequest) {
  const body = await request.json();
  const user = await db.user.create({ data: body });
  return NextResponse.json(user, { status: 201 });
}
```

### Layouts and Templates

```tsx
// app/layout.tsx - persistent across navigations
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Header />
        <main>{children}</main>
        <Footer />
      </body>
    </html>
  );
}

// app/dashboard/layout.tsx - nested layout
export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="dashboard">
      <Sidebar />
      <div className="content">{children}</div>
    </div>
  );
}
```

### Loading and Error States

```tsx
// app/dashboard/loading.tsx
export default function Loading() {
  return <DashboardSkeleton />;
}

// app/dashboard/error.tsx
'use client';

export default function Error({ error, reset }: { error: Error; reset: () => void }) {
  return (
    <div>
      <h2>Something went wrong!</h2>
      <button onClick={reset}>Try again</button>
    </div>
  );
}
```

### Metadata

```tsx
// Static metadata
export const metadata: Metadata = {
  title: 'Dashboard',
  description: 'User dashboard',
};

// Dynamic metadata
export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const user = await getUser(params.id);
  return {
    title: user.name,
    openGraph: { images: [user.avatar] },
  };
}
```

### Middleware

```tsx
// middleware.ts (root level)
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const token = request.cookies.get('token');

  if (!token && request.nextUrl.pathname.startsWith('/dashboard')) {
    return NextResponse.redirect(new URL('/login', request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: '/dashboard/:path*',
};
```

### Environment Variables

- `NEXT_PUBLIC_*` for client-side variables
- Non-prefixed for server-only
- Use `.env.local` for local overrides

```typescript
// Server only
const dbUrl = process.env.DATABASE_URL;

// Client accessible
const apiUrl = process.env.NEXT_PUBLIC_API_URL;
```

## Testing

```tsx
import { render, screen } from '@testing-library/react';

// Mock server component data
vi.mock('../lib/db', () => ({
  getUser: vi.fn().mockResolvedValue({ id: '1', name: 'John' }),
}));

it('should render user profile', async () => {
  const Component = await UserProfile({ userId: '1' });
  render(Component);
  expect(screen.getByText('John')).toBeInTheDocument();
});
```
