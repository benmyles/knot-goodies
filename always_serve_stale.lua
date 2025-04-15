-- MIT License
--
-- always_serve_stale.lua is a knot resolver module that serves stale data when the TTL is expired,
-- similar to "optimistic caching" in AdGuard Home. It sets a short 10s TTL on the returned record
-- and kicks off an async resolve to fetch fresh data for future use.
--
-- Copy it into the modules dir (e.g. /usr/lib/x86_64-linux-gnu/knot-resolver/kres_modules/) then
-- add it to kresd.conf in the modules section:
--
-- modules = {
--         'stats',
--         'always_serve_stale < cache',
-- }

local M = {
    -- served = 0,
    -- skipped = 0,
}

local ffi = require('ffi')

log_notice(ffi.C.LOG_GRP_SRVSTALE, '   => loading always_serve_stale module')

M.callback = ffi.cast("kr_stale_cb",
    function(ttl, name, type, qry)
        local n = kres.dname2str(qry.sname)

        if ttl + 3600 * 24 * 3 > 0 then -- at most 3 days stale
            log_notice(ffi.C.LOG_GRP_SRVSTALE, '   => served stale data for ' .. n .. ' with TTL: ' .. tostring(ttl))

            -- M.served = M.served + 1
            -- if stats then
            --     stats['astale.served'] = M.served
            -- end

            resolve(n, qry.stype, qry.sclass, { 'NO_CACHE' }) -- fetch fresh data for future use

            return 10                                         -- short ttl for stale data
        else
            log_notice(ffi.C.LOG_GRP_SRVSTALE,
                '   => skipped serving stale data for ' .. n .. ' with old TTL: ' .. tostring(ttl))

            M.skipped = M.skipped + 1
            -- if stats then
            --     stats['astale.skipped'] = M.skipped
            -- end

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
