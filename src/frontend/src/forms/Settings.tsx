
import { Form, useNavigation } from "react-router-dom"
import CSRF from "./CSRF"
import { SubmitButton } from "./SubmitButton"

type CommaSeparatedString = string

interface ManageServerForm {
  readonly port: number;
  name: string;
  game_password?: string;
  description?: string;
  tags: string;
  
  // Visibility & Access
  visibility_public: boolean;
  visibility_steam: boolean;
  visibility_lan: boolean;
  require_user_verification: boolean;
  use_authserver_bans: boolean;
  whitelist: boolean;

  // Player Settings
  max_players: number;
  ignore_limit_returning: boolean;
  admins: CommaSeparatedString
  allow_commands: 'false' | 'admins-only' | 'true';
  only_admins_can_pause_the_game: boolean;
  afk_autokick_interval: number;

  // Network & Performance
  max_upload_in_kilobytes_per_second: number;
  max_upload_slots: number;
  ignore_player_limit_for_returning_players: boolean;

  // Save Settings
  autosave_interval: number;
  autosave_only_on_server: boolean;
  non_blocking_saving: boolean;
  auto_pause: boolean;
}


/**
 * Renders the server management form with current settings.
 * @param data The current server configuration
 */
export default function ManageServerForm({ data }: { data: ManageServerForm }) {
  return (
    <Form method="post" action="settings/update" className="space-y-6">
      <CSRF />

      {/* Network & Identity */}
      <fieldset>
        <legend className="font-bold">Network & Identity</legend>
        <div>
          <label htmlFor="port">UDP Port (Read-only)</label>
          <input type="number" id="port" name="port" defaultValue={data.port} readOnly className="bg-gray-100 cursor-not-allowed" />
        </div>
        <div>
          <label htmlFor="name">Server Name</label>
          <input type="text" id="name" name="name" defaultValue={data.name} required />
        </div>
        <div>
          <label htmlFor="game_password">Password</label>
          <input type="password" id="game_password" name="game_password" defaultValue={data.game_password} />
        </div>
      </fieldset>

      {/* Visibility Settings */}
      <fieldset>
        <legend className="font-bold">Visibility</legend>
        <label className="block">
          <input type="checkbox" name="visibility_public" defaultChecked={data.visibility_public} /> Public
        </label>
        <label className="block">
          <input type="checkbox" name="visibility_steam" defaultChecked={data.visibility_steam} /> Steam
        </label>
        <label className="block">
          <input type="checkbox" name="visibility_lan" defaultChecked={data.visibility_lan} /> LAN
        </label>
      </fieldset>

      {/* Player Management */}
      <fieldset>
        <legend className="font-bold">Players & Permissions</legend>
        <div>
          <label htmlFor="max_players">Max Players</label>
          <input type="number" id="max_players" name="max_players" defaultValue={data.max_players} />
        </div>
        <div>
          <label htmlFor="allow_commands">Allow Lua Commands</label>
          <select id="allow_commands" name="allow_commands" defaultValue={data.allow_commands}>
            <option value="false">false</option>
            <option value="admins-only">admins-only</option>
            <option value="true">true</option>
          </select>
        </div>
        <div>
          <label htmlFor="admins">Admins (comma separated)</label>
          <input type="text" id="admins" name="admins" defaultValue={data.admins} />
        </div>
      </fieldset>

      {/* Server Mechanics */}
      <fieldset>
        <legend className="font-bold">Server Behavior</legend>
        <div>
          <label htmlFor="autosave_interval">Autosave Interval (seconds)</label>
          <input type="number" id="autosave_interval" name="autosave_interval" defaultValue={data.autosave_interval} />
        </div>
        <label className="block">
          <input type="checkbox" name="auto_pause" defaultChecked={data.auto_pause} /> Auto Pause (when empty)
        </label>
        <label className="block">
          <input type="checkbox" name="whitelist" defaultChecked={data.whitelist} /> Enable Whitelist
        </label>
      </fieldset>

      <SubmitButton />
    </Form>
  );
}
