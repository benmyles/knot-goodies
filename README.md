# Knot Resolver Goodies

A collection of useful modules and tools for [Knot Resolver](https://knot-resolver.readthedocs.io/en/stable/index.html) (v5.7.4).

### `always_serve_stale.lua`

A module that serves stale data when the TTL is expired, similar to "optimistic caching" in AdGuard Home. It sets a short TTL on the returned record and kicks off an async resolve to fetch fresh data for future use.

#### Installation
Copy it into the modules directory (e.g. `/usr/lib/x86_64-linux-gnu/knot-resolver/kres_modules/`) then add it to `kresd.conf`:

```lua
modules = {
    'stats',
    'always_serve_stale < cache',
}
```

### `knotstats.py`

A web-based dashboard for monitoring Knot Resolver statistics in real-time.

#### Requirements
Requires the Knot Resolver webmgmt feature to be enabled:

```lua
net.listen('127.0.0.1', 8453, { kind = 'webmgmt' })
modules = {
  'http',
}
http.config({})
```

#### Usage
1. Install uv: https://docs.astral.sh/uv/guides/scripts/
2. Run the dashboard: `uv run knotstats.py`
3. Open http://127.0.0.1:5001 in your browser

## License

This project is licensed under the MIT License - see the LICENSE file for details.
