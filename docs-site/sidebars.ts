import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

const sidebars: SidebarsConfig = {
  docs: [
    {
      type: 'category',
      label: 'Getting Started',
      items: [
        'getting-started/01-sign-up',
        'getting-started/02-connect-integrations',
        'getting-started/03-scope-selection',
        'getting-started/04-your-first-briefing',
      ],
    },
    {
      type: 'category',
      label: 'Concepts',
      items: [
        'concepts/briefing',
        'concepts/initiative',
        'concepts/dependency',
        'concepts/decision',
        'concepts/activation-moment',
      ],
    },
    {
      type: 'category',
      label: 'Workflow Reference',
      items: [
        'workflow-reference/executive-briefing',
        'workflow-reference/dependency-scan',
        'workflow-reference/onboarding-flow',
      ],
    },
  ],
};

export default sidebars;
