/**
 * One runnable check: the plugin registers every skill bundle under its own
 * provider, and default roots stay out. Run from a dsh profile directory so
 * the peer packages resolve:
 *   node /path/to/dsh-moments-aieo/tests/smoke.mjs
 */
import assert from 'node:assert/strict'
import { readdirSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { Context } from '@deepseek-ai/cordis'
import SkillRegistry from '@deepseek-ai/dsh-skill'
import * as plugin from '../index.mjs'

const skillsDir = fileURLToPath(new URL('../skills', import.meta.url))
const expected = readdirSync(skillsDir, { withFileTypes: true })
  .filter(e => e.isDirectory() && e.name !== 'shared')
  .map(e => e.name)
  .sort()

const ctx = new Context()
ctx.plugin(SkillRegistry, {})
ctx.plugin(plugin, {})
await new Promise(resolve => setTimeout(resolve, 1000))

const listed = await ctx.get('skills').list()
const mine = listed.filter(s => s.provider === 'moments-aieo').map(s => s.name).sort()

assert.deepEqual(mine, expected, `registered ${mine.length} skills, expected ${expected.length}`)
assert.equal(listed.length, mine.length, 'includeDefaultRoots: false must keep user roots out')
assert.ok(!mine.includes('shared'), 'shared/ must not be discovered as a skill')

console.log(`ok — ${mine.length} skills under provider moments-aieo`)
process.exit(0)
