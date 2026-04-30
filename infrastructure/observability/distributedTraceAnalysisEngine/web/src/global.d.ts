declare module 'react' {
  export const StrictMode: any;
  export function useState<T>(initial?: T): [T, (next: T) => void];
  export function useEffect(
    effect: () => void | (() => void),
    deps?: any[]
  ): void;
}

declare module 'react-dom/client' {
  export function createRoot(container: Element | DocumentFragment): {
    render(node: any): void;
  };
}

declare module 'react/jsx-runtime' {
  export const jsx: any;
  export const jsxs: any;
  export const Fragment: any;
}

declare namespace JSX {
  interface IntrinsicElements {
    [elemName: string]: any;
  }
}

interface ImportMeta {
  env: Record<string, string | undefined>;
}
