// Module declarations for missing TypeScript types.
// This bridges the gap when @types/react is not installed via npm.
// Using ESM-compatible named exports (no `export =` which breaks named imports).

declare module 'react' {
  // ── Core types ──────────────────────────────────────────────────────────────

  export type Key = string | number | bigint;

  export type Ref<T> = RefCallback<T> | RefObject<T> | null;
  export type RefCallback<T> = (instance: T | null) => void;
  export interface RefObject<T> {
    readonly current: T | null;
  }
  export interface MutableRefObject<T> {
    current: T;
  }

  export type ReactNode =
    | ReactElement
    | string
    | number
    | boolean
    | null
    | undefined
    | Iterable<ReactNode>;

  export interface ReactElement<
    P = Record<string, unknown>,
    T extends string | JSXElementConstructor<unknown> = string | JSXElementConstructor<unknown>
  > {
    type: T;
    props: P;
    key: Key | null;
  }

  export type JSXElementConstructor<P> =
    | ((props: P) => ReactNode)
    | (new (props: P) => Component<P>);

  export interface Component<P = Record<string, unknown>, S = Record<string, unknown>> {
    render(): ReactNode;
    props: Readonly<P>;
    state: Readonly<S>;
  }

  export type FC<P = Record<string, unknown>> = FunctionComponent<P>;
  export interface FunctionComponent<P = Record<string, unknown>> {
    (props: P): ReactNode;
    displayName?: string;
  }

  export type PropsWithChildren<P = unknown> = P & { children?: ReactNode };
  export type PropsWithRef<P> = P & { ref?: Ref<unknown> };

  // ── HTML attribute types ─────────────────────────────────────────────────────

  export interface CSSProperties {
    [key: string]: string | number | undefined | null;
  }

  export interface AriaAttributes {
    'aria-label'?: string;
    'aria-labelledby'?: string;
    'aria-hidden'?: boolean | 'true' | 'false';
    'aria-pressed'?: boolean | 'true' | 'false' | 'mixed';
    'aria-expanded'?: boolean | 'true' | 'false';
    'aria-selected'?: boolean | 'true' | 'false';
    'aria-disabled'?: boolean | 'true' | 'false';
    'aria-live'?: 'off' | 'assertive' | 'polite';
    'aria-atomic'?: boolean | 'true' | 'false';
    'aria-busy'?: boolean | 'true' | 'false';
    'aria-controls'?: string;
    'aria-describedby'?: string;
    'aria-current'?: boolean | 'true' | 'false' | 'page' | 'step' | 'location' | 'date' | 'time';
    'aria-haspopup'?: boolean | 'true' | 'false' | 'menu' | 'listbox' | 'tree' | 'grid' | 'dialog';
    'aria-role'?: string;
  }

  export interface DOMAttributes<T> {
    children?: ReactNode;
    onClick?: MouseEventHandler<T>;
    onMouseDown?: MouseEventHandler<T>;
    onMouseMove?: MouseEventHandler<T>;
    onMouseUp?: MouseEventHandler<T>;
    onMouseEnter?: MouseEventHandler<T>;
    onMouseLeave?: MouseEventHandler<T>;
    onKeyDown?: KeyboardEventHandler<T>;
    onKeyUp?: KeyboardEventHandler<T>;
    onChange?: ChangeEventHandler<T>;
    onInput?: FormEventHandler<T>;
    onSubmit?: FormEventHandler<T>;
    onFocus?: FocusEventHandler<T>;
    onBlur?: FocusEventHandler<T>;
    onScroll?: UIEventHandler<T>;
    onWheel?: WheelEventHandler<T>;
    onTouchStart?: TouchEventHandler<T>;
    onTouchEnd?: TouchEventHandler<T>;
    onTouchMove?: TouchEventHandler<T>;
    onPointerDown?: PointerEventHandler<T>;
    onPointerMove?: PointerEventHandler<T>;
    onPointerUp?: PointerEventHandler<T>;
  }

  export interface HTMLAttributes<T> extends AriaAttributes, DOMAttributes<T> {
    id?: string;
    className?: string;
    style?: CSSProperties;
    role?: string;
    tabIndex?: number;
    title?: string;
    ref?: Ref<T>;
    [key: `data-${string}`]: string | undefined;
  }

  export interface ButtonHTMLAttributes<T> extends HTMLAttributes<T> {
    disabled?: boolean;
    type?: 'button' | 'submit' | 'reset';
    form?: string;
    name?: string;
    value?: string | readonly string[] | number;
  }

  export interface InputHTMLAttributes<T> extends HTMLAttributes<T> {
    type?: string;
    value?: string | number | readonly string[];
    defaultValue?: string | number | readonly string[];
    checked?: boolean;
    defaultChecked?: boolean;
    disabled?: boolean;
    placeholder?: string;
    min?: number | string;
    max?: number | string;
    step?: number | string;
    name?: string;
    autoFocus?: boolean;
    readOnly?: boolean;
    required?: boolean;
    autoComplete?: string;
    onChange?: ChangeEventHandler<T>;
    onKeyDown?: KeyboardEventHandler<T>;
  }

  export interface TextareaHTMLAttributes<T> extends HTMLAttributes<T> {
    value?: string;
    defaultValue?: string;
    disabled?: boolean;
    placeholder?: string;
    rows?: number;
    cols?: number;
    readOnly?: boolean;
    required?: boolean;
    onChange?: ChangeEventHandler<T>;
  }

  export interface SelectHTMLAttributes<T> extends HTMLAttributes<T> {
    value?: string | string[] | number;
    defaultValue?: string | string[] | number;
    disabled?: boolean;
    multiple?: boolean;
    required?: boolean;
    onChange?: ChangeEventHandler<T>;
  }

  export interface SVGAttributes<T> extends AriaAttributes, DOMAttributes<T> {
    className?: string;
    style?: CSSProperties;
    id?: string;
    ref?: Ref<T>;
    width?: number | string;
    height?: number | string;
    viewBox?: string;
    fill?: string;
    stroke?: string;
    strokeWidth?: number | string;
    strokeLinecap?: 'butt' | 'round' | 'square' | 'inherit';
    strokeLinejoin?: 'miter' | 'round' | 'bevel' | 'inherit';
    strokeDasharray?: string | number;
    strokeDashoffset?: string | number;
    d?: string;
    cx?: number | string;
    cy?: number | string;
    r?: number | string;
    rx?: number | string;
    ry?: number | string;
    x?: number | string;
    y?: number | string;
    x1?: number | string;
    y1?: number | string;
    x2?: number | string;
    y2?: number | string;
    markerStart?: string;
    markerEnd?: string;
    markerWidth?: number | string;
    markerHeight?: number | string;
    markerUnits?: string;
    orient?: string;
    refX?: number | string;
    refY?: number | string;
    points?: string;
    transform?: string;
    opacity?: number | string;
    fillOpacity?: number | string;
    strokeOpacity?: number | string;
    pointerEvents?: string;
    cursor?: string;
    textAnchor?: string;
    dominantBaseline?: string;
    clipPath?: string;
    [key: string]: string | number | undefined | boolean | object | null;
  }

  // ── Event types ──────────────────────────────────────────────────────────────

  export interface SyntheticEvent<T = Element, E = Event> {
    bubbles: boolean;
    currentTarget: EventTarget & T;
    defaultPrevented: boolean;
    eventPhase: number;
    isTrusted: boolean;
    nativeEvent: E;
    persist(): void;
    preventDefault(): void;
    stopPropagation(): void;
    target: EventTarget & T;
    timeStamp: number;
    type: string;
  }

  export interface MouseEvent<T = Element, E = globalThis.MouseEvent> extends SyntheticEvent<T, E> {
    altKey: boolean;
    button: number;
    buttons: number;
    clientX: number;
    clientY: number;
    ctrlKey: boolean;
    metaKey: boolean;
    movementX: number;
    movementY: number;
    pageX: number;
    pageY: number;
    relatedTarget: EventTarget | null;
    screenX: number;
    screenY: number;
    shiftKey: boolean;
    preventDefault(): void;
  }

  export interface KeyboardEvent<T = Element> extends SyntheticEvent<T, globalThis.KeyboardEvent> {
    altKey: boolean;
    code: string;
    ctrlKey: boolean;
    key: string;
    keyCode: number;
    metaKey: boolean;
    repeat: boolean;
    shiftKey: boolean;
    which: number;
  }

  export interface ChangeEvent<T = Element> extends SyntheticEvent<T, globalThis.Event> {
    target: EventTarget & T;
  }

  export interface FormEvent<T = Element> extends SyntheticEvent<T, globalThis.Event> {}
  export interface FocusEvent<T = Element, R = Element> extends SyntheticEvent<T, globalThis.FocusEvent> {
    relatedTarget: EventTarget & R | null;
    target: EventTarget & T;
  }
  export interface UIEvent<T = Element, E = globalThis.UIEvent> extends SyntheticEvent<T, E> {}
  export interface WheelEvent<T = Element> extends MouseEvent<T, globalThis.WheelEvent> {}
  export interface TouchEvent<T = Element> extends SyntheticEvent<T, globalThis.TouchEvent> {
    altKey: boolean;
    changedTouches: TouchList;
    ctrlKey: boolean;
    metaKey: boolean;
    shiftKey: boolean;
    targetTouches: TouchList;
    touches: TouchList;
  }
  export interface PointerEvent<T = Element> extends MouseEvent<T, globalThis.PointerEvent> {
    pointerId: number;
    pressure: number;
    tiltX: number;
    tiltY: number;
    pointerType: string;
    isPrimary: boolean;
  }

  export type EventHandler<E extends SyntheticEvent<unknown>> = (event: E) => void;
  export type ReactEventHandler<T = Element> = EventHandler<SyntheticEvent<T>>;
  export type MouseEventHandler<T = Element> = EventHandler<MouseEvent<T>>;
  export type KeyboardEventHandler<T = Element> = EventHandler<KeyboardEvent<T>>;
  export type ChangeEventHandler<T = Element> = EventHandler<ChangeEvent<T>>;
  export type FormEventHandler<T = Element> = EventHandler<FormEvent<T>>;
  export type FocusEventHandler<T = Element> = EventHandler<FocusEvent<T>>;
  export type UIEventHandler<T = Element> = EventHandler<UIEvent<T>>;
  export type WheelEventHandler<T = Element> = EventHandler<WheelEvent<T>>;
  export type TouchEventHandler<T = Element> = EventHandler<TouchEvent<T>>;
  export type PointerEventHandler<T = Element> = EventHandler<PointerEvent<T>>;

  // ── Hooks ────────────────────────────────────────────────────────────────────

  export function useState<S>(initialState: S | (() => S)): [S, Dispatch<SetStateAction<S>>];
  export function useState<S = undefined>(): [S | undefined, Dispatch<SetStateAction<S | undefined>>];

  export function useEffect(effect: EffectCallback, deps?: DependencyList): void;
  export function useLayoutEffect(effect: EffectCallback, deps?: DependencyList): void;
  export function useInsertionEffect(effect: EffectCallback, deps?: DependencyList): void;

  export function useRef<T>(initialValue: T): MutableRefObject<T>;
  export function useRef<T>(initialValue: T | null): RefObject<T>;
  export function useRef<T = undefined>(): MutableRefObject<T | undefined>;

  export function useMemo<T>(factory: () => T, deps: DependencyList): T;
  export function useCallback<T extends (...args: never[]) => unknown>(callback: T, deps: DependencyList): T;
  export function useContext<T>(context: Context<T>): T;
  export function useReducer<S, A>(reducer: Reducer<S, A>, initialState: S): [S, Dispatch<A>];
  export function useId(): string;
  export function useImperativeHandle<T>(ref: Ref<T> | undefined, init: () => T, deps?: DependencyList): void;
  export function useDeferredValue<T>(value: T): T;
  export function useTransition(): [boolean, TransitionStartFunction];
  export function useDebugValue<T>(value: T, format?: (value: T) => unknown): void;

  export type EffectCallback = () => void | (() => void | undefined);
  export type DependencyList = ReadonlyArray<unknown>;
  export type Dispatch<A> = (value: A) => void;
  export type SetStateAction<S> = S | ((prevState: S) => S);
  export type Reducer<S, A> = (prevState: S, action: A) => S;
  export type TransitionStartFunction = (callback: () => void) => void;

  export interface Context<T> {
    Provider: Provider<T>;
    Consumer: Consumer<T>;
    displayName?: string;
  }

  export interface Provider<T> {
    (props: ProviderProps<T>): ReactElement | null;
  }

  export interface Consumer<T> {
    (props: ConsumerProps<T>): ReactElement | null;
  }

  export interface ProviderProps<T> {
    value: T;
    children?: ReactNode;
  }

  export interface ConsumerProps<T> {
    children: (value: T) => ReactNode;
  }

  export function createContext<T>(defaultValue: T): Context<T>;
  export function createContext<T>(defaultValue: T | undefined): Context<T | undefined>;

  export function memo<T extends ComponentType<unknown>>(
    Component: T,
    propsAreEqual?: (prevProps: Readonly<ComponentProps<T>>, nextProps: Readonly<ComponentProps<T>>) => boolean
  ): T;

  export function forwardRef<T, P = Record<string, unknown>>(
    render: ForwardRefRenderFunction<T, P>
  ): ForwardRefExoticComponent<PropsWithoutRef<P> & RefAttributes<T>>;

  export interface ForwardRefRenderFunction<T, P = Record<string, unknown>> {
    (props: P, ref: ForwardedRef<T>): ReactElement | null;
    displayName?: string;
  }

  export type ForwardedRef<T> = ((instance: T | null) => void) | MutableRefObject<T | null> | null;

  export interface ForwardRefExoticComponent<P> extends NamedExoticComponent<P> {
    defaultProps?: Partial<P>;
  }

  export interface NamedExoticComponent<P = Record<string, unknown>> {
    (props: P): ReactElement | null;
    displayName?: string;
  }

  export type PropsWithoutRef<P> = 'ref' extends keyof P ? Omit<P, 'ref'> : P;

  export interface RefAttributes<T> {
    ref?: Ref<T>;
  }

  export type ComponentType<P = Record<string, unknown>> = ComponentClass<P> | FunctionComponent<P>;

  export type ComponentProps<T extends ComponentType<unknown> | keyof JSX.IntrinsicElements | string> =
    T extends ComponentType<infer P>
      ? P
      : T extends keyof JSX.IntrinsicElements
        ? JSX.IntrinsicElements[T]
        : Record<string, unknown>;

  export interface ComponentClass<P = Record<string, unknown>, S = Record<string, unknown>> {
    new(props: P): Component<P, S>;
    displayName?: string;
    defaultProps?: Partial<P>;
  }

  export function createElement(
    type: string | ComponentType<unknown>,
    props?: Record<string, unknown> | null,
    ...children: ReactNode[]
  ): ReactElement;

  // React built-in components — must return ReactElement | null to be valid JSX
  export const StrictMode: (props: { children?: ReactNode }) => ReactElement | null;
  export const Fragment: (props: { children?: ReactNode; key?: Key }) => ReactElement | null;
  export const Suspense: (props: { children?: ReactNode; fallback?: ReactNode }) => ReactElement | null;

  export function lazy<T extends ComponentType<unknown>>(
    factory: () => Promise<{ default: T }>
  ): T;

  export function startTransition(scope: () => void): void;
  export function createPortal(children: ReactNode, container: Element | DocumentFragment): ReactElement;

  // ── Children ─────────────────────────────────────────────────────────────────

  export namespace Children {
    function map<T, C>(
      children: C | C[],
      fn: (child: C, index: number) => T
    ): Array<Exclude<T, boolean | null | undefined>>;
    function forEach<C>(children: C | C[], fn: (child: C, index: number) => void): void;
    function count(children: ReactNode): number;
    function only<C>(children: C): C extends unknown[] ? never : C;
    function toArray(children: ReactNode): Array<Exclude<ReactNode, boolean | null | undefined>>;
  }

  export default React;
}

declare module 'react/jsx-runtime' {
  import { ReactElement, ReactNode, Key, JSXElementConstructor } from 'react';

  export function jsx(
    type: string | JSXElementConstructor<Record<string, unknown>>,
    props: Record<string, unknown> & { children?: ReactNode },
    key?: Key | null
  ): ReactElement;

  export function jsxs(
    type: string | JSXElementConstructor<Record<string, unknown>>,
    props: Record<string, unknown> & { children?: ReactNode },
    key?: Key | null
  ): ReactElement;

  export function jsxDEV(
    type: string | JSXElementConstructor<Record<string, unknown>>,
    props: Record<string, unknown> & { children?: ReactNode },
    key?: Key | null,
    isStatic?: boolean,
    source?: object,
    self?: unknown
  ): ReactElement;

  export namespace JSX {
    type Element = ReactElement;
    interface ElementClass { render(): ReactNode; }
    interface ElementAttributesProperty { props: Record<string, unknown>; }
    interface ElementChildrenAttribute { children: unknown; }
    interface IntrinsicAttributes { key?: Key | null; }
    type IntrinsicElements = globalThis.JSX.IntrinsicElements;
  }
}

declare module 'react/jsx-dev-runtime' {
  export * from 'react/jsx-runtime';
}

declare module 'react-dom/client' {
  import { ReactNode } from 'react';

  export interface Root {
    render(children: ReactNode): void;
    unmount(): void;
  }

  export interface RootOptions {
    onUncaughtError?: (error: unknown, errorInfo: { componentStack: string }) => void;
    onCaughtError?: (error: unknown, errorInfo: { componentStack: string }) => void;
    onRecoverableError?: (error: unknown, errorInfo: { componentStack: string }) => void;
    identifierPrefix?: string;
  }

  export function createRoot(container: Element | DocumentFragment, options?: RootOptions): Root;
  export function hydrateRoot(container: Element | Document, initialChildren: ReactNode, options?: RootOptions): Root;
}
