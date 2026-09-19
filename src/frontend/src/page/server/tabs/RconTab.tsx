import { useEffect, useRef, useState } from "react";
import type { MutableRefObject } from "react";
import { apiUrl, getJSON, sendJSON } from "@/api";
import Button from "@/components/tags/Button";
import Input from "@/components/tags/Input";
import Code from "@/components/tags/Code";

interface RconResponse {
  host: string;
  port: number;
  password: string | null;
}

interface LogsResponse {
  current_log: string;
  previous_log: string;
}

interface Entry {
  cmd: string;
  response?: string;
  error?: string;
}

// Factorio writes chat/connection events to its log; surface those lines as a
// live feed (RCON itself is request/response and can't push chat).
const CHAT_RE = /\[(CHAT|JOIN|LEAVE|KICK|BAN)\]/;
const MAX_CHAT = 500;

function chatLines(text: string): string[] {
  return text
    .split("\n")
    .filter((line) => CHAT_RE.test(line));
}

function useRconCreds(name: string) {
  const [creds, setCreds] = useState<RconResponse | null>(null);

  useEffect(() => {
    (async () => {
      try {
        setCreds(await getJSON<RconResponse>(`/api/server/${name}/rcon`));
      } catch {
        /* credentials are optional context; ignore load failures */
      }
    })();
  }, [name]);

  return creds;
}

// Seeds the chat feed with any chat lines already in the current log, then
// keeps it live from the log stream.
function useChatFeed(name: string) {
  const [chat, setChat] = useState<string[]>([]);
  const chatRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const data = await getJSON<LogsResponse>(`/api/server/${name}/logs`);
        if (active) {
          setChat(chatLines(data.current_log).slice(-MAX_CHAT));
        }
      } catch {
        /* ignore; the stream will fill it in */
      }
    })();
    return () => {
      active = false;
    };
  }, [name]);

  useEffect(() => {
    const es = new EventSource(apiUrl(`/api/server/${name}/logs/stream`), {
      withCredentials: true,
    });
    es.onmessage = (event) => {
      const lines = chatLines(String(event.data));
      if (!lines.length) return;
      setChat((prev) => {
        const next = prev.concat(lines);
        return next.length > MAX_CHAT ? next.slice(next.length - MAX_CHAT) : next;
      });
    };
    return () => es.close();
  }, [name]);

  useEffect(() => {
    const el = chatRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [chat]);

  return { chat, chatRef };
}

function useRconTranscript(name: string) {
  const [command, setCommand] = useState("");
  const [entries, setEntries] = useState<Entry[]>([]);
  const [sending, setSending] = useState(false);
  const transcriptRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const el = transcriptRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [entries]);

  const send = async (e: React.SubmitEvent<HTMLFormElement>): Promise<void> => {
    e.preventDefault();
    const cmd = command.trim();
    if (!cmd) return;
    setSending(true);
    try {
      const res = await sendJSON<{ response: string }>(
        `/api/server/${name}/rcon/send`,
        "POST",
        { command: cmd },
      );
      setEntries((prev) => [...prev, { cmd, response: res.response }]);
      setCommand("");
    } catch (err) {
      setEntries((prev) => [
        ...prev,
        { cmd, error: err instanceof Error ? err.message : "Command failed" },
      ]);
    } finally {
      setSending(false);
    }
  };

  return { command, setCommand, entries, sending, transcriptRef, send };
}

function CredentialsPanel({ creds }: { creds: RconResponse }) {
  return (
    <dl className="panel-hole mb12">
      <dt>Host</dt>
      <dd>{creds.host}</dd>
      <dt>Port</dt>
      <dd>{creds.port}</dd>
      <dt>Password</dt>
      <dd>{creds.password ?? "— (start the server once to generate)"}</dd>
    </dl>
  );
}

function ChatPanel({ chat, chatRef }: { chat: string[]; chatRef: MutableRefObject<HTMLDivElement | null> }) {
  return (
    <>
      <h4 className="mt0">Live Chat</h4>
      <div className="log-window mb16" ref={chatRef} style={{ maxHeight: 220 }}>
        {chat.length ? chat.join("\n") : "No chat yet. Player chat and join/leave events will appear here."}
      </div>
    </>
  );
}

function ConsoleTranscript({
  entries,
  transcriptRef,
}: {
  entries: Entry[];
  transcriptRef: MutableRefObject<HTMLDivElement | null>;
}) {
  return (
    <div className="rcon-transcript" ref={transcriptRef}>
      {entries.length === 0 ? (
        <p className="mb0">
          No commands sent yet. Try <Code>/help</Code> or <Code>/players</Code>.
        </p>
      ) : (
        entries.map((entry, i) => (
          <div className="rcon-entry" key={i}>
            <div className="rcon-entry-cmd">{entry.cmd}</div>
            {entry.error ? (
              <div className="rcon-entry-err">{entry.error}</div>
            ) : (
              <div className="rcon-entry-res">{entry.response || "(no output)"}</div>
            )}
          </div>
        ))
      )}
    </div>
  );
}

// Interactive RCON console: sends commands to a running server via
// POST /api/server/:name/rcon/send, and shows a live in-game chat feed parsed
// from the log stream.
export default function RconTab({ name, status }: { name: string; status: string }) {
  const creds = useRconCreds(name);
  const { chat, chatRef } = useChatFeed(name);
  const { command, setCommand, entries, sending, transcriptRef, send } = useRconTranscript(name);
  const [showCreds, setShowCreds] = useState(false);

  const running = status === "running";

  return (
    <div className="panel-inset-lighter">
      <div className="flex flex-space-between flex-items-center mb12" style={{ gap: 12, flexWrap: "wrap" }}>
        <h3 className="mt0 mb0">RCON Console</h3>
        <Button variant="ghost" small onClick={() => setShowCreds((s) => !s)}>
          {showCreds ? "Hide" : "Show"} credentials
        </Button>
      </div>

      {showCreds && creds ? <CredentialsPanel creds={creds} /> : null}

      <ChatPanel chat={chat} chatRef={chatRef} />

      <h4>Console</h4>
      {!running ? (
        <p className="mod-token-warning">Server is not running — start it to send RCON commands.</p>
      ) : null}

      <ConsoleTranscript entries={entries} transcriptRef={transcriptRef} />

      <form className="rcon-form" onSubmit={send}>
        <Input
          type="text"
          value={command}
          placeholder="Enter RCON command…"
          onChange={(e) => setCommand(e.target.value)}
          disabled={!running || sending}
        />
        <Button type="submit" variant="green" disabled={!running || sending}>Send</Button>
      </form>
    </div>
  );
}
