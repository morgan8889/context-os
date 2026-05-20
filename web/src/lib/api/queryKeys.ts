export const graphKeys = {
  all: ['graph'] as const,
  nodes: (params?: { nodeType?: string; cursor?: string }) =>
    [...graphKeys.all, 'nodes', params] as const,
  edges: (params?: { edgeType?: string; cursor?: string }) =>
    [...graphKeys.all, 'edges', params] as const,
  snapshots: () => [...graphKeys.all, 'snapshots'] as const,
  snapshot: (timestamp: string) => [...graphKeys.all, 'snapshot', timestamp] as const,
};

export const workflowKeys = {
  all: ['workflows'] as const,
  list: (params?: { teamId?: string; initiativeId?: string }) =>
    [...workflowKeys.all, 'list', params] as const,
};

export const decisionKeys = {
  all: ['decisions'] as const,
  list: (params?: {
    q?: string;
    fromDate?: string;
    toDate?: string;
    authorId?: string;
    impactedSystem?: string;
  }) => [...decisionKeys.all, 'list', params] as const,
};

export const inboxKeys = {
  all: ['inbox'] as const,
  list: (params?: { status?: string; cursor?: string }) =>
    [...inboxKeys.all, 'list', params] as const,
};

export const viewStateKeys = {
  all: ['viewState'] as const,
  current: () => [...viewStateKeys.all, 'current'] as const,
};
