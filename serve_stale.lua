-- MIT License
--
-- serve_stale.lua is an alternative version of the knot resolver serve_stale module that always serves stale data when the TTL is expired, similar to "optimistic caching" in AdGuard Home.
--
-- It sets a short TTL on the response and kicks off an async resolve to fetch fresh data
-- for future use.
--
-- Install via:
--   $ mv /usr/lib/knot-resolver/kres_modules/serve_stale.lua \
--       /usr/lib/knot-resolver/kres_modules/serve_stale.lua.orig && \
--     cp serve_stale.lua /usr/lib/knot-resolver/kres_modules/serve_stale.lua
--
-- And make sure you load the serve_stale module in kresd.conf.

local M = {
}

local ffi = require('ffi')

log_debug(ffi.C.LOG_GRP_SRVSTALE, '   => loading [optimistic] serve_stale module')

M.callback = ffi.cast("kr_stale_cb",
    function(ttl, name, type, qry)
        local n = kres.dname2str(qry.sname)

        if ttl + 3600 * 24 > 0 then -- at most 1 day stale
            log_notice(ffi.C.LOG_GRP_SRVSTALE, '   => served stale data for ' .. n .. ' with TTL: ' .. tostring(ttl))

            resolve(n, qry.stype, qry.sclass, { 'NO_CACHE' }) -- fetch fresh data for future use

            return 1
        else
            log_notice(ffi.C.LOG_GRP_SRVSTALE,
                '   => skipped serving stale data for ' .. n .. ' with old TTL: ' .. tostring(ttl))

            return -1
        end
    end)

M.layer = {
    produce = function(state, req)
        local qry = req:current()
        -- Don't do anything for priming, prefetching, etc.
        if qry.flags.NO_CACHE then return state end

        qry.stale_cb = M.callback

        return state
    end,

    answer_finalize = function(state, req)
        local qry = req:resolved()
        if state ~= kres.DONE or qry == nil then
            return state
        end

        if req.stale_accounted and qry.stale_cb ~= nil then
            if req.answer:rcode() == kres.rcode.NOERROR then
                req:set_extended_error(kres.extended_error.STALE, 'WFAC')
            elseif req.answer:rcode() == kres.rcode.NXDOMAIN then
                req:set_extended_error(kres.extended_error.STALE_NXD, 'QSF6')
            end
        end

        return state
    end,
}

return M
