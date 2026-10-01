// Amp plugin sketch: Opus 5.5 orchestrator mode + GPT 6.1 Sol builder tool.
// Place in .amp/plugins/. Replace the model IDs with the ones Amp's picker shows.
// Custom agents are a recent Amp feature; check the plugin docs if the API has changed.
import type { PluginAPI } from '@ampcode/plugin'

export default function (amp: PluginAPI) {
  const builder = amp.createAgent({
    name: 'builder',
    model: '<gpt-6.1-sol-id>',
    instructions: 'Implement exactly the brief you are given. ' +
      'Run the stated test command and report results, files changed, and any blockers.',
    tools: 'all',
  })

  amp.registerTool({
    name: 'build',
    description: 'Use for ALL code implementation. Pass a complete brief: ' +
      'goal, files, constraints, and the test command that proves it is done.',
    inputSchema: { type: 'object',
      properties: { brief: { type: 'string' } }, required: ['brief'] },
    async execute(input, ctx) {
      const r = await builder.run(input.brief, { parentThreadID: ctx.thread.id })
      return r.text
    },
  })

  const orchestrator = amp.createAgent({
    name: 'orchestrator',
    model: '<opus-5.5-id>',
    instructions: 'You plan and review; you do not write code. ' +
      'Break work into tasks, send each to the build tool, ' +
      'then verify by running tests. Only make trivial one-line fixes yourself.',
    tools: 'all',
  })

  amp.registerAgentMode({
    key: 'opus-orchestrator',
    description: 'Opus plans, GPT builds',
    agent: orchestrator.definition,
  })
}
