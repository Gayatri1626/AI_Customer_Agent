"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  Users,
  Activity,
  Wrench,
  MessageSquare,
  CheckCircle2,
  XCircle,
  ChevronDown,
  ChevronRight,
  RefreshCw,
  Bot,
  Shield,
  Package,
  Calendar,
  Tag,
  AlertCircle,
  Wifi,
  WifiOff,
  ShoppingBag,
} from "lucide-react";

interface Customer {
  id: string;
  name: string;
  email: string;
  tier: string;
  member_since: string;
  orders: Order[];
}

interface Order {
  order_id: string;
  product: string;
  category: string;
  amount: number;
  purchase_date: string;
  status: string;
  condition: string;
  reason_for_return: string;
}

interface LogEntry {
  type: string;
  content?: string;
  tool?: string;
  input?: Record<string, unknown>;
  output?: Record<string, unknown>;
  session_id?: string;
  timestamp?: number;
}

interface Session {
  session_id: string;
  log_count: number;
}

// ── Tier config ───────────────────────────────────────────────────────────────
const TIER_CONFIG: Record<string, { badge: string; avatar: string; dot: string }> = {
  Gold: {
    badge: "bg-amber-50 text-amber-700 border border-amber-200 ring-1 ring-amber-100",
    avatar: "bg-gradient-to-br from-amber-400 to-orange-500",
    dot: "bg-amber-400",
  },
  Silver: {
    badge: "bg-slate-100 text-slate-600 border border-slate-200 ring-1 ring-slate-100",
    avatar: "bg-gradient-to-br from-slate-400 to-slate-600",
    dot: "bg-slate-400",
  },
  Bronze: {
    badge: "bg-orange-50 text-orange-700 border border-orange-200 ring-1 ring-orange-100",
    avatar: "bg-gradient-to-br from-orange-400 to-red-500",
    dot: "bg-orange-400",
  },
};

function TierBadge({ tier }: { tier: string }) {
  const cfg = TIER_CONFIG[tier] ?? {
    badge: "bg-gray-100 text-gray-600 border border-gray-200",
  };
  return (
    <span className={`inline-flex items-center gap-1 text-xs px-2.5 py-0.5 rounded-full font-medium ${cfg.badge}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${cfg.dot ?? "bg-gray-400"}`} />
      {tier}
    </span>
  );
}

// ── Customer card ─────────────────────────────────────────────────────────────
function CustomerCard({ customer }: { customer: Customer }) {
  const [open, setOpen] = useState(false);
  const order = customer.orders[0];
  const cfg = TIER_CONFIG[customer.tier] ?? TIER_CONFIG.Silver;
  const initials = customer.name.split(" ").map((n) => n[0]).join("").slice(0, 2);

  return (
    <div
      className={`bg-white rounded-2xl border transition-all duration-200 overflow-hidden
        ${open
          ? "border-indigo-200 shadow-md shadow-indigo-50"
          : "border-slate-200 shadow-sm hover:shadow-md hover:border-slate-300"
        }`}
    >
      {/* Card header */}
      <button
        className="w-full flex items-center gap-3 px-4 py-3.5 text-left group"
        onClick={() => setOpen((s) => !s)}
      >
        {/* Avatar */}
        <div className={`w-9 h-9 rounded-full ${cfg.avatar} flex items-center justify-center text-white text-xs font-bold shadow-sm flex-shrink-0`}>
          {initials}
        </div>

        {/* Name / email */}
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-slate-800 truncate">{customer.name}</p>
          <p className="text-xs text-slate-400 truncate">{customer.email}</p>
        </div>

        {/* Tier + chevron */}
        <div className="flex items-center gap-2 flex-shrink-0">
          <TierBadge tier={customer.tier} />
          <ChevronDown
            className={`w-4 h-4 text-slate-400 transition-transform duration-200 ${open ? "rotate-180" : ""}`}
          />
        </div>
      </button>

      {/* Expanded order details */}
      {open && order && (
        <div className="border-t border-slate-100 bg-gradient-to-b from-slate-50 to-white px-4 py-3 space-y-2">
          <div className="flex items-center gap-1.5 mb-2">
            <Package className="w-3.5 h-3.5 text-indigo-400" />
            <span className="text-xs font-semibold text-slate-600 uppercase tracking-wide">Order Details</span>
          </div>

          <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-xs">
            <OrderRow label="Order ID" value={order.order_id} mono />
            <OrderRow label="Status" value={order.status} />
            <OrderRow label="Product" value={order.product} span />
            <OrderRow label="Amount" value={`$${order.amount.toFixed(2)}`} bold />
            <OrderRow label="Purchased" value={order.purchase_date} />
            <OrderRow
              label="Condition"
              value={order.condition}
              color={
                order.condition === "Defective" ? "text-red-600" :
                order.condition === "Unopened" ? "text-emerald-600" :
                "text-slate-700"
              }
            />
            <OrderRow label="Category" value={order.category} />
            <OrderRow label="Reason" value={order.reason_for_return} span italic />
          </div>

          <div className="pt-1 flex items-center gap-1 text-[10px] text-slate-400">
            <Calendar className="w-3 h-3" />
            Member since {customer.member_since}
          </div>
        </div>
      )}

      {/* No orders */}
      {open && !order && (
        <div className="border-t border-slate-100 px-4 py-3 text-xs text-slate-400 text-center">
          No orders on file
        </div>
      )}
    </div>
  );
}

function OrderRow({
  label,
  value,
  mono = false,
  bold = false,
  span = false,
  italic = false,
  color,
}: {
  label: string;
  value: string;
  mono?: boolean;
  bold?: boolean;
  span?: boolean;
  italic?: boolean;
  color?: string;
}) {
  return (
    <div className={span ? "col-span-2" : ""}>
      <p className="text-slate-400 text-[10px] uppercase tracking-wide mb-0.5">{label}</p>
      <p
        className={`text-slate-700 truncate ${mono ? "font-mono" : ""} ${bold ? "font-semibold text-slate-900" : ""} ${italic ? "italic" : ""} ${color ?? ""}`}
      >
        {value}
      </p>
    </div>
  );
}

// ── Log entry ─────────────────────────────────────────────────────────────────
function LogRow({ entry }: { entry: LogEntry }) {
  const [expanded, setExpanded] = useState(false);

  const TYPE_STYLES: Record<string, { bg: string; border: string; icon: React.ReactNode; label: string }> = {
    user_message: {
      bg: "bg-sky-50", border: "border-sky-100",
      icon: <MessageSquare className="w-3.5 h-3.5 text-sky-500" />,
      label: "User",
    },
    assistant_message: {
      bg: "bg-violet-50", border: "border-violet-100",
      icon: <Bot className="w-3.5 h-3.5 text-violet-500" />,
      label: "Agent",
    },
    tool_call: {
      bg: "bg-amber-50", border: "border-amber-100",
      icon: <Wrench className="w-3.5 h-3.5 text-amber-500" />,
      label: "Tool call",
    },
    tool_result: {
      bg: "bg-emerald-50", border: "border-emerald-100",
      icon: <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />,
      label: "Tool result",
    },
    agent_thinking: {
      bg: "bg-indigo-50", border: "border-indigo-100",
      icon: <Bot className="w-3.5 h-3.5 text-indigo-400" />,
      label: "Thinking",
    },
    reasoning: {
      bg: "bg-slate-50", border: "border-slate-100",
      icon: <Activity className="w-3.5 h-3.5 text-slate-400" />,
      label: "Reasoning",
    },
  };

  const style = TYPE_STYLES[entry.type] ?? TYPE_STYLES.reasoning;
  const hasDetail = entry.type === "tool_call" || entry.type === "tool_result";

  const preview =
    entry.type === "tool_call" ? `${entry.tool}()` :
    entry.type === "tool_result" ? `${entry.tool} → result` :
    (entry.content?.slice(0, 100) ?? "") + (entry.content && entry.content.length > 100 ? "…" : "");

  return (
    <div className={`rounded-xl border ${style.bg} ${style.border} p-3 mb-2 text-xs transition-all`}>
      <div
        className={`flex items-start gap-2 ${hasDetail ? "cursor-pointer" : ""}`}
        onClick={() => hasDetail && setExpanded((s) => !s)}
      >
        <span className="mt-0.5 flex-shrink-0 p-1 rounded-md bg-white shadow-sm">{style.icon}</span>
        <div className="flex-1 min-w-0">
          <span className="text-[10px] font-semibold uppercase tracking-wide text-slate-400 mr-1.5">{style.label}</span>
          <span className="text-slate-600 leading-relaxed break-words">{preview}</span>
        </div>
        {hasDetail && (
          <ChevronDown className={`w-3.5 h-3.5 text-slate-400 flex-shrink-0 mt-0.5 transition-transform ${expanded ? "rotate-180" : ""}`} />
        )}
      </div>

      {expanded && hasDetail && (
        <pre className="mt-2.5 p-3 bg-white rounded-lg border border-slate-200 text-[10px] overflow-x-auto text-slate-600 max-h-48 leading-relaxed">
          {JSON.stringify(entry.type === "tool_call" ? entry.input : entry.output, null, 2)}
        </pre>
      )}

      {entry.session_id && (
        <p className="mt-1.5 font-mono text-[9px] text-slate-300">
          {entry.session_id.slice(0, 8)}…
        </p>
      )}
    </div>
  );
}

// ── Stat card ─────────────────────────────────────────────────────────────────
function StatCard({
  icon,
  value,
  label,
  color,
}: {
  icon: React.ReactNode;
  value: number;
  label: string;
  color: string;
}) {
  return (
    <div className={`flex items-center gap-3 px-4 py-2.5 rounded-xl border ${color} bg-white`}>
      <div className="flex-shrink-0">{icon}</div>
      <div>
        <p className="text-lg font-bold text-slate-800 leading-none">{value}</p>
        <p className="text-[11px] text-slate-500 mt-0.5">{label}</p>
      </div>
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────
export default function AdminPage() {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeTab, setActiveTab] = useState<"customers" | "logs" | "policy">("customers");
  const [policy, setPolicy] = useState("");
  const [wsStatus, setWsStatus] = useState<"connecting" | "connected" | "disconnected">("disconnected");
  const [filterType, setFilterType] = useState("all");
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const logsEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  useEffect(() => {
    fetch("http://localhost:8000/api/customers").then((r) => r.json()).then(setCustomers).catch(console.error);
    fetch("http://localhost:8000/api/refund-policy").then((r) => r.json()).then((d) => setPolicy(d.policy)).catch(console.error);
    fetch("http://localhost:8000/api/sessions").then((r) => r.json()).then(setSessions).catch(console.error);
  }, []);

  const connectWs = useCallback(() => {
    const existing = wsRef.current;
    if (existing && (existing.readyState === WebSocket.OPEN || existing.readyState === WebSocket.CONNECTING)) return;
    existing?.close();
    setWsStatus("connecting");
    const ws = new WebSocket("ws://localhost:8000/ws/admin");
    wsRef.current = ws;

    ws.onopen = () => setWsStatus("connected");

    ws.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        if (data.type === "ping") return;
        setLogs((prev) => [...prev.slice(-500), data]);
      } catch { /* ignore */ }
    };

    // Auto-reconnect after 3 seconds on any drop
    ws.onclose = () => {
      setWsStatus("disconnected");
      reconnectTimerRef.current = setTimeout(() => {
        if (wsRef.current?.readyState !== WebSocket.OPEN) connectWs();
      }, 3000);
    };

    ws.onerror = () => {
      setWsStatus("disconnected");
    };
  }, []);

  useEffect(() => {
    const t = setTimeout(connectWs, 100);
    return () => {
      clearTimeout(t);
      if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
      wsRef.current?.close();
      wsRef.current = null;
    };
  }, [connectWs]);

  const filteredLogs = filterType === "all" ? logs : logs.filter((l) => l.type === filterType);

  const stats = {
    approved: logs.filter((l) => l.type === "tool_result" && (l.output as { decision?: string })?.decision === "APPROVED").length,
    denied: logs.filter((l) => l.type === "tool_result" && (l.output as { decision?: string })?.decision === "DENIED").length,
    toolCalls: logs.filter((l) => l.type === "tool_call").length,
    sessions: sessions.length,
  };

  const TABS = [
    { id: "customers" as const, label: "Customers", icon: <Users className="w-4 h-4" /> },
    { id: "logs" as const, label: "Live Logs", icon: <Activity className="w-4 h-4" /> },
    { id: "policy" as const, label: "Policy", icon: <Shield className="w-4 h-4" /> },
  ];

  return (
    <div className="flex flex-col h-screen bg-[#F5F7FA]" style={{ fontFamily: "var(--font-inter, Inter, system-ui, sans-serif)" }}>

      {/* ── Header ── */}
      <header className="bg-white border-b border-slate-200 px-6 py-0 flex items-center justify-between shadow-sm">
        <div className="flex items-center gap-0 h-14">
          {/* Back */}
          <Link
            href="/"
            className="flex items-center gap-2 text-slate-500 hover:text-indigo-600 transition-colors pr-5 border-r border-slate-100 h-full group"
          >
            <ArrowLeft className="w-4 h-4 transition-transform group-hover:-translate-x-0.5" />
            <span className="text-sm font-medium hidden sm:block">Chat</span>
          </Link>

          {/* Brand */}
          <div className="flex items-center gap-3 pl-5">
            <div className="w-7 h-7 bg-gradient-to-br from-indigo-500 to-violet-600 rounded-lg flex items-center justify-center shadow-sm">
              <ShoppingBag className="w-4 h-4 text-white" />
            </div>
            <div>
              <h1 className="font-semibold text-slate-900 text-sm leading-tight">Admin Dashboard</h1>
              <p className="text-[11px] text-slate-400 leading-tight">ShopEase · Real-time monitoring</p>
            </div>
          </div>
        </div>

        {/* WS status */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-50 border border-slate-200">
            {wsStatus === "connected" ? (
              <Wifi className="w-3.5 h-3.5 text-emerald-500" />
            ) : wsStatus === "connecting" ? (
              <Wifi className="w-3.5 h-3.5 text-amber-500" />
            ) : (
              <WifiOff className="w-3.5 h-3.5 text-slate-400" />
            )}
            <span className={`text-xs font-medium capitalize ${
              wsStatus === "connected" ? "text-emerald-600" :
              wsStatus === "connecting" ? "text-amber-600" : "text-slate-500"
            }`}>
              {wsStatus}
            </span>
          </div>
          <button
            onClick={connectWs}
            className="w-8 h-8 flex items-center justify-center rounded-lg text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 transition-colors border border-slate-200"
            title="Reconnect WebSocket"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>
      </header>

      {/* ── Stats row ── */}
      <div className="bg-white border-b border-slate-200 px-6 py-3 flex items-center gap-3 overflow-x-auto">
        <StatCard
          icon={<CheckCircle2 className="w-4 h-4 text-emerald-500" />}
          value={stats.approved}
          label="Approved"
          color="border-emerald-100"
        />
        <StatCard
          icon={<XCircle className="w-4 h-4 text-red-400" />}
          value={stats.denied}
          label="Denied"
          color="border-red-100"
        />
        <StatCard
          icon={<Wrench className="w-4 h-4 text-amber-500" />}
          value={stats.toolCalls}
          label="Tool calls"
          color="border-amber-100"
        />
        <StatCard
          icon={<Activity className="w-4 h-4 text-indigo-500" />}
          value={stats.sessions}
          label="Sessions"
          color="border-indigo-100"
        />
        {/* Live indicator */}
        {wsStatus === "connected" && (
          <div className="ml-auto flex items-center gap-1.5 text-[11px] text-emerald-600 font-medium">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            Live
          </div>
        )}
      </div>

      {/* ── Tabs ── */}
      <div className="bg-white border-b border-slate-200 px-6 flex gap-1">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-all duration-150 ${
              activeTab === tab.id
                ? "border-indigo-500 text-indigo-600"
                : "border-transparent text-slate-500 hover:text-slate-800 hover:border-slate-300"
            }`}
          >
            {tab.icon}
            {tab.label}
          </button>
        ))}
      </div>

      {/* ── Content ── */}
      <div className="flex-1 overflow-hidden">

        {/* Customers */}
        {activeTab === "customers" && (
          <div className="h-full overflow-y-auto px-6 py-5">
            <p className="text-xs text-slate-400 font-medium mb-4 uppercase tracking-wide">
              {customers.length} customers · click to expand orders
            </p>
            {/* items-start fixes the empty space on expanded cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 max-w-6xl mx-auto items-start">
              {customers.map((c) => (
                <CustomerCard key={c.id} customer={c} />
              ))}
            </div>
          </div>
        )}

        {/* Logs */}
        {activeTab === "logs" && (
          <div className="h-full flex flex-col">
            {/* Filter bar */}
            <div className="bg-white border-b border-slate-100 px-6 py-2.5 flex items-center gap-2 flex-wrap">
              <span className="text-[11px] text-slate-400 font-semibold uppercase tracking-wide mr-1">Filter</span>
              {["all", "tool_call", "tool_result", "user_message", "assistant_message"].map((t) => (
                <button
                  key={t}
                  onClick={() => setFilterType(t)}
                  className={`text-xs px-3 py-1 rounded-full transition-all duration-150 font-medium ${
                    filterType === t
                      ? "bg-indigo-100 text-indigo-700 shadow-sm"
                      : "text-slate-500 hover:bg-slate-100 hover:text-slate-700"
                  }`}
                >
                  {t === "all" ? "All" : t.replace(/_/g, " ")}
                </button>
              ))}
              <span className="ml-auto text-[11px] text-slate-400">
                {filteredLogs.length} entries
              </span>
            </div>

            <div className="flex-1 overflow-y-auto p-4">
              {filteredLogs.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full text-slate-300 select-none">
                  <Activity className="w-14 h-14 mb-3 opacity-40" />
                  <p className="text-sm font-medium text-slate-400">No logs yet</p>
                  <p className="text-xs text-slate-300 mt-1">Start a chat to see agent reasoning in real time</p>
                </div>
              ) : (
                filteredLogs.map((entry, i) => <LogRow key={i} entry={entry} />)
              )}
              <div ref={logsEndRef} />
            </div>
          </div>
        )}

        {/* Policy */}
        {activeTab === "policy" && (
          <div className="h-full overflow-y-auto px-6 py-5">
            <div className="max-w-3xl mx-auto">
              <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
                <div className="px-6 py-4 border-b border-slate-100 flex items-center gap-3 bg-gradient-to-r from-indigo-50 to-white">
                  <div className="w-8 h-8 bg-indigo-100 rounded-lg flex items-center justify-center">
                    <Shield className="w-4 h-4 text-indigo-600" />
                  </div>
                  <div>
                    <h2 className="font-semibold text-slate-800 text-sm">ShopEase Refund Policy</h2>
                    <p className="text-[11px] text-slate-400">Live policy used by the AI agent</p>
                  </div>
                </div>
                <div className="px-6 py-5">
                  <pre className="text-xs text-slate-600 whitespace-pre-wrap font-mono leading-relaxed">
                    {policy || "Loading policy…"}
                  </pre>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
