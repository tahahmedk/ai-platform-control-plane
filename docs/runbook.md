# Local operations and failure diagnosis

1. Start with the bundled synthetic configuration and run the demo.
2. Correlate the X-Request-ID response header with JSON http_request/inference events.
3. For 403, inspect tenant region/capability policy. For 429, inspect remaining
   capacity and request rate. A restart resets state; it is not a production reset policy.
4. For 503, inspect eligibility, provider_failures and circuit cooldowns. Never loosen
   regional policy simply to find an available provider.
5. For an adapter bug, reproduce through an injected adapter in the HTTP tests.
6. After configuration changes, restart and run policy/failure tests before serving traffic.

Do not log raw prompts, responses or vendor error bodies. The API does not authenticate
tenants. Keep it on loopback or an isolated demonstration cluster. The simple guardrails
can have false positives and false negatives; they do not replace authorization,
data classification, vendor policy controls or dedicated safety evaluation.
