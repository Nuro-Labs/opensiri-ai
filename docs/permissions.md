# Permissions

Every source is opt-in. Default is deny.

The permission center should render `eliot_harness.sources.MANIFESTS` and allow:

- Off
- Ask every time
- Read only
- Read + write
- Session only
- Persistent

Risky actions still require confirmation even when write permission is enabled:

- destructive local actions
- external communication
- network/web
- payments/purchases
- credentials/passwords
- system administration
