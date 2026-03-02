import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { api, MT5ConnectionStatus, MT5SymbolsResponse } from '@/services/api';
import { RefreshCw, Activity, Link2Off } from 'lucide-react';
import { useCallback, useEffect, useMemo, useState } from 'react';

export function MT5BridgeSettings() {
  const [connection, setConnection] = useState<MT5ConnectionStatus | null>(null);
  const [symbols, setSymbols] = useState<MT5SymbolsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async (isManual = false) => {
    if (isManual) setRefreshing(true);
    try {
      const [conn, symbolData] = await Promise.all([
        api.getMT5Connection(),
        api.getMT5Symbols({ enabledOnly: true }),
      ]);
      setConnection(conn);
      setSymbols(symbolData);
      setError(null);
    } catch (err) {
      console.error('Failed loading MT5 bridge settings:', err);
      setError('Could not load bridge data from backend');
    } finally {
      setLoading(false);
      if (isManual) setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    refresh();
    // Refresh at source cadence target: 1s.
    const id = setInterval(() => {
      refresh();
    }, 1000);
    return () => clearInterval(id);
  }, [refresh]);

  const statusLabel = useMemo(() => {
    if (!connection) return 'Unknown';
    if (connection.status) return connection.status;
    if (connection.connected && connection.authorized) return 'Connected';
    if (connection.connected && !connection.authorized) return 'Connected (Unauthorized)';
    return 'Disconnected';
  }, [connection]);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-primary">MT5 Bridge</h3>
        <Button
          variant="outline"
          size="sm"
          onClick={() => refresh(true)}
          disabled={refreshing}
          className="gap-2"
        >
          <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      <div className="rounded-lg border border-border bg-muted p-4 space-y-2">
        <div className="flex items-center gap-2">
          {connection?.connected ? (
            <Activity className="h-4 w-4 text-green-500" />
          ) : (
            <Link2Off className="h-4 w-4 text-red-500" />
          )}
          <span className="font-medium">Status:</span>
          <Badge className="text-xs bg-muted text-muted-foreground border-border">{statusLabel}</Badge>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-sm">
          <div>
            <span className="text-muted-foreground">Broker:</span> {connection?.broker ?? '—'}
          </div>
          <div>
            <span className="text-muted-foreground">Latency:</span> {connection?.latency_ms ?? '—'} ms
          </div>
          <div>
            <span className="text-muted-foreground">Account ID:</span> {connection?.account_id ?? '—'}
          </div>
          <div>
            <span className="text-muted-foreground">Balance:</span> {connection?.balance ?? '—'}
          </div>
          <div className="sm:col-span-2">
            <span className="text-muted-foreground">Last Updated:</span> {connection?.last_checked_at ?? '—'}
          </div>
        </div>

        {(connection?.error || error) && (
          <p className="text-sm text-yellow-500">{connection?.error || error}</p>
        )}
      </div>

      <div className="rounded-lg border border-border bg-muted p-4">
        <div className="flex items-center justify-between mb-3">
          <h4 className="font-medium text-primary">Configured Symbols</h4>
          <span className="text-xs text-muted-foreground">{symbols?.count ?? 0} symbols</span>
        </div>

        {loading ? (
          <p className="text-sm text-muted-foreground">Loading symbols...</p>
        ) : symbols?.symbols?.length ? (
          <div className="space-y-2 max-h-72 overflow-auto">
            {symbols.symbols.map((s) => (
              <div key={s.ticker} className="flex items-center justify-between rounded border border-border px-3 py-2 bg-panel">
                <div className="min-w-0">
                  <p className="text-sm font-medium text-primary">{s.ticker}</p>
                  <p className="text-xs text-muted-foreground truncate">{s.mt5_symbol}</p>
                </div>
                <div className="flex items-center gap-2">
                  <Badge className="text-xs bg-muted text-muted-foreground border-border">{s.category}</Badge>
                  <Badge className="text-xs bg-muted text-muted-foreground border-border">{s.runtime_status ?? 'unknown'}</Badge>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">{symbols?.error || 'No symbols available'}</p>
        )}
      </div>
    </div>
  );
}
