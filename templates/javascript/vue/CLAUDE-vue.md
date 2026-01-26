# Claude Code Guidelines: Vue

> **Extends:** [CLAUDE-javascript.md](../CLAUDE-javascript.md)

## Vue Patterns

### Composition API

- **Use Composition API** with `<script setup>` for all new components
- **TypeScript** with `defineProps` and `defineEmits` for type safety
- Organize code by logical concern, not by option type

```vue
<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';

interface Props {
  userId: string;
  showDetails?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  showDetails: false,
});

const emit = defineEmits<{
  select: [userId: string];
  delete: [userId: string];
}>();

const user = ref<User | null>(null);
const loading = ref(true);

const displayName = computed(() =>
  user.value ? `${user.value.firstName} ${user.value.lastName}` : ''
);

onMounted(async () => {
  user.value = await fetchUser(props.userId);
  loading.value = false;
});
</script>

<template>
  <div v-if="loading">Loading...</div>
  <div v-else-if="user" @click="emit('select', user.id)">
    {{ displayName }}
  </div>
</template>
```

### Composables

- Extract reusable logic into composables
- Prefix composable functions with `use`
- Return refs and functions for reactivity

```typescript
// composables/useUser.ts
export function useUser(userId: Ref<string>) {
  const user = ref<User | null>(null);
  const loading = ref(true);
  const error = ref<Error | null>(null);

  watch(userId, async (id) => {
    loading.value = true;
    try {
      user.value = await fetchUser(id);
    } catch (e) {
      error.value = e as Error;
    } finally {
      loading.value = false;
    }
  }, { immediate: true });

  return { user, loading, error };
}
```

### Reactivity

- Use `ref` for primitives, `reactive` for objects
- Use `computed` for derived state
- Use `watch` / `watchEffect` for side effects
- Use `toRefs` when destructuring reactive objects

```typescript
// Refs for primitives
const count = ref(0);

// Computed for derived values
const doubled = computed(() => count.value * 2);

// Watch for side effects
watch(count, (newVal, oldVal) => {
  console.log(`Count changed from ${oldVal} to ${newVal}`);
});
```

### Component Organization

```
components/
├── base/                 # Base/UI components (BaseButton, BaseInput)
├── feature/              # Feature-specific components
└── layout/               # Layout components (TheHeader, TheSidebar)
```

### Naming Conventions

- **PascalCase** for component files: `UserProfile.vue`
- **PascalCase** for component usage: `<UserProfile />`
- Prefix base components: `Base`, `App`, `V`
- Prefix single-instance components: `The`

### Props and Events

- Define prop types explicitly
- Use prop validation
- Emit events with clear names (past tense for completed actions)

```vue
<script setup lang="ts">
interface Props {
  items: Item[];
  selectedId?: string;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  'item-selected': [item: Item];
  'item-deleted': [itemId: string];
}>();
</script>
```

### State Management (Pinia)

- Use Pinia for global state
- Define stores with Composition API syntax
- Keep stores focused on single domain

```typescript
// stores/user.ts
export const useUserStore = defineStore('user', () => {
  const user = ref<User | null>(null);
  const isLoggedIn = computed(() => user.value !== null);

  async function login(credentials: Credentials) {
    user.value = await authService.login(credentials);
  }

  function logout() {
    user.value = null;
  }

  return { user, isLoggedIn, login, logout };
});
```

### Routing (Vue Router)

- Use typed routes with vue-router
- Lazy load route components
- Use navigation guards for auth

```typescript
const routes: RouteRecordRaw[] = [
  {
    path: '/dashboard',
    component: () => import('./pages/Dashboard.vue'),
    meta: { requiresAuth: true },
  },
];

router.beforeEach((to) => {
  if (to.meta.requiresAuth && !isAuthenticated()) {
    return '/login';
  }
});
```

## Testing

- Use Vue Test Utils with Vitest
- Test component behavior and output
- Mock composables and stores when needed

```typescript
import { mount } from '@vue/test-utils';
import { createTestingPinia } from '@pinia/testing';

it('should display user name', async () => {
  const wrapper = mount(UserProfile, {
    props: { userId: '123' },
    global: {
      plugins: [createTestingPinia()],
    },
  });

  await flushPromises();
  expect(wrapper.text()).toContain('John Doe');
});
```

## Project Structure

```
src/
├── assets/               # Static assets
├── components/           # Vue components
├── composables/          # Composition functions
├── pages/                # Route views
├── router/               # Vue Router config
├── services/             # API services
├── stores/               # Pinia stores
├── types/                # TypeScript types
└── utils/                # Utility functions
```
