// Global JSX namespace declaration for react-jsx transform compatibility.
// When @types/react is not installed, this provides the global JSX.IntrinsicElements
// interface that TypeScript requires for type-safe JSX.

declare namespace JSX {
  // React 19 allows components to return undefined (in addition to null).
  // Setting Element to ReactElement | undefined allows components like
  // AnimatePresence (from framer-motion) that return `Element | undefined`.
  type Element = import('react').ReactElement | undefined | null;

  interface ElementClass {
    render(): import('react').ReactNode;
  }

  interface ElementAttributesProperty {
    props: Record<string, unknown>;
  }

  interface ElementChildrenAttribute {
    children: unknown;
  }

  interface IntrinsicAttributes {
    key?: string | number | bigint | null | undefined;
    children?: import('react').ReactNode;
  }

  interface IntrinsicClassAttributes<T> {
    ref?: ((instance: T | null) => void) | { current: T | null } | null;
  }

  interface IntrinsicElements {
    // ── HTML block elements ──────────────────────────────────────────────────
    div: React.HTMLAttributes<HTMLDivElement>;
    span: React.HTMLAttributes<HTMLSpanElement>;
    p: React.HTMLAttributes<HTMLParagraphElement>;
    h1: React.HTMLAttributes<HTMLHeadingElement>;
    h2: React.HTMLAttributes<HTMLHeadingElement>;
    h3: React.HTMLAttributes<HTMLHeadingElement>;
    h4: React.HTMLAttributes<HTMLHeadingElement>;
    h5: React.HTMLAttributes<HTMLHeadingElement>;
    h6: React.HTMLAttributes<HTMLHeadingElement>;
    section: React.HTMLAttributes<HTMLElement>;
    article: React.HTMLAttributes<HTMLElement>;
    aside: React.HTMLAttributes<HTMLElement>;
    header: React.HTMLAttributes<HTMLElement>;
    footer: React.HTMLAttributes<HTMLElement>;
    main: React.HTMLAttributes<HTMLElement>;
    nav: React.HTMLAttributes<HTMLElement>;
    ul: React.HTMLAttributes<HTMLUListElement>;
    ol: React.HTMLAttributes<HTMLOListElement>;
    li: React.HTMLAttributes<HTMLLIElement>;
    dl: React.HTMLAttributes<HTMLDListElement>;
    dt: React.HTMLAttributes<HTMLElement>;
    dd: React.HTMLAttributes<HTMLElement>;
    pre: React.HTMLAttributes<HTMLPreElement>;
    code: React.HTMLAttributes<HTMLElement>;
    em: React.HTMLAttributes<HTMLElement>;
    strong: React.HTMLAttributes<HTMLElement>;
    small: React.HTMLAttributes<HTMLElement>;
    b: React.HTMLAttributes<HTMLElement>;
    i: React.HTMLAttributes<HTMLElement>;
    u: React.HTMLAttributes<HTMLElement>;
    blockquote: React.HTMLAttributes<HTMLElement>;
    hr: React.HTMLAttributes<HTMLHRElement>;
    br: React.HTMLAttributes<HTMLBRElement>;

    // ── HTML inline / interactive elements ──────────────────────────────────
    a: React.HTMLAttributes<HTMLAnchorElement> & {
      href?: string;
      target?: string;
      rel?: string;
      download?: string | boolean;
    };
    button: React.HTMLAttributes<HTMLButtonElement> & {
      disabled?: boolean;
      type?: 'button' | 'submit' | 'reset';
      form?: string;
    };
    input: React.HTMLAttributes<HTMLInputElement> & {
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
      onChange?: React.ChangeEventHandler<HTMLInputElement>;
    };
    textarea: React.HTMLAttributes<HTMLTextAreaElement> & {
      value?: string;
      defaultValue?: string;
      disabled?: boolean;
      placeholder?: string;
      rows?: number;
      cols?: number;
      readOnly?: boolean;
      required?: boolean;
      onChange?: React.ChangeEventHandler<HTMLTextAreaElement>;
    };
    select: React.HTMLAttributes<HTMLSelectElement> & {
      value?: string | string[] | number;
      defaultValue?: string | string[] | number;
      disabled?: boolean;
      multiple?: boolean;
      required?: boolean;
      onChange?: React.ChangeEventHandler<HTMLSelectElement>;
    };
    option: React.HTMLAttributes<HTMLOptionElement> & {
      value?: string | number | readonly string[];
      disabled?: boolean;
      selected?: boolean;
    };
    label: React.HTMLAttributes<HTMLLabelElement> & {
      htmlFor?: string;
    };
    form: React.HTMLAttributes<HTMLFormElement> & {
      action?: string;
      method?: string;
      onSubmit?: React.FormEventHandler<HTMLFormElement>;
    };

    // ── Media elements ───────────────────────────────────────────────────────
    img: React.HTMLAttributes<HTMLImageElement> & {
      src?: string;
      alt?: string;
      width?: number | string;
      height?: number | string;
      loading?: 'lazy' | 'eager';
      decoding?: 'sync' | 'async' | 'auto';
    };
    video: React.HTMLAttributes<HTMLVideoElement> & {
      src?: string;
      autoPlay?: boolean;
      controls?: boolean;
      loop?: boolean;
      muted?: boolean;
      width?: number | string;
      height?: number | string;
    };
    audio: React.HTMLAttributes<HTMLAudioElement> & {
      src?: string;
      autoPlay?: boolean;
      controls?: boolean;
      loop?: boolean;
      muted?: boolean;
    };
    canvas: React.HTMLAttributes<HTMLCanvasElement> & {
      width?: number | string;
      height?: number | string;
    };

    // ── Table elements ───────────────────────────────────────────────────────
    table: React.HTMLAttributes<HTMLTableElement>;
    thead: React.HTMLAttributes<HTMLTableSectionElement>;
    tbody: React.HTMLAttributes<HTMLTableSectionElement>;
    tfoot: React.HTMLAttributes<HTMLTableSectionElement>;
    tr: React.HTMLAttributes<HTMLTableRowElement>;
    th: React.HTMLAttributes<HTMLTableHeaderCellElement> & {
      colSpan?: number;
      rowSpan?: number;
      scope?: string;
    };
    td: React.HTMLAttributes<HTMLTableDataCellElement> & {
      colSpan?: number;
      rowSpan?: number;
    };

    // ── Time element ─────────────────────────────────────────────────────────
    time: React.HTMLAttributes<HTMLTimeElement> & { dateTime?: string };

    // ── Metadata / document elements ─────────────────────────────────────────
    style: React.HTMLAttributes<HTMLStyleElement> & { children?: string };
    script: React.HTMLAttributes<HTMLScriptElement> & {
      src?: string;
      async?: boolean;
      defer?: boolean;
      type?: string;
    };
    link: React.HTMLAttributes<HTMLLinkElement> & {
      rel?: string;
      href?: string;
      type?: string;
    };
    meta: React.HTMLAttributes<HTMLMetaElement> & {
      name?: string;
      content?: string;
      charSet?: string;
    };
    title: React.HTMLAttributes<HTMLTitleElement>;
    head: React.HTMLAttributes<HTMLHeadElement>;
    body: React.HTMLAttributes<HTMLBodyElement>;
    html: React.HTMLAttributes<HTMLHtmlElement>;

    // ── SVG elements ─────────────────────────────────────────────────────────
    svg: React.SVGAttributes<SVGSVGElement> & {
      xmlns?: string;
      viewBox?: string;
      width?: number | string;
      height?: number | string;
      fill?: string;
      stroke?: string;
    };
    path: React.SVGAttributes<SVGPathElement>;
    circle: React.SVGAttributes<SVGCircleElement>;
    rect: React.SVGAttributes<SVGRectElement>;
    line: React.SVGAttributes<SVGLineElement>;
    polyline: React.SVGAttributes<SVGPolylineElement>;
    polygon: React.SVGAttributes<SVGPolygonElement>;
    ellipse: React.SVGAttributes<SVGEllipseElement>;
    g: React.SVGAttributes<SVGGElement>;
    text: React.SVGAttributes<SVGTextElement> & { children?: React.ReactNode };
    tspan: React.SVGAttributes<SVGTSpanElement>;
    defs: React.SVGAttributes<SVGDefsElement>;
    marker: React.SVGAttributes<SVGMarkerElement> & {
      id?: string;
      markerWidth?: number | string;
      markerHeight?: number | string;
      refX?: number | string;
      refY?: number | string;
      orient?: string;
      markerUnits?: string;
    };
    linearGradient: React.SVGAttributes<SVGLinearGradientElement> & { id?: string };
    radialGradient: React.SVGAttributes<SVGRadialGradientElement> & { id?: string };
    stop: React.SVGAttributes<SVGStopElement> & {
      offset?: string | number;
      stopColor?: string;
      stopOpacity?: number | string;
    };
    clipPath: React.SVGAttributes<SVGClipPathElement> & { id?: string };
    mask: React.SVGAttributes<SVGMaskElement> & { id?: string };
    use: React.SVGAttributes<SVGUseElement> & { href?: string; xlinkHref?: string };
    symbol: React.SVGAttributes<SVGSymbolElement> & { id?: string; viewBox?: string };
    filter: React.SVGAttributes<SVGFilterElement> & { id?: string };
    feGaussianBlur: React.SVGAttributes<SVGFEGaussianBlurElement>;
    feColorMatrix: React.SVGAttributes<SVGFEColorMatrixElement>;
    animate: React.SVGAttributes<SVGAnimateElement>;
    animateTransform: React.SVGAttributes<SVGAnimateTransformElement>;
    foreignObject: React.SVGAttributes<SVGForeignObjectElement>;
  }
}
