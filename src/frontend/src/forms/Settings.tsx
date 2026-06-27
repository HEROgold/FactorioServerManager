import { useEffect, useRef, useState } from "react";
import { useBlocker } from "react-router-dom";
import { SubmitButton } from "./SubmitButton";
import { sendJSON } from "@/api";
import Input from "@/components/tags/Input";
import Select from "@/components/tags/Select";
import Checkbox from "@/components/tags/Checkbox";
import Fieldset from "@/components/tags/Fieldset";

interface Visibility {
  public: boolean;
  lan: boolean;
}

/** Manager metadata (public-display opt-in), stored separately from Factorio settings. */
export interface PublicDisplay {
  public_display: boolean;
  show_name: boolean;
  show_status: boolean;
  show_reachability: boolean;
  show_ip: boolean;
}

const PUBLIC_DISPLAY_DEFAULT: PublicDisplay = {
  public_display: false,
  show_name: true,
  show_status: true,
  show_reachability: true,
  show_ip: false,
};

/** Mirrors the Factorio 2.1 server-settings.json returned by GET /api/server/:name/settings. */
export interface ManageServerData {
  name: string;
  description: string;
  tags: string[];
  max_players: number;
  visibility: Visibility;
  username: string;
  password: string;
  token: string;
  game_password: string;
  require_user_verification: boolean;
  max_upload_in_kilobytes_per_second: number;
  max_upload_slots: number;
  minimum_latency_in_ticks: number;
  max_heartbeats_per_second: number;
  ignore_player_limit_for_returning_players: boolean;
  allow_commands: "true" | "false" | "admins-only";
  autosave_interval: number;
  autosave_slots: number;
  afk_autokick_interval: number;
  auto_pause: boolean;
  auto_pause_when_players_connect: boolean;
  only_admins_can_pause_the_game: boolean;
  autosave_only_on_server: boolean;
  non_blocking_saving: boolean;
  minimum_segment_size: number;
  minimum_segment_size_peer_count: number;
  maximum_segment_size: number;
  maximum_segment_size_peer_count: number;
  public_display?: PublicDisplay;
}

interface Props {
  name: string;
  data: ManageServerData;
}

/** Reads the editable settings fields off the form into the PATCH payload. */
function collect(form: HTMLFormElement) {
  const str = (n: string) => (form.elements.namedItem(n) as HTMLInputElement | HTMLSelectElement | null)?.value ?? "";
  const num = (n: string) => Number(str(n));
  const bool = (n: string) => (form.elements.namedItem(n) as HTMLInputElement | null)?.checked ?? false;

  return {
    name: str("name"),
    description: str("description"),
    game_password: str("game_password"),
    max_players: num("max_players"),
    visibility_public: bool("visibility_public"),
    visibility_lan: bool("visibility_lan"),
    require_user_verification: bool("require_user_verification"),
    ignore_player_limit_for_returning_players: bool("ignore_player_limit_for_returning_players"),
    allow_commands: str("allow_commands"),
    max_upload_in_kilobytes_per_second: num("max_upload_in_kilobytes_per_second"),
    max_upload_slots: num("max_upload_slots"),
    max_heartbeats_per_second: num("max_heartbeats_per_second"),
    autosave_interval: num("autosave_interval"),
    autosave_slots: num("autosave_slots"),
    afk_autokick_interval: num("afk_autokick_interval"),
    auto_pause: bool("auto_pause"),
    auto_pause_when_players_connect: bool("auto_pause_when_players_connect"),
    only_admins_can_pause_the_game: bool("only_admins_can_pause_the_game"),
    autosave_only_on_server: bool("autosave_only_on_server"),
    non_blocking_saving: bool("non_blocking_saving"),
    public_display: {
      public_display: bool("pd_public_display"),
      show_name: bool("pd_show_name"),
      show_status: bool("pd_show_status"),
      show_reachability: bool("pd_show_reachability"),
      show_ip: bool("pd_show_ip"),
    },
  };
}

/** Renders the Factorio 2.1 server-settings form and persists changes via PATCH. */
export default function ManageServerForm({ name, data }: Props) {
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [dirty, setDirty] = useState(false);
  const pd = data.public_display ?? PUBLIC_DISPLAY_DEFAULT;
  const [publicDisplay, setPublicDisplay] = useState(pd.public_display);
  const formRef = useRef<HTMLFormElement>(null);
  // Serialized snapshot of the pristine (or last-saved) form for dirty checks.
  const baselineRef = useRef<string>("");

  // Capture the pristine form once mounted (defaults come from `data`).
  useEffect(() => {
    if (formRef.current) baselineRef.current = JSON.stringify(collect(formRef.current));
  }, []);

  const recomputeDirty = () => {
    if (formRef.current) {
      setDirty(JSON.stringify(collect(formRef.current)) !== baselineRef.current);
    }
  };

  // Guard a browser refresh/close/navigation when there are unsaved edits.
  useEffect(() => {
    if (!dirty) return;
    const handler = (e: BeforeUnloadEvent) => {
      e.preventDefault();
      e.returnValue = "";
    };
    window.addEventListener("beforeunload", handler);
    return () => window.removeEventListener("beforeunload", handler);
  }, [dirty]);

  // Guard in-app navigation — both tab switches (search param) and route
  // changes — while the form is dirty.
  const blocker = useBlocker(
    ({ currentLocation, nextLocation }) =>
      dirty &&
      (currentLocation.pathname !== nextLocation.pathname ||
        currentLocation.search !== nextLocation.search),
  );

  useEffect(() => {
    if (blocker.state !== "blocked") return;
    if (window.confirm("You have unsaved settings changes. Leave without saving?")) {
      blocker.proceed();
    } else {
      blocker.reset();
    }
  }, [blocker]);

  const handleSubmit = async (e: React.SubmitEvent<HTMLFormElement>) => {
    e.preventDefault();
    setMessage(null);
    setError(null);
    setSubmitting(true);
    const form = e.currentTarget;
    const payload = collect(form);

    try {
      await sendJSON(`/api/server/${name}/settings`, "PATCH", payload);
      setMessage("Settings saved.");
      // Saved state becomes the new baseline so the form is no longer "dirty".
      baselineRef.current = JSON.stringify(payload);
      setDirty(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save settings");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form ref={formRef} onSubmit={handleSubmit} onChange={recomputeDirty} onInput={recomputeDirty} className="form-stack">
      <Fieldset>
        <legend>Identity</legend>
        <div className="field">
          <label htmlFor="name">Server Name</label>
          <Input type="text" id="name" name="name" defaultValue={data.name} required />
        </div>
        <div className="field">
          <label htmlFor="description">Description</label>
          <Input type="text" id="description" name="description" defaultValue={data.description} />
        </div>
        <div className="field">
          <label htmlFor="game_password">Game Password</label>
          <Input type="password" id="game_password" name="game_password" defaultValue={data.game_password} />
        </div>

        <hr />
        <Checkbox
          name="pd_public_display"
          checked={publicDisplay}
          onChange={(e) => setPublicDisplay(e.target.checked)}
          label="Display this server publicly on the manager"
        />
        <div style={{ paddingLeft: 24, opacity: publicDisplay ? 1 : 0.5 }}>
          <Checkbox name="pd_show_name" defaultChecked={pd.show_name} disabled={!publicDisplay} label="Show name" />
          <Checkbox name="pd_show_status" defaultChecked={pd.show_status} disabled={!publicDisplay} label="Show status light" />
          <Checkbox name="pd_show_reachability" defaultChecked={pd.show_reachability} disabled={!publicDisplay} label="Show reachability light" />
          <Checkbox name="pd_show_ip" defaultChecked={pd.show_ip} disabled={!publicDisplay} label="Show IP address" />
        </div>
      </Fieldset>

      <Fieldset>
        <legend>Visibility</legend>
        <Checkbox name="visibility_public" defaultChecked={data.visibility.public} label="Public" />
        <Checkbox name="visibility_lan" defaultChecked={data.visibility.lan} label="LAN" />
        <Checkbox name="require_user_verification" defaultChecked={data.require_user_verification} label="Require user verification" />
      </Fieldset>

      <Fieldset>
        <legend>Players &amp; Permissions</legend>
        <div className="field">
          <label htmlFor="max_players">Max Players (0 = unlimited)</label>
          <Input type="number" id="max_players" name="max_players" min={0} step={1} defaultValue={data.max_players} />
        </div>
        <div className="field">
          <label htmlFor="allow_commands">Allow Lua Commands</label>
          <Select id="allow_commands" name="allow_commands" defaultValue={data.allow_commands}>
            <option value="false">false</option>
            <option value="admins-only">admins-only</option>
            <option value="true">true</option>
          </Select>
        </div>
        <Checkbox name="ignore_player_limit_for_returning_players" defaultChecked={data.ignore_player_limit_for_returning_players} label="Ignore player limit for returning players" />
      </Fieldset>

      <Fieldset>
        <legend>Saving &amp; Pausing</legend>
        <div className="field">
          <label htmlFor="autosave_interval">Autosave Interval (minutes)</label>
          <Input type="number" id="autosave_interval" name="autosave_interval" min={0} step={1} defaultValue={data.autosave_interval} />
        </div>
        <div className="field">
          <label htmlFor="autosave_slots">Autosave Slots</label>
          <Input type="number" id="autosave_slots" name="autosave_slots" min={0} step={1} defaultValue={data.autosave_slots} />
        </div>
        <div className="field">
          <label htmlFor="afk_autokick_interval">AFK Autokick (minutes, 0 = never)</label>
          <Input type="number" id="afk_autokick_interval" name="afk_autokick_interval" min={0} step={1} defaultValue={data.afk_autokick_interval} />
        </div>
        <Checkbox name="auto_pause" defaultChecked={data.auto_pause} label="Auto pause when empty" />
        <Checkbox name="auto_pause_when_players_connect" defaultChecked={data.auto_pause_when_players_connect} label="Auto pause when players connect" />
        <Checkbox name="only_admins_can_pause_the_game" defaultChecked={data.only_admins_can_pause_the_game} label="Only admins can pause" />
        <Checkbox name="autosave_only_on_server" defaultChecked={data.autosave_only_on_server} label="Autosave only on server" />
        <Checkbox name="non_blocking_saving" defaultChecked={data.non_blocking_saving} label="Non-blocking saving (experimental)" />
      </Fieldset>

      <Fieldset>
        <legend>Network &amp; Performance</legend>
        <div className="field">
          <label htmlFor="max_upload_in_kilobytes_per_second">Max Upload (KB/s, 0 = unlimited)</label>
          <Input type="number" id="max_upload_in_kilobytes_per_second" name="max_upload_in_kilobytes_per_second" min={0} step={1} defaultValue={data.max_upload_in_kilobytes_per_second} />
        </div>
        <div className="field">
          <label htmlFor="max_upload_slots">Max Upload Slots</label>
          <Input type="number" id="max_upload_slots" name="max_upload_slots" min={0} step={1} defaultValue={data.max_upload_slots} />
        </div>
        <div className="field">
          <label htmlFor="max_heartbeats_per_second">Max Heartbeats/s (6–240)</label>
          <Input type="number" id="max_heartbeats_per_second" name="max_heartbeats_per_second" min={6} max={240} step={1} defaultValue={data.max_heartbeats_per_second} />
        </div>
      </Fieldset>

      {message ? <p style={{ color: "#aee7be" }}>{message}</p> : null}
      {error ? <p className="red">{error}</p> : null}

      <SubmitButton busy="Saving..." idle="Save Changes" submitting={submitting} />
    </form>
  );
}
