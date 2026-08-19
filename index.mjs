/**
 * moments-aieo — mounts the AIEO skill bundle (诊断 / 定位 / 内容 / 监控) as its
 * own isolated skill provider, so the whole set travels as one loader row.
 *
 * @module moments-aieo
 */
import { fileURLToPath } from 'node:url'
import z from '@deepseek-ai/schemastery'
import * as SkillFilesystem from '@deepseek-ai/dsh-skill-filesystem'

export const name = 'moments-aieo'
export const inject = ['skills']

export const Config = z.object({
  /** Directory holding the `<name>/SKILL.md` bundles. Defaults to this repo's `skills/`. */
  skillsDir: z.string().default(fileURLToPath(new URL('skills', import.meta.url))),
  /** Provider name on ctx.skills; keeps this set separable from the user's own roots. */
  providerName: z.string().default('moments-aieo'),
})

export function apply(ctx, config) {
  ctx.plugin(SkillFilesystem, {
    providerName: config.providerName,
    includeDefaultRoots: false,
    customSkillDirs: [config.skillsDir],
  })
}
