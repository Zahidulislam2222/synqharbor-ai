# Configuration ownership

`.env.example` lists supported frontend and backend environment settings. `backend/app/settings.py` is the typed backend boundary; `src/config/` owns public browser settings. Keep deployment-specific service limits/paths/ports/images in deployment settings, not feature modules.

| Group | Ownership and precautions |
|---|---|
| `NEXT_PUBLIC_*` | Public build-time origin/API prefix; never secrets |
| Database URLs/session secret | Private environment or secret store; separate migration/runtime environments |
| Origin/cookies/hosts/enrollment | Exact HTTPS origin, Secure host cookie, expected hosts and operator enrollment policy |
| Provider/model/digests | Local loopback only, installed complete digests, separate Builder/coding/Reviewer bindings |
| Time/token/context/queue/resource budgets | Typed settings; validate lease duration against worst-case bounded inference/test time |
| Repository paths/grants | Operator configuration plus workspace/target/profile authorization |
| Prompts/profiles/public copy | Validated maintained JSON and Markdown, not scattered control-flow literals |
| Protocol constants | Named API/Git/guest/import modules; changed only with compatible protocol review |

Change provider/model/version/timeouts through the owning settings/data. Restart relevant services after private runtime changes; rebuild for public build-time changes. Validate configuration before activation and preserve the previous version for rollback. Never include real secret values in examples, public docs, command arguments, logs or browser bundles.

Maintained by [Zahidul Islam](https://github.com/Zahidulislam2222). See the [documentation index](README.md) and [delivery roadmap](roadmap.md).
